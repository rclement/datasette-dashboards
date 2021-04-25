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
