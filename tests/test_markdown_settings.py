import pytest

import typing as t
from pathlib import Path

from datasette.app import Datasette


def lstriplines(s: str) -> str:
    return "\n".join(line.lstrip() for line in s.splitlines())


@pytest.fixture()
def datasette_md_metadata(datasette_db: Path) -> t.Dict[str, t.Any]:
    metadata = {
        "plugins": {
            "datasette-dashboards": {
                "job-dashboard": {
                    "title": "Job dashboard",
                    "description": "Gathering metrics about jobs",
                    "settings": {"allow_fullscreen": False},
                    "charts": {
                        "analysis-note": {
                            "library": "markdown",
                            "display": lstriplines(
                                """
                                # Analysis details {: name="notes"}

                                We wanted to analyze data from job offers, using the **`python` search keyword**
                                from three sources of job-boards:

                                | Board name | URL                       |
                                | ---------- | ------------------------- |
                                | APEC       | https://www.apec.fr       |
                                | Indeed     | https://fr.indeed.com/    |
                                | RegionsJob | https://regionsjob.com    |
                            """
                            ),
                        },
                    },
                },
            },
        },
    }
    return metadata


dashboard_slug = "job-dashboard"
chart_slug = "analysis-note"


@pytest.mark.asyncio
async def test_md_settings_defaults(
    datasette_db: Path, datasette_md_metadata: t.Dict[str, t.Any]
) -> None:
    """
    The default settings for markdown should allow tables to be generated,
    but not allow attributes on tags.

    The datasette_md_metadata fixture does not change these defaults.
    """
    datasette = Datasette([str(datasette_db)], metadata=datasette_md_metadata)
    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    chart = dashboards[dashboard_slug]["charts"][chart_slug]
    assert "settings" not in chart.keys()
    response = await datasette.client.get(
        f"/-/dashboards/{dashboard_slug}/{chart_slug}/embed"
    )
    assert response.status_code == 200
    # Make sure we have the header, without the attribute
    assert "<h1>Analysis details</h1>" in response.text
    # Make sure we have the table
    assert "<table>" in response.text
    assert "<th>Board name</th>" in response.text
    assert "<td>APEC</td>" in response.text


@pytest.mark.asyncio
async def test_md_settings_extensions(
    datasette_db: Path, datasette_md_metadata: t.Dict[str, t.Any]
) -> None:
    """
    The default settings for markdown should allow tables to be generated,
    but not allow attributes on tags.

    In this test we specifically limit the extensions to `attr_list`
    (which is normally included in `extra`), disabling table generation.
    However, since we don't specify `extra_attrs`, the attribute is
    still not allowed in the resulting HTML.
    """
    meta = datasette_md_metadata["plugins"]["datasette-dashboards"]
    meta_chart = meta[dashboard_slug]["charts"][chart_slug]
    meta_chart["settings"] = {"extensions": ["attr_list"]}

    datasette = Datasette([str(datasette_db)], metadata=datasette_md_metadata)
    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    chart = dashboards[dashboard_slug]["charts"][chart_slug]
    assert "settings" in chart.keys()
    response = await datasette.client.get(
        f"/-/dashboards/{dashboard_slug}/{chart_slug}/embed"
    )
    assert response.status_code == 200
    # Make sure we have the header, without the attribute
    assert "<h1>Analysis details</h1>" in response.text
    # Make sure we do not have our table
    assert "<th>Board name</th>" not in response.text
    assert "<td>APEC</td>" not in response.text


@pytest.mark.asyncio
async def test_md_settings_attrs(
    datasette_db: Path, datasette_md_metadata: t.Dict[str, t.Any]
) -> None:
    """
    The default settings for markdown should allow tables to be generated,
    but not allow attributes on tags.

    In this test we allow the `name` attr on the `h1` tag
    """
    meta = datasette_md_metadata["plugins"]["datasette-dashboards"]
    meta_chart = meta[dashboard_slug]["charts"][chart_slug]
    meta_chart["settings"] = {"extra_attrs": {"h1": "name"}}

    datasette = Datasette([str(datasette_db)], metadata=datasette_md_metadata)
    dashboards = datasette._metadata["plugins"]["datasette-dashboards"]
    chart = dashboards[dashboard_slug]["charts"][chart_slug]
    assert "settings" in chart.keys()
    response = await datasette.client.get(
        f"/-/dashboards/{dashboard_slug}/{chart_slug}/embed"
    )
    assert response.status_code == 200
    # Make sure we have the header, without the attribute
    assert '<h1 name="notes">Analysis details</h1>' in response.text
    # Make sure we have the table, as we haven't messed with extensions
    assert "<table>" in response.text
    assert "<th>Board name</th>" in response.text
    assert "<td>APEC</td>" in response.text
