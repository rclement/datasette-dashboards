import typing as t

import pytest

from datasette_dashboards.chart_types import (
    CHART_TYPES,
    convert_chart_type,
    _normalize_field,
)


# --- _normalize_field ---


def test_normalize_field_string() -> None:
    result = _normalize_field("day", "temporal")
    assert result == {"field": "day", "type": "temporal"}


def test_normalize_field_dict_with_type() -> None:
    result = _normalize_field({"field": "day", "type": "ordinal"}, "temporal")
    assert result == {"field": "day", "type": "ordinal"}


def test_normalize_field_dict_without_type_uses_default() -> None:
    result = _normalize_field({"field": "day"}, "temporal")
    assert result == {"field": "day", "type": "temporal"}


def test_normalize_field_dict_missing_field_key_raises() -> None:
    with pytest.raises(ValueError, match="'field' key"):
        _normalize_field({"type": "temporal"}, "nominal")


def test_normalize_field_dict_with_extra_keys() -> None:
    result = _normalize_field(
        {"field": "day", "type": "temporal", "timeUnit": "yearmonthdate"},
        "nominal",
    )
    assert result == {
        "field": "day",
        "type": "temporal",
        "timeUnit": "yearmonthdate",
    }


# --- convert_chart_type (generic) ---


def test_convert_non_chart_type_returns_unchanged() -> None:
    chart: dict[str, t.Any] = {"library": "vega-lite", "display": {"mark": "bar"}}
    result = convert_chart_type(chart)
    assert result is chart


def test_convert_no_library_returns_unchanged() -> None:
    chart: dict[str, t.Any] = {"display": {"mark": "bar"}}
    result = convert_chart_type(chart)
    assert result is chart


def test_convert_does_not_mutate_original() -> None:
    chart: dict[str, t.Any] = {
        "library": "line",
        "display": {"x": "day", "y": "count"},
        "db": "test",
        "query": "SELECT * FROM t",
    }
    original_library = chart["library"]
    original_display: dict[str, t.Any] = {k: v for k, v in chart["display"].items()}
    convert_chart_type(chart)
    assert chart["library"] == original_library
    assert chart["display"] == original_display


def test_convert_preserves_non_display_fields() -> None:
    chart: dict[str, t.Any] = {
        "library": "line",
        "title": "My chart",
        "db": "test",
        "query": "SELECT * FROM t",
        "display": {"x": "day", "y": "count"},
    }
    result = convert_chart_type(chart)
    assert result["title"] == "My chart"
    assert result["db"] == "test"
    assert result["query"] == "SELECT * FROM t"


# --- line chart ---


def test_line_simple_fields() -> None:
    chart: dict[str, t.Any] = {
        "library": "line",
        "display": {"x": "day", "y": "count"},
    }
    result = convert_chart_type(chart)
    assert result["library"] == "vega-lite"
    assert result["display"] == {
        "mark": {"type": "line", "tooltip": True},
        "encoding": {
            "x": {"field": "day", "type": "temporal"},
            "y": {"field": "count", "type": "quantitative"},
        },
    }


def test_line_with_color() -> None:
    chart: dict[str, t.Any] = {
        "library": "line",
        "display": {"x": "day", "y": "count", "color": "source"},
    }
    result = convert_chart_type(chart)
    encoding = result["display"]["encoding"]
    assert encoding["color"] == {"field": "source", "type": "nominal"}
    assert encoding["opacity"] == {
        "condition": {"param": "highlight", "value": 1},
        "value": 0.2,
    }
    assert result["display"]["params"] == [
        {
            "name": "highlight",
            "select": {
                "type": "point",
                "fields": ["source"],
                "on": "mouseover",
            },
            "bind": "legend",
        }
    ]


def test_line_without_color_no_highlight() -> None:
    chart: dict[str, t.Any] = {
        "library": "line",
        "display": {"x": "day", "y": "count"},
    }
    result = convert_chart_type(chart)
    assert "params" not in result["display"]
    assert "opacity" not in result["display"]["encoding"]


def test_line_custom_xtype() -> None:
    chart: dict[str, t.Any] = {
        "library": "line",
        "display": {"x": "day", "y": "count", "xtype": "ordinal"},
    }
    result = convert_chart_type(chart)
    assert result["display"]["encoding"]["x"]["type"] == "ordinal"


def test_line_custom_ytype() -> None:
    chart: dict[str, t.Any] = {
        "library": "line",
        "display": {"x": "day", "y": "count", "ytype": "nominal"},
    }
    result = convert_chart_type(chart)
    assert result["display"]["encoding"]["y"]["type"] == "nominal"


