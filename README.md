# datasette-dashboards

> Bringing data dashboards to Datasette!

Datasette plugin providing data dashboards from metadata.

**WARNING**: this is a highly experimental work serving as exploration and
proof-of-concept. This could become a plugin in the long run if something
interesting comes up!

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

A new URL is now available at `/-/dashboards` listing all defined dashboards.

## Setup

```bash
pipenv install -d
pipenv shell
```

## Examples

```bash
datasette \
    --template-dir datasette_dashboards/templates \
    --plugins-dir datasette_dashboards \
    --metadata example/metadata.yml \
    example/jobs.db
```
