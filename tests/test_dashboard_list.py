import copy
import pytest

from datasette.app import Datasette


@pytest.mark.asyncio
async def test_dashboard_list_index(datasette):
    response = await datasette.client.get("/-/dashboards")
    assert response.status_code == 200
    assert "<h1>Dashboards</h1>" in response.text

    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    for slug, dashboard in dashboards.items():
        assert (
            f'<a href="/-/dashboards/{slug}">{dashboard["title"]}</a>' in response.text
        )
        assert f'<p>{dashboard["description"]}</p>' in response.text


@pytest.mark.asyncio
async def test_dashboard_list_index_empty(datasette_db, datasette_metadata):
    metadata = copy.deepcopy(datasette_metadata)
    del metadata["plugins"]
    datasette = Datasette([str(datasette_db)], metadata=metadata)
    response = await datasette.client.get("/-/dashboards")
    assert response.status_code == 200
    assert "<h1>Dashboards</h1>" in response.text
    assert "<p>No dashboards found</p>" in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "metadata,authenticated,expected_status",
    [
        # Deny all access
        ({"allow": False}, False, 403),
        ({"allow": False}, True, 403),
        # Allow all access
        ({"allow": True}, False, 200),
        ({"allow": True}, True, 200),
        # Allow only to logged in user
        ({"allow": {"id": "user"}}, False, 403),
        ({"allow": {"id": "user"}}, True, 200),
    ],
)
async def test_dashboard_list_permissions(
    datasette_db, datasette_metadata, metadata, authenticated, expected_status
):
    datasette = Datasette(
        [str(datasette_db)], metadata={**datasette_metadata, **metadata}
    )

    cookies = {}
    if authenticated:
        cookies["ds_actor"] = datasette.sign({"a": {"id": "user"}}, "actor")

    response = await datasette.client.get("/-/dashboards", cookies=cookies)
    assert response.status_code == expected_status
