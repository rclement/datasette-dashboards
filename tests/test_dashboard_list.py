import copy
import pytest


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
async def test_dashboard_list_index_empty(datasette):
    original_metadata = datasette._metadata
    try:
        metadata = copy.deepcopy(datasette._metadata)
        del metadata["plugins"]
        datasette._metadata = metadata
        response = await datasette.client.get("/-/dashboards")
        assert response.status_code == 200
        assert "<h1>Dashboards</h1>" in response.text
        assert "<p>No dashboards found</p>" in response.text
    finally:
        datasette._metadata = original_metadata


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
    datasette, metadata, authenticated, expected_status
):
    original_metadata = datasette._metadata
    try:
        datasette._metadata = {**datasette._metadata, **metadata}
        cookies = {}
        if authenticated:
            cookies["ds_actor"] = datasette.sign({"a": {"id": "user"}}, "actor")
        response = await datasette.client.get("/-/dashboards", cookies=cookies)
        assert response.status_code == expected_status
    finally:
        datasette._metadata = original_metadata
