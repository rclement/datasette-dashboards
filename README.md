# datasette-dashboards

> Datasette plugin providing data dashboards from metadata

[![PyPI](https://img.shields.io/pypi/v/datasette-dashboards.svg)](https://pypi.org/project/datasette-dashboards/)
[![Test](https://github.com/rclement/datasette-dashboards/actions/workflows/test.yml/badge.svg)](https://github.com/rclement/datasette-dashboards/actions/workflows/test.yml)
[![Demo](https://github.com/rclement/datasette-dashboards/actions/workflows/demo.yml/badge.svg)](https://github.com/rclement/datasette-dashboards/actions/workflows/demo.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/datasette-graphql/blob/master/LICENSE)

Try out a live demo at [https://datasette-dashboards-demo.vercel.app](https://datasette-dashboards-demo.vercel.app/-/dashboards)

**WARNING**: this is a highly experimental work serving as exploration and
proof-of-concept. This could become a plugin in the long run if something
interesting comes up!

## Installation

Install this plugin in the same environment as Datasette:

```bash
$ datasette install datasette-dashboards
```

## Usage

Define dashboards within `metadata.yml` / `metadata.json`:

```yaml
plugins:
  datasette-dashboards:
    my_dashboard:
      title: My Dashboard
      description: Showing some nice metrics
      visualizations:
        - title: Number of events by day
          db: jobs
          query: SELECT date(date) as day, count(*) as count FROM events GROUP BY day ORDER BY day
          chart: line
          encoding:
            x: { field: day, type: temporal }
            y: { field: count, type: quantitative }
        - title: Number of events by source
          db: jobs
          query: SELECT source, count(*) as count FROM events GROUP BY source ORDER BY count DESC
          chart: arc
          encoding:
            color: { field: source, type: nominal }
            theta: { field: count, type: quantitative }
```

_Note_: for now, data visualizations are dynamically generated using `vega-lite`.
For simplicity sake, axes configuration are mapped to the same terminology depending
on the chart type. Please refer to [Vega-Lite Documentation](https://vega.github.io/vega-lite/docs/).

A new menu entry is now available, pointing at `/-/dashboards` to access all defined dashboards.

## Development

To set up this plugin locally, first checkout the code.
Then create a new virtual environment and the required dependencies:

```bash
pipenv install -d
pipenv shell
```

To run the tests:

```bash
pytest
```

## Demo

With the developmnent environment setup, you can run the demo locally:

```bash
datasette --metadata demo/metadata.yml demo/jobs.db
```

## License

Licensed under Apache License, Version 2.0

Copyright (c) 2021 - present Romain Clement
