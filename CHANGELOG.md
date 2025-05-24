# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Support markdown configuration in markdown chart definition


## [0.7.1] - 2025-03-10
### Fixed
- Support bracketed fields in query parameters replacement
- Demo Vercel deployment resulting in error 500

### Changed
- Update dependencies

## [0.7.0] - 2024-11-14
### Added
- Add Python 3.12 and 3.13 support
- Use `package.json` to track and bundle external JS dependencies

### Changed
- Update dependencies

### Removed
- BREAKING: drop Python 3.8 support

## [0.6.2] - 2023-08-23
### Fixed
- Improve compatibility with new JSON API format introduced in Datasette 1.0a3

## [0.6.1] - 2023-08-21
### Changed
- Switch `select` filter to autocomplete text filter when more than 100 options are provided

## [0.6.0] - 2023-08-18
### Added
- Enable extra extensions for Markdown rendering
- Chart row limit warning tooltip

### Fixed
- Markdown lists rendering
- Text filter style
- Chart page display with no filters defined

### Changed
- Update README with dashboard layout examples
- Update README demo dashboard screenshot
- Update demo with full-text search filter for job titles
- Update dependencies

### Internal
- Enable strict `mypy` check

## [0.5.3] - 2023-06-05
### Fixed
- Allow dashboard metadata without filters and charts sections

### Changed
- Update dependencies

## [0.5.2] - 2023-05-02
### Fixed
- Update vega-lite definition in README.md (thanks @hydrosquall) (PR #107)
- Make dashboard filters form compatible with Datasette-Lite

## Changed
- Update dependencies

## [0.5.1] - 2023-04-25
### Fixed
- Vega-Lite chart tooltip style rendering
- Charts data URL are absolute and use optional `base_url` setting

### Changed
- Update demo
- Update dependencies

## [0.5.0] - 2023-04-20
### Added
- Missing `py.typed` file to distribute type information

### Fixed
- Make Vega charts deterministic

### Changed
- Updated README demo dashboard screenshot
- BREAKING: Removed support for Python 3.7

### Internal
- Automatic demo dashboard screenshot
- Package publishing to test index on master branch
- Use `poetry` instead of `pipenv` and `setup.py` for package management
- Remove unused dev dependencies

## [0.4.0] - 2023-03-30
### Added
- Table chart component
- Map chart component
- Fullscreen mode for dashboards
- Autorefresh mode for dashboards
- Allow embedding dashboards and charts

### Changed
- Improve filters layout
- Embed external static assets for Vega, Vega-Lite and Vega-Embed
- Update dependencies

### Fixed
- Menu not showing in plugin pages

### Internal
- Add type hints and mypy integration

## [0.3.0] - 2023-03-14
### Added
- Select filter type with static and dynamic values
- BREAKING: Support for Vega charts with the new `vega` library

### Changed
- BREAKING: Renamed `vega` library to `vega-lite`

### Fixed
- Allow quotes in chart SQL query
- Automatically redirect with dashboard default filter values
- Navigation breadcrumbs

### Changed
- Update dependencies

### Internal
- Add preview deployment for branches

## [0.2.2] - 2023-01-05
### Fixed
- Pass database as string to execute sql permission check (thanks @badboy) (PR #47)

### Changed
- Update dependencies

## [0.2.1] - 2022-12-22
### Added
- Support for Python 3.11
- Update dependencies

## [0.2.0] - 2022-04-30
### Added
- Support for Python 3.10
- Renovatebot configuration

### Changed
- Mention the metric library in README.md (thanks @hydrosquall) (PR #20)
- Pin dev dependencies in Pipfile
- Update dependencies

### Removed
- Support for Python 3.6 (end of life)

## [0.1.6] - 2021-06-19
### Added
- Add dashboard filters feature

## [0.1.5] - 2021-05-23
### Fixed
- Fix query URI encoding in AJAX calls
- Fix Python packaging `setup.py`

## [0.1.4] - 2021-05-10
### Added
- Add standalone chart view from dashboard

### Changed
- BREAKING: `charts` property is now a dictionary
- BREAKING: removed `alias` property for charts
- BREAKING: dashboard layout is now using chart key identifiers from the `charts` property
- Set mobile layout breakpoint to 800px for better readability

## [0.1.3] - 2021-05-01
### Added
- Metric chart component

### Changed
- BREAKING: dashboard layout is now using chart identifiers using the `alias` property

## [0.1.2] - 2021-04-29
### Added
- Custom dashboard layout
- Markdown component

### Changed
- Design improvements

## [0.1.1] - 2021-04-25
### Fixed
- Add missing packages for test requirements in `setup.py`

### Changed
- BREAKING: update plugin metadata spec to be chart-library agnostic
- Update demo with choropleth map and interactive charts
- Update README.md

### Added
- Respect view-instance and execute-sql permissions
- More unit tests

## [0.1.0] - 2021-04-24
### Added
- Initial release of `datasette-dashboards`

[Unreleased]: https://github.com/rclement/datasette-dashboards/compare/0.7.1...HEAD
[0.7.1]: https://github.com/rclement/datasette-dashboards/compare/0.7.0...0.7.1
[0.7.0]: https://github.com/rclement/datasette-dashboards/compare/0.6.2...0.7.0
[0.6.2]: https://github.com/rclement/datasette-dashboards/compare/0.6.1...0.6.2
[0.6.1]: https://github.com/rclement/datasette-dashboards/compare/0.6.0...0.6.1
[0.6.0]: https://github.com/rclement/datasette-dashboards/compare/0.5.3...0.6.0
[0.5.3]: https://github.com/rclement/datasette-dashboards/compare/0.5.2...0.5.3
[0.5.2]: https://github.com/rclement/datasette-dashboards/compare/0.5.1...0.5.2
[0.5.1]: https://github.com/rclement/datasette-dashboards/compare/0.5.0...0.5.1
[0.5.0]: https://github.com/rclement/datasette-dashboards/compare/0.4.0...0.5.0
[0.4.0]: https://github.com/rclement/datasette-dashboards/compare/0.3.0...0.4.0
[0.3.0]: https://github.com/rclement/datasette-dashboards/compare/0.2.2...0.3.0
[0.2.2]: https://github.com/rclement/datasette-dashboards/compare/0.2.1...0.2.2
[0.2.1]: https://github.com/rclement/datasette-dashboards/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/rclement/datasette-dashboards/compare/0.1.6...0.2.0
[0.1.6]: https://github.com/rclement/datasette-dashboards/compare/0.1.5...0.1.6
[0.1.5]: https://github.com/rclement/datasette-dashboards/compare/0.1.4...0.1.5
[0.1.4]: https://github.com/rclement/datasette-dashboards/compare/0.1.3...0.1.4
[0.1.3]: https://github.com/rclement/datasette-dashboards/compare/0.1.2...0.1.3
[0.1.2]: https://github.com/rclement/datasette-dashboards/compare/0.1.1...0.1.2
[0.1.1]: https://github.com/rclement/datasette-dashboards/compare/0.1.0...0.1.1
[0.1.0]: https://github.com/rclement/datasette-dashboards/releases/tag/0.1.0
