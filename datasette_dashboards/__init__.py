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


async def dashboards(request, datasette):
    await check_permission_instance(request, datasette)
    config = datasette.plugin_config("datasette-dashboards") or {}
    return Response.html(
        await datasette.render_template(
            "dashboards.html",
            {"dashboards": config},
        )
    )


async def dashboards_slug(request, datasette):
    await check_permission_instance(request, datasette)

    config = datasette.plugin_config("datasette-dashboards") or {}
    slug = urllib.parse.unquote(request.url_vars["slug"])
    if slug not in config.keys():
        raise NotFound(f"Dashboard not found: {slug}")

    dbs = set([chart["db"] for chart in config[slug]["charts"]])
    for db in dbs:
        try:
            database = datasette.get_database(db)
        except KeyError:
            raise NotFound(f"Database does not exist: {db}")
        await check_permission_execute_sql(request, datasette, database)

    return Response.html(
        await datasette.render_template(
            "dashboard_view.html",
            {"dashboards": config, "slug": slug},
        )
    )


@hookimpl
def register_routes():
    return (
        ("^/-/dashboards$", dashboards),
        ("^/-/dashboards/(?P<slug>.*)$", dashboards_slug),
    )


@hookimpl
def menu_links(datasette, actor):
    return [
        {"href": datasette.urls.path("/-/dashboards"), "label": "Dashboards"},
    ]