def test_line_dict_field_spec() -> None:
    chart: dict[str, t.Any] = {
        "library": "line",
        "display": {
            "x": {"field": "day", "type": "temporal", "timeUnit": "yearmonthdate"},
            "y": "count",
        },
    }
    result = convert_chart_type(chart)
    assert result["display"]["encoding"]["x"] == {
        "field": "day",
        "type": "temporal",
        "timeUnit": "yearmonthdate",
    }


# --- area chart ---


def test_area_simple_fields() -> None:
    chart: dict[str, t.Any] = {
        "library": "area",
        "display": {"x": "day", "y": "revenue"},
    }
    result = convert_chart_type(chart)
    assert result["library"] == "vega-lite"
    assert result["display"] == {
        "mark": {"type": "area", "tooltip": True},
        "encoding": {
            "x": {"field": "day", "type": "temporal"},
            "y": {"field": "revenue", "type": "quantitative"},
        },
    }


def test_area_with_color() -> None:
    chart: dict[str, t.Any] = {
        "library": "area",
        "display": {"x": "day", "y": "revenue", "color": "category"},
    }
    result = convert_chart_type(chart)
    encoding = result["display"]["encoding"]
    assert encoding["color"] == {"field": "category", "type": "nominal"}
    assert encoding["opacity"] == {
        "condition": {"param": "highlight", "value": 1},
        "value": 0.2,
    }
    assert result["display"]["params"] == [
        {
            "name": "highlight",
            "select": {
                "type": "point",
                "fields": ["category"],
                "on": "mouseover",
            },
            "bind": "legend",
        }
    ]


def test_area_without_color_no_highlight() -> None:
    chart: dict[str, t.Any] = {
        "library": "area",
        "display": {"x": "day", "y": "revenue"},
    }
    result = convert_chart_type(chart)
    assert "params" not in result["display"]
    assert "opacity" not in result["display"]["encoding"]


# --- bar chart ---


def test_bar_simple_fields() -> None:
    chart: dict[str, t.Any] = {
        "library": "bar",
        "display": {"x": "source", "y": "count"},
    }
    result = convert_chart_type(chart)
    assert result["library"] == "vega-lite"
    assert result["display"] == {
        "mark": {"type": "bar", "tooltip": True},
        "encoding": {
            "x": {"field": "source", "type": "nominal"},
            "y": {"field": "count", "type": "quantitative"},
        },
    }


def test_bar_horizontal() -> None:
    chart: dict[str, t.Any] = {
        "library": "bar",
        "display": {
            "x": "source",
            "y": "count",
            "horizontal": True,
        },
    }
    result = convert_chart_type(chart)
    encoding = result["display"]["encoding"]
    assert encoding["x"] == {"field": "count", "type": "quantitative"}
    assert encoding["y"] == {"field": "source", "type": "nominal"}


def test_bar_with_color() -> None:
    chart: dict[str, t.Any] = {
        "library": "bar",
        "display": {"x": "day", "y": "count", "color": "source"},
    }
    result = convert_chart_type(chart)
    encoding = result["display"]["encoding"]
    assert encoding["color"] == {"field": "source", "type": "nominal"}
    assert encoding["opacity"] == {
        "condition": {"param": "highlight", "value": 1},
        "value": 0.2,
    }
    assert result["display"]["params"] == [
        {
            "name": "highlight",
            "select": {
                "type": "point",
                "fields": ["source"],
                "on": "mouseover",
            },
            "bind": "legend",
        }
    ]


def test_bar_without_color_no_highlight() -> None:
    chart: dict[str, t.Any] = {
        "library": "bar",
        "display": {"x": "source", "y": "count"},
    }
    result = convert_chart_type(chart)
    assert "params" not in result["display"]
    assert "opacity" not in result["display"]["encoding"]


# --- scatter chart ---


def test_scatter_simple_fields() -> None:
    chart: dict[str, t.Any] = {
        "library": "scatter",
        "display": {"x": "price", "y": "rating"},
    }
    result = convert_chart_type(chart)
    assert result["library"] == "vega-lite"
    assert result["display"] == {
        "mark": {"type": "point", "tooltip": True},
        "encoding": {
            "x": {"field": "price", "type": "quantitative"},
            "y": {"field": "rating", "type": "quantitative"},
        },
    }


def test_scatter_with_color() -> None:
    chart: dict[str, t.Any] = {
        "library": "scatter",
        "display": {"x": "price", "y": "rating", "color": "category"},
    }
    result = convert_chart_type(chart)
    encoding = result["display"]["encoding"]
    assert encoding["color"] == {"field": "category", "type": "nominal"}
    assert encoding["opacity"] == {
        "condition": {"param": "highlight", "value": 1},
        "value": 0.2,
    }
    assert result["display"]["params"] == [
        {
            "name": "highlight",
            "select": {
                "type": "point",
                "fields": ["category"],
                "on": "mouseover",
            },
            "bind": "legend",
        }
    ]


