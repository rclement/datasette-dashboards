import urllib
from datasette import hookimpl
from datasette.utils.asgi import NotFound, Response


async def dashboards(request, datasette):
    config = datasette.plugin_config("datasette-dashboards") or {}
    return Response.html(
        await datasette.render_template(
            "dashboards.html",
            {"dashboards": config},
        )
    )


async def dashboards_slug(request, datasette):
    config = datasette.plugin_config("datasette-dashboards") or {}
    slug = urllib.parse.unquote(request.url_vars["slug"])
    if slug not in config.keys():
        raise NotFound(f"Dashboard not found: {slug}")

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
