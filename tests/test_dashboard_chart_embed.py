import pytest


@pytest.mark.asyncio
async def test_dashboard_chart_embed(datasette):
    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    for slug, dashboard in dashboards.items():
        for chart_slug, chart in dashboard["charts"].items():
            props = chart.keys()
            response = await datasette.client.get(
                f"/-/dashboards/{slug}/{chart_slug}/embed"
            )
            assert response.status_code == 200
            assert f'<h1>{dashboard["title"]}</h1>' in response.text
            if "title" in props:
                assert f'<p>{chart["title"]}</p>' in response.text
