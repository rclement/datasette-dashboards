import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from invoke import task
from invoke.context import Context

app_path = "datasette_dashboards"
tests_path = "tests"


@task
def format(ctx: Context) -> None:
    ctx.run("uv run ruff format .", echo=True, pty=True)


@task
def lint(ctx: Context) -> None:
    ctx.run(f"uv run ruff check {app_path} {tests_path}", echo=True, pty=True)


@task
def typing(ctx: Context) -> None:
    ctx.run(
        f"uv run mypy --strict {app_path} {tests_path}",
        echo=True,
        pty=True,
    )


@task
def test(ctx: Context) -> None:
    ctx.run(
        f"uv run pytest -v"
        f" --cov={app_path} --cov={tests_path}"
        f" --cov-branch --cov-report=term-missing"
        f" {tests_path}",
        echo=True,
        pty=True,
    )


@task(lint, typing, test)
def qa(ctx: Context) -> None:
    pass


@task
def shots(ctx: Context) -> None:
    demo_shots_dir = Path("demo/shots")
    demo_port = 8001
    base_url = f"http://localhost:{demo_port}"

    pages = [
        ("home", "/"),
        ("dashboards", "/-/dashboards"),
        (
            "dashboard-job-offers-stats",
            "/-/dashboards/job-offers-stats?date_start=2021-01-01&date_end=2021-05-01&source=&region=",
        ),
        ("dashboard-chart-types", "/-/dashboards/chart-types"),
        ("dashboard-single-chart", "/-/dashboards/chart-types/map-chart"),
    ]

    demo_shots_dir.mkdir(exist_ok=True)

    shots_yaml = "\n".join(
        f"- url: {base_url}{path}\n"
        f"  output: {demo_shots_dir}/{name}.png\n"
        f"  wait: 1000\n"
        f"  width: 1440\n"
        f"  retina: true"
        for name, path in pages
    )

    server = subprocess.Popen(
        [
            "uv",
            "run",
            "datasette",
            "demo/jobs.db",
            "--metadata",
            "demo/metadata.yml",
            "--template-dir",
            "demo/templates",
            "-p",
            str(demo_port),
        ],
    )

    try:
        for _ in range(30):
            try:
                urllib.request.urlopen(base_url)
                break
            except (urllib.error.URLError, OSError):
                time.sleep(0.5)

        shots_file = demo_shots_dir / "shots.yml"
        shots_file.write_text(shots_yaml)
        ctx.run(f"uvx shot-scraper multi {shots_file}", echo=True, pty=True)
    finally:
        server.terminate()
        shots_file.unlink(missing_ok=True)
