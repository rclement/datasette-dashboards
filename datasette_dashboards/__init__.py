import re
import typing as t
import urllib.parse

from datasette import hookimpl
from datasette.database import Database
from datasette.utils.asgi import Forbidden, NotFound, Request, Response

if t.TYPE_CHECKING:  # pragma: no cover
    from datasette.app import Datasette


sql_opt_pattern = re.compile(r"(?P<opt>\[\[[^\]]*\]\])")
sql_var_pattern = re.compile(r"\:(?P<var>[a-zA-Z0-9_]+)")


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
    datasette: "Datasette", dashboard: t.Dict[str, t.Any]
) -> None:
    for flt in dashboard.get("filters", {}).values():
        if flt["type"] == "select" and {"db", "query"} & flt.keys():
            values = [
                row[0] for row in await datasette.execute(flt["db"], flt["query"])
            ]
            flt["options"] = values


def get_dashboard_filters_keys(
    request: Request, dashboard: t.Dict[str, t.Any]
) -> t.Set[str]:
    filters_keys = (dashboard.get("filters") or {}).keys()
    return set(filters_keys) & set(request.args.keys())


def get_dashboard_filters(request: Request, opts_keys: t.Set[str]) -> t.Dict[str, str]:
    return {key: request.args[key] for key in opts_keys}


def generate_dashboard_filters_qs(request: Request, opts_keys: t.Set[str]) -> str:
    return urllib.parse.urlencode({key: request.args[key] for key in opts_keys})


def fill_chart_query_options(
    chart: t.Dict[str, t.Any], options: t.Dict[str, str]
) -> None:
    query: t.Optional[str] = chart.get("query")
    if query is None:
        return

    to_replace: t.List[t.Dict[str, str]] = []
    for opt_match in re.finditer(sql_opt_pattern, query):
        opt_group = opt_match.group("opt")
        var_match = re.search(sql_var_pattern, opt_group)
        var_group = var_match.group("var") if var_match is not None else ""
        opt_keep = var_group in options and options[var_group] != ""
        to_replace.append(
            {
                "opt": opt_group,
                "replacement": opt_group.strip("[[]]") if opt_keep else "",
            }
        )

    for r in to_replace:
        query = query.replace(r["opt"], r["replacement"])

    chart["query"] = query


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

    settings = dashboard.get("settings", {})
    dbs = set([chart["db"] for chart in dashboard["charts"].values() if "db" in chart])
    for db in dbs:
        try:
            database = datasette.get_database(db)
        except KeyError:
            raise NotFound(f"Database does not exist: {db}")
        await check_permission_execute_sql(request, datasette, database.name)

    await fill_dynamic_filters(datasette, dashboard)
    options_keys = get_dashboard_filters_keys(request, dashboard)
    query_parameters = get_dashboard_filters(request, options_keys)
    query_string = generate_dashboard_filters_qs(request, options_keys)

    default_filters = {
        k: v["default"] for k, v in dashboard["filters"].items() if v.get("default")
    }
    if len(query_parameters.keys()) == 0 and len(default_filters) > 0:
        qs = urllib.parse.urlencode(default_filters)
        response = Response.redirect(f"{request.path}?{qs}")
        for k, v in request.cookies.items():
            response.set_cookie(k, v)
        return response

    for chart in dashboard["charts"].values():
        fill_chart_query_options(chart, query_parameters)

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
                "query_string": query_string,
                "dashboard": dashboard,
                "embed": embed,
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

    try:
        chart = dashboard["charts"][chart_slug]
    except KeyError:
        raise NotFound(f"Chart does not exist: {chart_slug}")

    db = chart.get("db")
    if db:
        database = datasette.get_database(db)
        await check_permission_execute_sql(request, datasette, database.name)

    options_keys = get_dashboard_filters_keys(request, dashboard)
    query_parameters = get_dashboard_filters(request, options_keys)
    query_string = generate_dashboard_filters_qs(request, options_keys)
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
            },
            request=request,
        )
    )


async def dashboard_chart(request: Request, datasette: "Datasette") -> Response:
    return await _dashboard_chart(request, datasette, embed=False)


async def dashboard_chart_embed(request: Request, datasette: "Datasette") -> Response:
    return await _dashboard_chart(request, datasette, embed=True)


@hookimpl
def register_routes() -> (
    t.Iterable[t.Tuple[str, t.Callable[..., t.Coroutine[t.Any, t.Any, Response]]]]
):
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
    datasette: "Datasette", actor: t.Optional[t.Dict[str, t.Any]]
) -> t.Iterable[t.Dict[str, t.Any]]:
    return [
        {"href": datasette.urls.path("/-/dashboards"), "label": "Dashboards"},
    ]