def test_scatter_without_color_no_highlight() -> None:
    chart: dict[str, t.Any] = {
        "library": "scatter",
        "display": {"x": "price", "y": "rating"},
    }
    result = convert_chart_type(chart)
    assert "params" not in result["display"]
    assert "opacity" not in result["display"]["encoding"]


def test_scatter_with_size() -> None:
    chart: dict[str, t.Any] = {
        "library": "scatter",
        "display": {"x": "price", "y": "rating", "size": "volume"},
    }
    result = convert_chart_type(chart)
    encoding = result["display"]["encoding"]
    assert encoding["size"] == {"field": "volume", "type": "quantitative"}


def test_scatter_with_color_and_size() -> None:
    chart: dict[str, t.Any] = {
        "library": "scatter",
        "display": {
            "x": "price",
            "y": "rating",
            "color": "category",
            "size": "volume",
        },
    }
    result = convert_chart_type(chart)
    encoding = result["display"]["encoding"]
    assert encoding["color"] == {"field": "category", "type": "nominal"}
    assert encoding["size"] == {"field": "volume", "type": "quantitative"}


# --- pie chart ---


def test_pie_simple_fields() -> None:
    chart: dict[str, t.Any] = {
        "library": "pie",
        "display": {"label": "source", "value": "count"},
    }
    result = convert_chart_type(chart)
    assert result["library"] == "vega-lite"
    assert result["display"] == {
        "mark": {"type": "arc", "tooltip": True},
        "params": [
            {
                "name": "highlight",
                "select": {
                    "type": "point",
                    "fields": ["source"],
                    "on": "mouseover",
                },
                "bind": "legend",
            }
        ],
        "encoding": {
            "color": {"field": "source", "type": "nominal"},
            "theta": {"field": "count", "type": "quantitative"},
            "opacity": {
                "condition": {"param": "highlight", "value": 1},
                "value": 0.2,
            },
        },
    }


def test_pie_dict_field_spec() -> None:
    chart: dict[str, t.Any] = {
        "library": "pie",
        "display": {
            "label": {"field": "source", "type": "ordinal"},
            "value": "count",
        },
    }
    result = convert_chart_type(chart)
    encoding = result["display"]["encoding"]
    assert encoding["color"] == {"field": "source", "type": "ordinal"}


# --- choropleth chart ---


def test_choropleth_simple_fields() -> None:
    chart: dict[str, t.Any] = {
        "library": "choropleth",
        "display": {
            "label": "name",
            "value": "count",
            "geodata_url": "https://example.com/geo.json",
            "geodata_key": "properties.name",
        },
    }
    result = convert_chart_type(chart)
    assert result["library"] == "vega-lite"
    assert result["display"]["mark"] == "geoshape"
    assert result["display"]["projection"] == {"type": "mercator"}
    assert result["display"]["encoding"]["fill"] == {
        "field": "count",
        "type": "quantitative",
        "scale": {"scheme": "blues"},
    }
    assert result["display"]["encoding"]["stroke"] == {"value": "white"}
    assert result["display"]["encoding"]["tooltip"] == [
        {"field": "name", "type": "nominal"},
        {"field": "count", "type": "quantitative"},
    ]


def test_choropleth_transform_lookup() -> None:
    chart: dict[str, t.Any] = {
        "library": "choropleth",
        "display": {
            "label": "name",
            "value": "count",
            "geodata_url": "https://example.com/geo.json",
            "geodata_key": "properties.name",
        },
    }
    result = convert_chart_type(chart)
    transform = result["display"]["transform"]
    assert len(transform) == 1
    assert transform[0]["lookup"] == "name"
    assert transform[0]["from"]["data"]["url"] == "https://example.com/geo.json"
    assert transform[0]["from"]["key"] == "properties.name"
    assert transform[0]["from"]["fields"] == ["type", "geometry"]


def test_choropleth_custom_projection() -> None:
    chart: dict[str, t.Any] = {
        "library": "choropleth",
        "display": {
            "label": "name",
            "value": "count",
            "geodata_url": "https://example.com/geo.json",
            "geodata_key": "properties.name",
            "projection": "equalEarth",
        },
    }
    result = convert_chart_type(chart)
    assert result["display"]["projection"] == {"type": "equalEarth"}


