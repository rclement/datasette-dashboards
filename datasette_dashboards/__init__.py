import urllib
from datasette import hookimpl
from datasette.utils.asgi import Forbidden, NotFound, Response


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

    dbs = set([chart["db"] for chart in dashboard["charts"] if "db" in chart])
    for db in dbs:
        try:
            database = datasette.get_database(db)
        except KeyError:
            raise NotFound(f"Database does not exist: {db}")
        await check_permission_execute_sql(request, datasette, database)

    return Response.html(
        await datasette.render_template(
            "dashboard_view.html",
            {"dashboard": dashboard},
        )
    )


@hookimpl
def register_routes():
    return (
        ("^/-/dashboards$", dashboard_list),
        ("^/-/dashboards/(?P<slug>.*)$", dashboard_view),
    )


@hookimpl
def menu_links(datasette, actor):
    return [
        {"href": datasette.urls.path("/-/dashboards"), "label": "Dashboards"},
    ]
