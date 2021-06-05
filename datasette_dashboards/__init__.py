import re
import urllib
from datasette import hookimpl
from datasette.utils.asgi import Forbidden, NotFound, Response


sql_opt_pattern = re.compile(r"(?P<opt>\[\[[^\]]*\]\])")
sql_var_pattern = re.compile(r"\:(?P<var>[a-zA-Z0-9_]+)")


async def check_permission_instance(request, datasette):
    if (
        await datasette.permission_allowed(
            request.actor,
            "view-instance",
            default=None,
        )
    ) is False:
        raise Forbidden("view-instance denied")


async def check_permission_execute_sql(request, datasette, database):
    if (
        await datasette.permission_allowed(
            request.actor,
            "execute-sql",
            resource=database,
            default=None,
        )
    ) is False:
        raise Forbidden("execute-sql denied")


def get_dashboard_filters_keys(request, dashboard):
    filters_keys = (dashboard.get("filters") or {}).keys()
    return set(filters_keys) & set(request.args.keys())


def get_dashboard_filters(request, opts_keys):
    return {key: request.args[key] for key in opts_keys}


def generate_dashboard_filters_qs(request, opts_keys):
    return urllib.parse.urlencode({key: request.args[key] for key in opts_keys})


def fill_chart_query_options(chart, options_keys):
    query = chart.get("query")
    if query is None:
        return

    to_replace = []
    for opt_match in re.finditer(sql_opt_pattern, query):
        opt_group = opt_match.group("opt")
        var_match = re.search(sql_var_pattern, opt_group)
        var_group = var_match.group("var")
        to_replace.append({"opt": opt_group, "keep": var_group in options_keys})

    for r in to_replace:
        if r["keep"]:
            query = query.replace(r["opt"], r["opt"].strip("[[]]"))
        else:
            query = query.replace(r["opt"], "")

    chart["query"] = query


async def dashboard_list(request, datasette):
    await check_permission_instance(request, datasette)
    config = datasette.plugin_config("datasette-dashboards") or {}
    return Response.html(
        await datasette.render_template(
            "dashboard_list.html",
            {"dashboards": config},
        )
    )


async def dashboard_view(request, datasette):
    await check_permission_instance(request, datasette)

    config = datasette.plugin_config("datasette-dashboards") or {}
    slug = urllib.parse.unquote(request.url_vars["slug"])
    try:
        dashboard = config[slug]
    except KeyError:
        raise NotFound(f"Dashboard not found: {slug}")

    dbs = set([chart["db"] for chart in dashboard["charts"].values() if "db" in chart])
    for db in dbs:
        try:
            database = datasette.get_database(db)
        except KeyError:
            raise NotFound(f"Database does not exist: {db}")
        await check_permission_execute_sql(request, datasette, database)

    options_keys = get_dashboard_filters_keys(request, dashboard)
    query_parameters = get_dashboard_filters(request, options_keys)
    query_string = generate_dashboard_filters_qs(request, options_keys)

    for chart in dashboard["charts"].values():
        fill_chart_query_options(chart, options_keys)

    return Response.html(
        await datasette.render_template(
            "dashboard_view.html",
            {
                "slug": slug,
                "query_parameters": query_parameters,
                "query_string": query_string,
                "dashboard": dashboard,
            },
        )
    )


async def dashboard_chart(request, datasette):
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
        await check_permission_execute_sql(request, datasette, database)

    options_keys = get_dashboard_filters_keys(request, dashboard)
    query_string = generate_dashboard_filters_qs(request, options_keys)
    fill_chart_query_options(chart, options_keys)

    return Response.html(
        await datasette.render_template(
            "dashboard_chart.html",
            {
                "slug": slug,
                "query_string": query_string,
                "dashboard": dashboard,
                "chart": chart,
            },
        )
    )


@hookimpl
def register_routes():
    return (
        ("^/-/dashboards$", dashboard_list),
        ("^/-/dashboards/(?P<slug>[^/]+)$", dashboard_view),
        ("^/-/dashboards/(?P<slug>[^/]+)/(?P<chart_slug>[^/]+)$", dashboard_chart),
    )


@hookimpl
def menu_links(datasette, actor):
    return [
        {"href": datasette.urls.path("/-/dashboards"), "label": "Dashboards"},
    ]
