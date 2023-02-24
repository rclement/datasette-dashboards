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
        assert "grid-template-columns: repeat(2, 1fr);" in response.text
        assert "grid-template-areas" not in response.text
        assert "grid-area:" not in response.text

        assert '<details class="dashboard-filters">' in response.text
        for key, flt in dashboard["filters"].items():
            expected_type = (
                flt["type"]
                if flt["type"] in ["text", "date", "number", "select"]
                else "text"
            )
            assert f'<label for="{key}">{flt["name"]}</label>' in response.text
            if flt["type"] == "select":
                assert f'<select id="{key}" name="{key}">' in response.text
                assert '<option value="" selected></option>' in response.text
                for option in flt["options"]:
                    assert f'<option value="{option}">'
                    assert f"{option}</option>"
            else:
                assert (
                    f'<input id="{key}" name="{key}" type="{expected_type}"'
                    in response.text
                )

        for chart_slug, chart in dashboard["charts"].items():
            assert (
                f'<div id="chart-{chart_slug}" class="dashboard-card-chart">'
                in response.text
            )

            if chart["library"] == "vega":
                assert (
                    f'<p><a href="/-/dashboards/{slug}/{chart_slug}">{chart["title"]}</a></p>'
                    in response.text
                )
                assert f"renderVegaChart('#chart-{chart_slug}', " in response.text
            elif chart["library"] == "metric":
                assert (
                    f'<p><a href="/-/dashboards/{slug}/{chart_slug}">{chart["title"]}</a></p>'
                    in response.text
                )
                assert f"renderMetricChart('#chart-{chart_slug}', " in response.text


@pytest.mark.asyncio
async def test_dashboard_view_layout(datasette_db, datasette_metadata):
    metadata = copy.deepcopy(datasette_metadata)
    metadata["plugins"]["datasette-dashboards"]["job-dashboard"]["layout"] = [
        ["analysis-note", "offers-day", "offers-day"],
        ["analysis-note", "offers-source", "offers-count"],
    ]
    datasette = Datasette([str(datasette_db)], metadata=metadata)

    response = await datasette.client.get("/-/dashboards/job-dashboard")
    assert response.status_code == 200

    assert (
        'grid-template-areas: "analysis-note offers-day offers-day " "analysis-note offers-source offers-count " ;'
        in response.text
    )
    assert "grid-area: analysis-note;" in response.text
    assert "grid-area: offers-count;" in response.text
    assert "grid-area: offers-day;" in response.text
    assert "grid-area: offers-source;" in response.text
    assert "grid-template-columns: repeat(2, 1fr);" not in response.text


@pytest.mark.asyncio
async def test_dashboard_view_parameters(datasette):
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard?date_start=2021-01-01"
    )
    assert response.status_code == 200

    assert '<details class="dashboard-filters">' in response.text
    assert '<label for="date_start">Date Start</label>' in response.text
    assert (
        '<input id="date_start" name="date_start" type="date" value="2021-01-01">'
        in response.text
    )
    assert (
        '<input id="date_end" name="date_end" type="date" value="2021-12-31">'
        in response.text
    )

    assert (
        "SELECT date(date) as day, count(*) as count FROM offers_view WHERE TRUE  AND date \\u003e= date(:date_start)   GROUP BY day ORDER BY day"
        in response.text
    )


@pytest.mark.asyncio
async def test_dashboard_view_parameters_empty(datasette):
    response = await datasette.client.get("/-/dashboards/job-dashboard?date_start=")
    assert response.status_code == 200

    assert '<details class="dashboard-filters">' in response.text
    assert '<label for="date_start">Date Start</label>' in response.text
    assert (
        '<input id="date_start" name="date_start" type="date" value="">'
        in response.text
    )
    assert (
        '<input id="date_end" name="date_end" type="date" value="2021-12-31">'
        in response.text
    )

    assert (
        "SELECT date(date) as day, count(*) as count FROM offers_view WHERE TRUE   GROUP BY day ORDER BY day"
        in response.text
    )


@pytest.mark.asyncio
async def test_dashboard_view_unknown(datasette):
    response = await datasette.client.get("/-/dashboards/unknown-dashboard")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_view_unknown_chart_db(datasette_db, datasette_metadata):
    metadata = copy.deepcopy(datasette_metadata)
    metadata["plugins"]["datasette-dashboards"]["job-dashboard"]["charts"][
        "offers-count"
    ]["db"] = "unknown_db"
    datasette = Datasette([str(datasette_db)], metadata=metadata)

    response = await datasette.client.get("/-/dashboards/job-dashboard")
    assert response.status_code == 404


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
    datasette_db, datasette_metadata, metadata, authenticated, expected_status
):
    datasette = Datasette(
        [str(datasette_db)], metadata={**datasette_metadata, **metadata}
    )

    cookies = {}
    if authenticated:
        cookies["ds_actor"] = datasette.sign({"a": {"id": "user"}}, "actor")

    slug = list(datasette_metadata["plugins"]["datasette-dashboards"].keys())[0]
    response = await datasette.client.get(f"/-/dashboards/{slug}", cookies=cookies)
    assert response.status_code == expected_status
