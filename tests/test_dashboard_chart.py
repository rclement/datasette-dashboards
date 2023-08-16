import copy
import typing as t
import pytest

from pathlib import Path
from datasette.app import Datasette


@pytest.mark.asyncio
async def test_dashboard_chart(datasette: Datasette) -> None:
    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    for slug, dashboard in dashboards.items():
        for chart_slug, chart in dashboard["charts"].items():
            props = chart.keys()
            response = await datasette.client.get(f"/-/dashboards/{slug}/{chart_slug}")
            assert response.status_code == 200
            assert '<li><a href="/-/dashboards">Dashboards</a></li>' in response.text
            assert f'<h1>{dashboard["title"]}</h1>' in response.text
            if "title" in props:
                assert chart["title"] in response.text
            if "db" in props and "query" in props:
                assert "View and edit SQL" in response.text


@pytest.mark.asyncio
async def test_dashboard_chart_unknown_dashboard(datasette: Datasette) -> None:
    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    dashboard = list(dashboards.values())[0]
    chart_slug = list(dashboard["charts"].items())[0][0]

    response = await datasette.client.get(
        f"/-/dashboards/unknown-dashboard/{chart_slug}"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_chart_unknown_chart(datasette: Datasette) -> None:
    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    slug = list(dashboards.keys())[0]

    response = await datasette.client.get(f"/-/dashboards/{slug}/unknown-chart")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_chart_parameters(datasette: Datasette) -> None:
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard/offers-day?date_start=2021-01-01"
    )
    assert response.status_code == 200
    assert (
        "SELECT date(date) as day, count(*) as count FROM offers_view WHERE TRUE  AND date \\u003e= date(:date_start)   GROUP BY day ORDER BY day"
        in response.text
    )


@pytest.mark.asyncio
async def test_dashboard_chart_parameters_empty(datasette: Datasette) -> None:
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard/offers-day?date_start="
    )
    assert response.status_code == 200
    assert (
        "SELECT date(date) as day, count(*) as count FROM offers_view WHERE TRUE   GROUP BY day ORDER BY day"
        in response.text
    )


@pytest.mark.asyncio
async def test_dashboard_chart_no_filters(
    datasette_db: Path, datasette_metadata: t.Dict[str, t.Any]
) -> None:
    metadata = copy.deepcopy(datasette_metadata)
    metadata["plugins"]["datasette-dashboards"]["job-dashboard"].pop("filters")
    datasette = Datasette([str(datasette_db)], metadata=metadata)

    response = await datasette.client.get("/-/dashboards/job-dashboard/offers-day")
    assert response.status_code == 200
