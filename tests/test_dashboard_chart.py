import pytest


@pytest.mark.asyncio
async def test_dashboard_chart(datasette):
    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    for slug, dashboard in dashboards.items():
        for chart_slug, chart in dashboard["charts"].items():
            props = chart.keys()
            response = await datasette.client.get(f"/-/dashboards/{slug}/{chart_slug}")
            assert response.status_code == 200
            assert f'<h1>{dashboard["title"]}</h1>' in response.text
            if "title" in props:
                assert f'<p>{chart["title"]}</p>' in response.text
            if "db" in props and "query" in props:
                assert f'<a href="/{chart["db"]}?sql={chart["query"]}">'
                assert "View and edit SQL"


@pytest.mark.asyncio
async def test_dashboard_chart_unknown_dashboard(datasette):
    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    dashboard = list(dashboards.values())[0]
    chart_slug = list(dashboard["charts"].items())[0][0]

    response = await datasette.client.get(
        f"/-/dashboards/unknown-dashboard/{chart_slug}"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_chart_unknown_chart(datasette):
    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    slug = list(dashboards.keys())[0]

    response = await datasette.client.get(f"/-/dashboards/{slug}/unknown-chart")
    assert response.status_code == 404
