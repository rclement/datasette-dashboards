import pytest
import sqlite_utils

from datasette.app import Datasette
from faker import Faker


@pytest.fixture(scope="session")
def datasette_db(tmp_path_factory):
    faker = Faker()
    db_directory = tmp_path_factory.mktemp("dbs")
    db_path = db_directory / "test.db"
    db = sqlite_utils.Database(db_path)
    db["jobs"].insert_all(
        [
            dict(
                id=i + 1,
                date=faker.past_date().isoformat(),
                source=faker.company(),
                job=faker.job(),
            )
            for i in range(10)
        ],
        pk="id",
    )

    return db_path


@pytest.fixture(scope="session")
def datasette_metadata():
    return {
        "plugins": {
            "datasette-dashboards": {
                "job-dashboard": {
                    "title": "Job dashboard",
                    "description": "Gathering metrics about jobs",
                    "filters": {
                        "date_start": {
                            "name": "Date Start",
                            "type": "date",
                            "default": "2021-01-01",
                        },
                        "date_end": {
                            "name": "Date End",
                            "type": "date",
                            "default": "2021-12-31",
                        },
                        "text_filter": {
                            "name": "Text Filter",
                            "type": "text",
                        },
                        "number_filter": {
                            "name": "Number Filter",
                            "type": "number",
                            "min": 12,
                            "max": 42,
                            "step": 2,
                        },
                        "unknown_filter": {
                            "name": "Unknown Filter",
                            "type": "unknown",
                        },
                    },
                    "charts": {
                        "analysis-note": {
                            "library": "markdown",
                            "display": """
                                # Analysis details

                                We wanted to analyze data from job offers, using the **`python` search keyword**
                                from three sources of job-boards:
                                [APEC](https://www.apec.fr),
                                [Indeed](https://fr.indeed.com/) and
                                [RegionsJob](https://regionsjob.com).

                                ## Process

                                The process was in 3 steps:

                                - Extraction
                                - Transformation
                                - Loading

                                After the ETL process, an extra data enrichment step was developed to provide
                                location geocoding, based on place names.

                                ## SQL query

                                ```sql
                                SELECT
                                    date(date) as day,
                                    count(*) as count
                                FROM offers_view
                                GROUP BY day
                                ORDER BY day
                                ```
                            """,
                        },
                        "offers-count": {
                            "title": "Total number of offers",
                            "db": "test",
                            "query": "SELECT count(*) as count FROM offers_view;",
                            "library": "metric",
                            "display": {
                                "field": "count",
                                "prefix": "",
                                "suffix": " offers",
                            },
                        },
                        "offers-day": {
                            "title": "Number of offers by day",
                            "db": "test",
                            "query": "SELECT date(date) as day, count(*) as count FROM offers_view WHERE TRUE [[ AND date >= date(:date_start) ]] [[ AND date <= date(:date_end) ]] GROUP BY day ORDER BY day",
                            "library": "vega",
                            "display": {
                                "mark": {
                                    "type": "line",
                                    "tooltip": "true",
                                },
                                "encoding": {
                                    "x": {"field": "day", "type": "temporal"},
                                    "y": {"field": "count", "type": "quantitative"},
                                },
                            },
                        },
                        "offers-source": {
                            "title": "Number of offers by source",
                            "db": "test",
                            "query": "SELECT source, count(*) as count FROM jobs GROUP BY source ORDER BY count DESC",
                            "library": "vega",
                            "display": {
                                "chart": {
                                    "type": "bar",
                                    "tooltip": "true",
                                },
                                "encoding": {
                                    "color": {"field": "source", "type": "nominal"},
                                    "theta": {"field": "count", "type": "quantitative"},
                                },
                            },
                        },
                    },
                }
            }
        }
    }


@pytest.fixture(scope="session")
def datasette(datasette_db, datasette_metadata):
    return Datasette([str(datasette_db)], metadata=datasette_metadata)
