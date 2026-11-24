import json
import re
import typing as t
import urllib.parse

from datasette import hookimpl
from datasette.database import Database
from datasette.utils.asgi import Forbidden, NotFound, Request, Response

from datasette_dashboards.chart_types import convert_chart_type

if t.TYPE_CHECKING:  # pragma: no cover
    from datasette.app import Datasette


sql_opt_pattern = re.compile(r"(?P<opt>\[\[.*?\]\])")
sql_var_pattern = re.compile(r"\:(?P<var>[a-zA-Z0-9_]+)")


def replace_opts_in_query(query: str, options: dict[str, str]) -> str:
    to_replace: list[dict[str, str]] = []
    for opt_match in re.finditer(sql_opt_pattern, query):
        opt_group = opt_match.group("opt")
        var_match = re.search(sql_var_pattern, opt_group)
        var_group = var_match.group("var") if var_match is not None else ""
        opt_keep = var_group in options and options[var_group] != ""
        to_replace.append(
            {
                "opt": opt_group,
                "replacement": (
                    opt_group.removeprefix("[[").removesuffix("]]") if opt_keep else ""
                ),
            }
        )

    result = query
    for r in to_replace:
        result = result.replace(r["opt"], r["replacement"])

    return result


async def check_permission_instance(request: Request, datasette: "Datasette") -> None:
    if (
        await datasette.permission_allowed(
            request.actor,
            "view-instance",
            default=None,
        )
    ) is False:
        raise Forbidden("view-instance denied")


async def check_permission_execute_sql(
    request: Request, datasette: "Datasette", database: Database
) -> None:
    if (
        await datasette.permission_allowed(
            request.actor,
            "execute-sql",
            resource=database,
            default=None,
        )
    ) is False:
        raise Forbidden("execute-sql denied")


async def fill_dynamic_filters(
    datasette: "Datasette", dashboard: dict[str, t.Any], options: dict[str, str]
) -> None:
    for flt in dashboard["filters"].values():
        if flt["type"] == "select" and {"db", "query"} & flt.keys():
            query = replace_opts_in_query(flt["query"], options)
            values = [
                row[0]
                for row in await datasette.execute(flt["db"], query, params=options)
            ]
            flt["options"] = values


def get_dashboard_filters_keys(
    request: Request, dashboard: dict[str, t.Any]
) -> set[str]:
    filters_keys = dashboard["filters"].keys()
    return set(filters_keys) & set(request.args.keys())


def is_multiple_filter(dashboard: dict[str, t.Any], key: str) -> bool:
    flt = dashboard.get("filters", {}).get(key, {})
    return flt.get("type") == "select" and bool(flt.get("multiple"))


def get_multiple_filter_values(request: Request, key: str) -> list[str]:
    values: list[str] = list(request.args.getlist(key))
    if len(values) == 1 and values[0].startswith("["):
        # Already serialized as a JSON array (e.g. in chart links)
        try:
            parsed = json.loads(values[0])
        except ValueError:
            return values
        if isinstance(parsed, list):
            return [str(v) for v in parsed]
    return values


def get_dashboard_filters(
    request: Request,
    opts_keys: set[str],
    dashboard: dict[str, t.Any] | None = None,
) -> dict[str, str]:
    # SQLite cannot bind a list to a named parameter, so the values of a
    # `multiple` filter are passed as a JSON array, to be used in SQL with
    # `IN (SELECT value FROM json_each(:name))`
    dashboard = dashboard or {}
    return {
        key: (
            json.dumps(get_multiple_filter_values(request, key))
            if is_multiple_filter(dashboard, key)
            else request.args[key]
        )
        for key in opts_keys
    }


def get_multiple_filters_selection(
    dashboard: dict[str, t.Any], query_parameters: dict[str, str]
) -> dict[str, list[str]]:
    selection: dict[str, list[str]] = {}
    for key, flt in dashboard["filters"].items():
        if not is_multiple_filter(dashboard, key):
            continue
        if key in query_parameters:
            selection[key] = json.loads(query_parameters[key])
        else:
            default = flt.get("default", [])
            selection[key] = [
                str(v) for v in (default if isinstance(default, list) else [default])
            ]
    return selection


def generate_dashboard_filters_qs(
    request: Request,
    opts_keys: set[str],
    dashboard: dict[str, t.Any] | None = None,
) -> str:
    return urllib.parse.urlencode(get_dashboard_filters(request, opts_keys, dashboard))


def fill_chart_query_options(chart: dict[str, t.Any], options: dict[str, str]) -> None:
    query: str | None = chart.get("query")
    if query is None:
        return
    chart["query"] = replace_opts_in_query(query, options)


async def dashboard_list(request: Request, datasette: "Datasette") -> Response:
    await check_permission_instance(request, datasette)
    config = datasette.plugin_config("datasette-dashboards") or {}
    return Response.html(
        await datasette.render_template(
            "dashboard_list.html",
            {"dashboards": config},
            request=request,
        )
    )


