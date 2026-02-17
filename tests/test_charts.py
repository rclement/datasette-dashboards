import copy
import typing as t

import pytest

from pathlib import Path
from datasette.app import Datasette


@pytest.mark.asyncio
async def test_line_chart_renders_as_vegalite(datasette: Datasette) -> None:
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard/offers-line", follow_redirects=True
    )
    assert response.status_code == 200
    assert "Offers over time (line)" in response.text
    assert '"library": "vega-lite"' in response.text
    assert '"type": "line"' in response.text
    assert '"tooltip": true' in response.text


@pytest.mark.asyncio
async def test_bar_chart_renders_as_vegalite(datasette: Datasette) -> None:
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard/offers-bar", follow_redirects=True
    )
    assert response.status_code == 200
    assert "Offers by source (bar)" in response.text
    assert '"library": "vega-lite"' in response.text
    assert '"type": "bar"' in response.text
    assert '"tooltip": true' in response.text


@pytest.mark.asyncio
async def test_area_chart_renders_as_vegalite(datasette: Datasette) -> None:
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard/offers-area", follow_redirects=True
    )
    assert response.status_code == 200
    assert "Offers over time (area)" in response.text
    assert '"library": "vega-lite"' in response.text
    assert '"type": "area"' in response.text
    assert '"tooltip": true' in response.text


@pytest.mark.asyncio
async def test_scatter_chart_renders_as_vegalite(datasette: Datasette) -> None:
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard/offers-scatter", follow_redirects=True
    )
    assert response.status_code == 200
    assert "Offers scatter" in response.text
    assert '"library": "vega-lite"' in response.text
    assert '"type": "point"' in response.text
    assert '"tooltip": true' in response.text


@pytest.mark.asyncio
async def test_pie_chart_renders_as_vegalite(datasette: Datasette) -> None:
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard/offers-pie", follow_redirects=True
    )
    assert response.status_code == 200
    assert "Offers by source (pie)" in response.text
    assert '"library": "vega-lite"' in response.text
    assert '"type": "arc"' in response.text
    assert '"tooltip": true' in response.text


@pytest.mark.asyncio
async def test_line_chart_encoding_fields(datasette: Datasette) -> None:
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard/offers-line", follow_redirects=True
    )
    assert response.status_code == 200
    # The encoding should contain x with temporal and y with quantitative
    assert '"field": "day"' in response.text
    assert '"field": "count"' in response.text


@pytest.mark.asyncio
async def test_bar_chart_horizontal(
    datasette_db: Path, datasette_metadata: t.Dict[str, t.Any]
) -> None:
    metadata = copy.deepcopy(datasette_metadata)
    metadata["plugins"]["datasette-dashboards"]["job-dashboard"]["charts"][
        "horizontal-bar"
    ] = {
        "title": "Horizontal bar",
        "db": "test",
        "query": "SELECT source, count(*) as count FROM jobs GROUP BY source",
        "library": "bar",
        "display": {
            "x": "source",
            "y": "count",
            "horizontal": True,
        },
    }
    ds = Datasette([str(datasette_db)], metadata=metadata)

    response = await ds.client.get(
        "/-/dashboards/job-dashboard/horizontal-bar", follow_redirects=True
    )
    assert response.status_code == 200
    assert '"library": "vega-lite"' in response.text
    assert '"type": "bar"' in response.text


@pytest.mark.asyncio
async def test_scatter_chart_with_color_and_size(
    datasette_db: Path, datasette_metadata: t.Dict[str, t.Any]
) -> None:
    metadata = copy.deepcopy(datasette_metadata)
    metadata["plugins"]["datasette-dashboards"]["job-dashboard"]["charts"][
        "fancy-scatter"
    ] = {
        "title": "Fancy scatter",
        "db": "test",
        "query": "SELECT id, count(*) as count, source FROM jobs GROUP BY id",
        "library": "scatter",
        "display": {
            "x": "id",
            "y": "count",
            "color": "source",
            "size": "count",
        },
    }
    ds = Datasette([str(datasette_db)], metadata=metadata)

    response = await ds.client.get(
        "/-/dashboards/job-dashboard/fancy-scatter", follow_redirects=True
    )
    assert response.status_code == 200
    assert '"library": "vega-lite"' in response.text
    assert '"type": "point"' in response.text
    assert '"field": "source"' in response.text


