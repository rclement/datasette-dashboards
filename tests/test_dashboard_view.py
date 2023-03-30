import copy
import typing as t
import pytest

from pathlib import Path
from datasette.app import Datasette


@pytest.mark.asyncio
async def test_dashboard_views(datasette: Datasette) -> None:
    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    for slug, dashboard in dashboards.items():
        response = await datasette.client.get(
            f"/-/dashboards/{slug}", follow_redirects=True
        )
        assert response.status_code == 200
        assert '<li><a href="/-/dashboards">Dashboards</a></li>' in response.text
        assert f'<h1>{dashboard["title"]}</h1>' in response.text
        assert f'<p>{dashboard["description"]}</p>' in response.text
        assert "grid-template-columns: repeat(2, 1fr);" in response.text
        assert "grid-template-areas" not in response.text
        assert "grid-area:" not in response.text

        assert '<div class="dashboard-toolbar">' in response.text
        assert (
            '<button type="button" onclick="toggleFullscreen()">Fullscreen</button>'
            not in response.text
        )
        assert "autorefresh" not in response.text

        assert '<div class="dashboard-filters">' in response.text
        for key, flt in dashboard["filters"].items():
            expected_type = (
                flt["type"]
                if flt["type"] in ["text", "date", "number", "select"]
                else "text"
            )
            assert f'<legend>{flt["name"]}</legend>' in response.text
            if flt["type"] == "select":
                assert f'<select id="{key}" name="{key}">' in response.text
                assert '<option value="" selected></option>' in response.text
                if {"db", "query"} & flt.keys():
                    values = await datasette.execute(flt["db"], flt["query"])
                    for option in values:
                        assert f'<option value="{option[0]}"' in response.text
                        assert f"{option[0]}</option>" in response.text
                else:
                    for option in flt["options"]:
                        assert f'<option value="{option}"' in response.text
                        assert f"{option}</option>" in response.text
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

            if chart["library"] != "markdown":
                assert f'<a href="/-/dashboards/{slug}/{chart_slug}?' in response.text
                assert f'{chart["title"]}' in response.text
            assert f"renderChart('#chart-{chart_slug}', " in response.text


@pytest.mark.asyncio
async def test_dashboard_view_layout(
    datasette_db: Path, datasette_metadata: t.Dict[str, t.Any]
) -> None:
    metadata = copy.deepcopy(datasette_metadata)
    metadata["plugins"]["datasette-dashboards"]["job-dashboard"]["layout"] = [
        ["analysis-note", "offers-day", "offers-day"],
        ["analysis-note", "offers-source", "offers-count"],
    ]
    datasette = Datasette([str(datasette_db)], metadata=metadata)

    response = await datasette.client.get(
        "/-/dashboards/job-dashboard", follow_redirects=True
    )
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
async def test_dashboard_view_filters_default_redirect(datasette: Datasette) -> None:
    response = await datasette.client.get("/-/dashboards/job-dashboard")
    assert response.status_code == 302
    assert (
        response.headers["location"]
        == "/-/dashboards/job-dashboard?date_start=2021-01-01&date_end=2021-12-31"
    )


@pytest.mark.asyncio
async def test_dashboard_view_parameters(datasette: Datasette) -> None:
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard?date_start=2021-01-01"
    )
    assert response.status_code == 200

    assert '<div class="dashboard-filters">' in response.text
    assert "<legend>Date Start</legend>" in response.text
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
async def test_dashboard_view_parameters_empty(datasette: Datasette) -> None:
    response = await datasette.client.get("/-/dashboards/job-dashboard?date_start=")
    assert response.status_code == 200

    assert '<div class="dashboard-filters">' in response.text
    assert "<legend>Date Start</legend>" in response.text
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
async def test_dashboard_view_unknown(datasette: Datasette) -> None:
    response = await datasette.client.get("/-/dashboards/unknown-dashboard")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_view_unknown_chart_db(
    datasette_db: Path, datasette_metadata: t.Dict[str, t.Any]
) -> None:
    metadata = copy.deepcopy(datasette_metadata)
    metadata["plugins"]["datasette-dashboards"]["job-dashboard"]["charts"][
        "offers-count"
    ]["db"] = "unknown_db"
    datasette = Datasette([str(datasette_db)], metadata=metadata)

    response = await datasette.client.get("/-/dashboards/job-dashboard")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_view_allow_fullscreen(
    datasette_db: Path, datasette_metadata: t.Dict[str, t.Any]
) -> None:
    metadata = copy.deepcopy(datasette_metadata)
    metadata["plugins"]["datasette-dashboards"]["job-dashboard"]["settings"][
        "allow_fullscreen"
    ] = True
    datasette = Datasette([str(datasette_db)], metadata=metadata)

    response = await datasette.client.get(
        "/-/dashboards/job-dashboard", follow_redirects=True
    )
    assert response.status_code == 200

    assert (
        '<button type="button" onclick="toggleFullscreen()">Fullscreen</button>'
        in response.text
    )


@pytest.mark.asyncio
async def test_dashboard_view_enable_autorefresh(
    datasette_db: Path, datasette_metadata: t.Dict[str, t.Any]
) -> None:
    metadata = copy.deepcopy(datasette_metadata)
    metadata["plugins"]["datasette-dashboards"]["job-dashboard"]["settings"][
        "autorefresh"
    ] = 1
    datasette = Datasette([str(datasette_db)], metadata=metadata)

    response = await datasette.client.get(
        "/-/dashboards/job-dashboard", follow_redirects=True
    )
    assert response.status_code == 200

    assert "autorefresh(1)" in response.text


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
    datasette_db: Path,
    datasette_metadata: t.Dict[str, t.Any],
    metadata: t.Dict[str, t.Any],
    authenticated: bool,
    expected_status: int,
) -> None:
    datasette = Datasette(
        [str(datasette_db)], metadata={**datasette_metadata, **metadata}
    )

    cookies = {}
    if authenticated:
        cookies["ds_actor"] = datasette.sign({"a": {"id": "user"}}, "actor")

    slug = list(datasette_metadata["plugins"]["datasette-dashboards"].keys())[0]
    response = await datasette.client.get(
        f"/-/dashboards/{slug}", cookies=cookies, follow_redirects=True
    )
    assert response.status_code == expected_status
