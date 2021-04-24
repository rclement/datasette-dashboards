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
                    "visualizations": [
                        {
                            "title": "Number of offers by day",
                            "db": "test",
                            "query": "SELECT date(date) as day, count(*) as count FROM jobs GROUP BY day ORDER BY day",
                            "chart": "line",
                            "encoding": {
                                "x": {"field": "day", "type": "temporal"},
                                "y": {"field": "count", "type": "quantitative"},
                            },
                        },
                        {
                            "title": "Number of offers by source",
                            "db": "test",
                            "query": "SELECT source, count(*) as count FROM jobs GROUP BY source ORDER BY count DESC",
                            "chart": "bar",
                            "encoding": {
                                "color": {"field": "source", "type": "nominal"},
                                "theta": {"field": "count", "type": "quantitative"},
                            },
                        },
                    ],
                }
            }
        }
    }


@pytest.fixture(scope="session")
def datasette(datasette_db, datasette_metadata):
    return Datasette([str(datasette_db)], metadata=datasette_metadata)