@pytest.mark.asyncio
async def test_line_chart_with_dict_field_spec(
    datasette_db: Path, datasette_metadata: t.Dict[str, t.Any]
) -> None:
    metadata = copy.deepcopy(datasette_metadata)
    metadata["plugins"]["datasette-dashboards"]["job-dashboard"]["charts"][
        "detailed-line"
    ] = {
        "title": "Detailed line",
        "db": "test",
        "query": "SELECT date(date) as day, count(*) as count FROM jobs GROUP BY day ORDER BY day",
        "library": "line",
        "display": {
            "x": {"field": "day", "type": "temporal", "timeUnit": "yearmonthdate"},
            "y": "count",
        },
    }
    ds = Datasette([str(datasette_db)], metadata=metadata)

    response = await ds.client.get(
        "/-/dashboards/job-dashboard/detailed-line", follow_redirects=True
    )
    assert response.status_code == 200
    assert '"library": "vega-lite"' in response.text
    assert "yearmonthdate" in response.text


@pytest.mark.asyncio
async def test_choropleth_chart_renders_as_vegalite(datasette: Datasette) -> None:
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard/offers-choropleth", follow_redirects=True
    )
    assert response.status_code == 200
    assert "Offers by region (choropleth)" in response.text
    assert '"library": "vega-lite"' in response.text
    assert '"geoshape"' in response.text


@pytest.mark.asyncio
async def test_choropleth_chart_encoding_fields(datasette: Datasette) -> None:
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard/offers-choropleth", follow_redirects=True
    )
    assert response.status_code == 200
    assert '"field": "region"' in response.text
    assert '"field": "count"' in response.text
    assert '"scheme": "blues"' in response.text


@pytest.mark.asyncio
async def test_wordcloud_chart_renders_as_vega(datasette: Datasette) -> None:
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard/offers-wordcloud", follow_redirects=True
    )
    assert response.status_code == 200
    assert "Word cloud of job titles (wordcloud)" in response.text
    assert '"library": "vega"' in response.text


@pytest.mark.asyncio
async def test_wordcloud_chart_fields(datasette: Datasette) -> None:
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard/offers-wordcloud", follow_redirects=True
    )
    assert response.status_code == 200
    assert '"wordcloud"' in response.text
    assert '"field": "word"' in response.text


@pytest.mark.asyncio
async def test_chart_types_in_dashboard_view(datasette: Datasette) -> None:
    """All chart types should render in the full dashboard view."""
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard", follow_redirects=True
    )
    assert response.status_code == 200

    for chart_slug in [
        "offers-line",
        "offers-bar",
        "offers-area",
        "offers-scatter",
        "offers-pie",
        "offers-choropleth",
        "offers-wordcloud",
    ]:
        assert (
            f'<div id="chart-{chart_slug}" class="dashboard-card-chart">'
            in response.text
        )
        assert f"renderChart('{chart_slug}', " in response.text


@pytest.mark.asyncio
async def test_chart_conversion_does_not_mutate_metadata(datasette: Datasette) -> None:
    """Verify that converting chart types doesn't modify the original metadata."""
    original_metadata = datasette._metadata["plugins"]["datasette-dashboards"]
    charts = original_metadata["job-dashboard"]["charts"]

    # Access the dashboard twice
    await datasette.client.get("/-/dashboards/job-dashboard", follow_redirects=True)
    await datasette.client.get("/-/dashboards/job-dashboard", follow_redirects=True)

    # Original metadata should still have the chart types
    assert charts["offers-line"]["library"] == "line"
    assert charts["offers-bar"]["library"] == "bar"
    assert charts["offers-area"]["library"] == "area"
    assert charts["offers-scatter"]["library"] == "scatter"
    assert charts["offers-pie"]["library"] == "pie"
    assert charts["offers-choropleth"]["library"] == "choropleth"
    assert charts["offers-wordcloud"]["library"] == "wordcloud"


@pytest.mark.asyncio
async def test_chart_type_with_filters(datasette: Datasette) -> None:
    """Chart types should work with dashboard filters."""
    response = await datasette.client.get(
        "/-/dashboards/job-dashboard/offers-line?date_start=2021-01-01"
    )
    assert response.status_code == 200
    assert '"library": "vega-lite"' in response.text
