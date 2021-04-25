import pytest


@pytest.mark.asyncio
async def test_plugin_is_installed(datasette):
    response = await datasette.client.get("/-/plugins.json")
    assert response.status_code == 200
    installed_plugins = {p["name"] for p in response.json()}
    assert "datasette-dashboards" in installed_plugins


@pytest.mark.asyncio
async def test_menu(datasette):
    response = await datasette.client.get("/")
    assert response.status_code == 200
    assert '<li><a href="/-/dashboards">Dashboards</a></li>' in response.text


@pytest.mark.asyncio
async def test_dashboards_index(datasette, datasette_metadata):
    response = await datasette.client.get("/-/dashboards")
    assert response.status_code == 200
    assert "<h1>Dashboards</h1>" in response.text

    dashboards = datasette_metadata["plugins"]["datasette-dashboards"]
    for slug, dashboard in dashboards.items():
        assert (
            f'<a href="/-/dashboards/{slug}">{dashboard["title"]}</a>' in response.text
        )
        assert f'<p>{dashboard["description"]}</p>' in response.text


@pytest.mark.asyncio
async def test_dashboard_views(datasette, datasette_metadata):
    dashboards = datasette_metadata["plugins"]["datasette-dashboards"]
    for slug, dashboard in dashboards.items():
        response = await datasette.client.get(f"/-/dashboards/{slug}")
        assert response.status_code == 200
        assert f'<h1>{dashboard["title"]}</h1>' in response.text
        assert f'<p>{dashboard["description"]}</p>' in response.text

        for index, chart in enumerate(dashboard["charts"]):
            assert f'<div id="vis-{index}" class="grid-item">'
            assert f'/{chart["db"]}.json?sql={chart["query"]}&_shape=array'