async def _dashboard_view(
    request: Request, datasette: "Datasette", embed: bool = False
) -> Response:
    await check_permission_instance(request, datasette)

    config = datasette.plugin_config("datasette-dashboards") or {}
    slug = urllib.parse.unquote(request.url_vars["slug"])
    try:
        dashboard = config[slug]
    except KeyError:
        raise NotFound(f"Dashboard not found: {slug}")

    dashboard["filters"] = dashboard.get("filters", {})
    dashboard["charts"] = dashboard.get("charts", {})

    settings = dashboard.get("settings", {})
    dbs = {chart["db"] for chart in dashboard["charts"].values() if "db" in chart}
    for db in dbs:
        try:
            database = datasette.get_database(db)
        except KeyError:
            raise NotFound(f"Database does not exist: {db}")
        await check_permission_execute_sql(request, datasette, database.name)

    options_keys = get_dashboard_filters_keys(request, dashboard)
    query_parameters = get_dashboard_filters(request, options_keys, dashboard)
    query_string = generate_dashboard_filters_qs(request, options_keys, dashboard)
    await fill_dynamic_filters(datasette, dashboard, query_parameters)

    default_filters = {
        k: v["default"] for k, v in dashboard["filters"].items() if v.get("default")
    }
    if len(query_parameters.keys()) == 0 and len(default_filters) > 0:
        qs = urllib.parse.urlencode(default_filters, doseq=True)
        response = Response.redirect(f"{request.path}?{qs}")
        for k, v in request.cookies.items():
            response.set_cookie(k, v)
        return response

    charts = {}
    for chart_slug, chart in dashboard["charts"].items():
        try:
            charts[chart_slug] = convert_chart_type(chart)
        except KeyError as e:
            raise NotFound(
                f"Chart '{chart_slug}' configuration error: missing required field {e}"
            )
    for chart in charts.values():
        fill_chart_query_options(chart, query_parameters)

    render_dashboard = dict(dashboard, charts=charts)

    return Response.html(
        await datasette.render_template(
            "dashboard_view.html",
            {
                "settings": settings,
                "absolute_url": datasette.absolute_url(
                    request, datasette.urls.instance()
                ),
                "slug": slug,
                "query_parameters": query_parameters,
                "multiple_selection": get_multiple_filters_selection(
                    dashboard, query_parameters
                ),
                "query_string": query_string,
                "dashboard": render_dashboard,
                "embed": embed,
                "row_limit": datasette.settings_dict().get("max_returned_rows"),
            },
            request=request,
        )
    )


async def dashboard_view(request: Request, datasette: "Datasette") -> Response:
    return await _dashboard_view(request, datasette, embed=False)


async def dashboard_view_embed(request: Request, datasette: "Datasette") -> Response:
    return await _dashboard_view(request, datasette, embed=True)


async def _dashboard_chart(
    request: Request, datasette: "Datasette", embed: bool = False
) -> Response:
    await check_permission_instance(request, datasette)

    config = datasette.plugin_config("datasette-dashboards") or {}
    slug = urllib.parse.unquote(request.url_vars["slug"])
    chart_slug = urllib.parse.unquote(request.url_vars["chart_slug"])

    try:
        dashboard = config[slug]
    except KeyError:
        raise NotFound(f"Dashboard not found: {slug}")

    dashboard["filters"] = dashboard.get("filters", {})
    dashboard["charts"] = dashboard.get("charts", {})

    try:
        chart = dashboard["charts"][chart_slug]
    except KeyError:
        raise NotFound(f"Chart does not exist: {chart_slug}")

    db = chart.get("db")
    if db:
        database = datasette.get_database(db)
        await check_permission_execute_sql(request, datasette, database.name)

    options_keys = get_dashboard_filters_keys(request, dashboard)
    query_parameters = get_dashboard_filters(request, options_keys, dashboard)
    query_string = generate_dashboard_filters_qs(request, options_keys, dashboard)

    try:
        chart = convert_chart_type(chart)
    except KeyError as e:
        raise NotFound(
            f"Chart '{chart_slug}' configuration error: missing required field {e}"
        )
    fill_chart_query_options(chart, query_parameters)

    return Response.html(
        await datasette.render_template(
            "dashboard_chart.html",
            {
                "absolute_url": datasette.absolute_url(
                    request, datasette.urls.instance()
                ),
                "slug": slug,
                "query_string": query_string,
                "dashboard": dashboard,
                "chart": chart,
                "embed": embed,
                "row_limit": datasette.settings_dict().get("max_returned_rows"),
            },
            request=request,
        )
    )


async def dashboard_chart(request: Request, datasette: "Datasette") -> Response:
    return await _dashboard_chart(request, datasette, embed=False)


async def dashboard_chart_embed(request: Request, datasette: "Datasette") -> Response:
    return await _dashboard_chart(request, datasette, embed=True)


@hookimpl
def register_routes() -> t.Iterable[
    tuple[str, t.Callable[..., t.Coroutine[t.Any, t.Any, Response]]]
]:
    return (
        ("^/-/dashboards$", dashboard_list),
        ("^/-/dashboards/(?P<slug>[^/]+)$", dashboard_view),
        ("^/-/dashboards/(?P<slug>[^/]+)/embed$", dashboard_view_embed),
        ("^/-/dashboards/(?P<slug>[^/]+)/(?P<chart_slug>[^/]+)$", dashboard_chart),
        (
            "^/-/dashboards/(?P<slug>[^/]+)/(?P<chart_slug>[^/]+)/embed$",
            dashboard_chart_embed,
        ),
    )


@hookimpl
def menu_links(
    datasette: "Datasette", actor: dict[str, t.Any] | None
) -> t.Iterable[dict[str, t.Any]]:
    return [
        {"href": datasette.urls.path("/-/dashboards"), "label": "Dashboards"},
    ]
