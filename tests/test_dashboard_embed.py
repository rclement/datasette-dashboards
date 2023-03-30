import pytest

from datasette.app import Datasette


@pytest.mark.asyncio
async def test_dashboard_embed(datasette: Datasette) -> None:
    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    for slug, dashboard in dashboards.items():
        response = await datasette.client.get(
            f"/-/dashboards/{slug}/embed", follow_redirects=True
        )
        assert response.status_code == 200
        assert f'<h1>{dashboard["title"]}</h1>' in response.text
        assert f'<p>{dashboard["description"]}</p>' in response.text


@pytest.mark.asyncio
async def test_dashboard_embed_filters_default_redirect(datasette: Datasette) -> None:
    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    slug = list(dashboards.keys())[0]
    response = await datasette.client.get(f"/-/dashboards/{slug}/embed")
    assert response.status_code == 302
