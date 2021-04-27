import copy
import pytest

from datasette.app import Datasette


@pytest.mark.asyncio
async def test_dashboard_views(datasette):
    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    for slug, dashboard in dashboards.items():
        response = await datasette.client.get(f"/-/dashboards/{slug}")
        assert response.status_code == 200
        assert f'<h1>{dashboard["title"]}</h1>' in response.text
        assert f'<p>{dashboard["description"]}</p>' in response.text
        assert "grid-template-areas" not in response.text

        for index, chart in enumerate(dashboard["charts"]):
            assert f'<p><a href="/{chart["db"]}?sql={chart["query"]}">{chart["title"]}</a></p>'
            assert f'<div id="vis-{index}" class="grid-item">'
            assert f'/{chart["db"]}.json?sql={chart["query"]}&_shape=array'


@pytest.mark.asyncio
async def test_dashboard_view_layout(datasette):
    original_metadata = datasette._metadata
    try:
        metadata = copy.deepcopy(datasette._metadata)
        metadata["plugins"]["datasette-dashboards"]["job-dashboard"]["layout"] = [
            ["chart1"],
            ["chart2"],
        ]
        datasette._metadata = metadata
        response = await datasette.client.get(f"/-/dashboards/job-dashboard")
        assert response.status_code == 200

        assert 'grid-template-areas: "chart1 " "chart2 " ;' in response.text
        assert "grid-area: chart1;" in response.text
        assert "grid-area: chart2;" in response.text
    finally:
        datasette._metadata = original_metadata


@pytest.mark.asyncio
async def test_dashboard_view_unknown(datasette):
    response = await datasette.client.get("/-/dashboards/unknown-dashboard")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_view_unknown_chart_db(datasette):
    original_metadata = datasette._metadata
    try:
        metadata = copy.deepcopy(datasette._metadata)
        metadata["plugins"]["datasette-dashboards"]["job-dashboard"]["charts"][0][
            "db"
        ] = "unknown_db"
        datasette._metadata = metadata
        response = await datasette.client.get(f"/-/dashboards/job-dashboard")
        assert response.status_code == 404
    finally:
        datasette._metadata = original_metadata


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "metadata,authenticated,expected_status",
    [
        # Deny all access
        ({"allow": False}, False, 403),
        ({"allow": False}, True, 403),
        ({"allow_sql": False}, False, 403),
        ({"allow_sql": False}, True, 403),
        # Allow all access
        ({"allow": True}, False, 200),
        ({"allow": True}, True, 200),
        ({"allow_sql": True}, False, 200),
        ({"allow_sql": True}, True, 200),
        # Allow only to logged in user
        ({"allow": {"id": "user"}}, False, 403),
        ({"allow": {"id": "user"}}, True, 200),
        ({"allow_sql": {"id": "user"}}, False, 403),
        ({"allow_sql": {"id": "user"}}, True, 200),
    ],
)
async def test_dashboard_view_permissions(
    datasette, metadata, authenticated, expected_status
):
    original_metadata = datasette._metadata
    try:
        datasette._metadata = {**datasette._metadata, **metadata}
        cookies = {}
        if authenticated:
            cookies["ds_actor"] = datasette.sign({"a": {"id": "user"}}, "actor")
        slug = list(datasette._metadata["plugins"]["datasette-dashboards"].keys())[0]
        response = await datasette.client.get(f"/-/dashboards/{slug}", cookies=cookies)
        assert response.status_code == expected_status
    finally:
        datasette._metadata = original_metadata