def test_choropleth_custom_color_scheme() -> None:
    chart: dict[str, t.Any] = {
        "library": "choropleth",
        "display": {
            "label": "name",
            "value": "count",
            "geodata_url": "https://example.com/geo.json",
            "geodata_key": "properties.name",
            "color_scheme": "reds",
        },
    }
    result = convert_chart_type(chart)
    assert result["display"]["encoding"]["fill"]["scale"] == {"scheme": "reds"}


def test_choropleth_dict_field_spec() -> None:
    chart: dict[str, t.Any] = {
        "library": "choropleth",
        "display": {
            "label": {"field": "name", "type": "ordinal"},
            "value": "count",
            "geodata_url": "https://example.com/geo.json",
            "geodata_key": "properties.name",
        },
    }
    result = convert_chart_type(chart)
    assert result["display"]["encoding"]["tooltip"][0] == {
        "field": "name",
        "type": "ordinal",
    }


# --- wordcloud chart ---


def test_wordcloud_simple_fields() -> None:
    chart: dict[str, t.Any] = {
        "library": "wordcloud",
        "display": {"text": "word", "size": "frequency"},
    }
    result = convert_chart_type(chart)
    assert result["library"] == "vega"
    assert len(result["display"]["scales"]) == 1
    assert result["display"]["scales"][0]["name"] == "color"
    assert result["display"]["scales"][0]["domain"] == {
        "data": "table",
        "field": "word",
    }


def test_wordcloud_marks_structure() -> None:
    chart: dict[str, t.Any] = {
        "library": "wordcloud",
        "display": {"text": "word", "size": "frequency"},
    }
    result = convert_chart_type(chart)
    marks = result["display"]["marks"]
    assert len(marks) == 1
    mark = marks[0]
    assert mark["type"] == "text"
    assert mark["from"] == {"data": "table"}
    assert mark["encode"]["enter"]["text"] == {"field": "word"}
    assert mark["encode"]["enter"]["fill"] == {"scale": "color", "field": "word"}


def test_wordcloud_transform() -> None:
    chart: dict[str, t.Any] = {
        "library": "wordcloud",
        "display": {"text": "word", "size": "frequency"},
    }
    result = convert_chart_type(chart)
    transform = result["display"]["marks"][0]["transform"][0]
    assert transform["type"] == "wordcloud"
    assert transform["text"] == {"field": "word"}
    assert transform["fontSize"] == {"field": "datum.frequency"}
    assert transform["rotate"] == 0
    assert transform["fontSizeRange"] == [12, 56]


def test_wordcloud_custom_colors() -> None:
    chart: dict[str, t.Any] = {
        "library": "wordcloud",
        "display": {
            "text": "word",
            "size": "frequency",
            "colors": ["#ff0000", "#00ff00"],
        },
    }
    result = convert_chart_type(chart)
    assert result["display"]["scales"][0]["range"] == ["#ff0000", "#00ff00"]


def test_wordcloud_custom_font() -> None:
    chart: dict[str, t.Any] = {
        "library": "wordcloud",
        "display": {
            "text": "word",
            "size": "frequency",
            "font": "Georgia",
        },
    }
    result = convert_chart_type(chart)
    transform = result["display"]["marks"][0]["transform"][0]
    assert transform["font"] == "Georgia"


def test_wordcloud_custom_rotate() -> None:
    chart: dict[str, t.Any] = {
        "library": "wordcloud",
        "display": {
            "text": "word",
            "size": "frequency",
            "rotate": 45,
        },
    }
    result = convert_chart_type(chart)
    transform = result["display"]["marks"][0]["transform"][0]
    assert transform["rotate"] == 45


def test_wordcloud_custom_font_size_range() -> None:
    chart: dict[str, t.Any] = {
        "library": "wordcloud",
        "display": {
            "text": "word",
            "size": "frequency",
            "font_size_range": [8, 72],
        },
    }
    result = convert_chart_type(chart)
    transform = result["display"]["marks"][0]["transform"][0]
    assert transform["fontSizeRange"] == [8, 72]


def test_wordcloud_default_height() -> None:
    chart: dict[str, t.Any] = {
        "library": "wordcloud",
        "display": {"text": "word", "size": "frequency"},
    }
    result = convert_chart_type(chart)
    assert result["display"]["height"] == 200


def test_wordcloud_custom_height() -> None:
    chart: dict[str, t.Any] = {
        "library": "wordcloud",
        "display": {"text": "word", "size": "frequency", "height": 300},
    }
    result = convert_chart_type(chart)
    assert result["display"]["height"] == 300


# --- CHART_TYPES registry ---


def test_all_chart_types_present() -> None:
    assert CHART_TYPES == {
        "line",
        "bar",
        "area",
        "scatter",
        "pie",
        "choropleth",
        "wordcloud",
    }
