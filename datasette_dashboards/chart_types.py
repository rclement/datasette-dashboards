import copy
import typing as t

CHART_TYPES = {"line", "bar", "area", "scatter", "pie", "choropleth", "wordcloud"}

# Default field types per chart type for x and y axes
_DEFAULT_TYPES: dict[str, dict[str, str]] = {
    "line": {"x": "temporal", "y": "quantitative"},
    "area": {"x": "temporal", "y": "quantitative"},
    "bar": {"x": "nominal", "y": "quantitative"},
    "scatter": {"x": "quantitative", "y": "quantitative"},
}


def _normalize_field(
    value: t.Union[str, dict[str, t.Any]], default_type: str
) -> dict[str, t.Any]:
    """Normalize a field spec to a Vega-Lite encoding channel definition.

    Accepts either:
      - A string (field name): "day" -> {"field": "day", "type": default_type}
      - A dict with at least "field": {"field": "day", "type": "temporal"}

    Any extra keys in a dict value are passed through to the encoding.
    """
    if isinstance(value, str):
        return {"field": value, "type": default_type}

    if "field" not in value:
        raise ValueError(
            f"Field specification dict must include a 'field' key; got: {value!r}"
        )

    result = dict(value)
    result.setdefault("type", default_type)
    return result


def _apply_color_highlight(
    display: dict[str, t.Any],
    encoding: dict[str, t.Any],
    result: dict[str, t.Any],
) -> None:
    """If a color field is present, add it to encoding and attach interactive legend highlighting."""
    if "color" not in display:
        return
    color_spec = _normalize_field(display["color"], "nominal")
    encoding["color"] = color_spec
    result["params"] = [
        {
            "name": "highlight",
            "select": {
                "type": "point",
                "fields": [color_spec["field"]],
                "on": "mouseover",
            },
            "bind": "legend",
        }
    ]
    encoding["opacity"] = {
        "condition": {"param": "highlight", "value": 1},
        "value": 0.2,
    }


def _convert_line(display: dict[str, t.Any]) -> dict[str, t.Any]:
    """Convert a high-level line chart spec to Vega-Lite.

    When a color field is present, adds interactive legend highlighting.
    """
    defaults = _DEFAULT_TYPES["line"]
    x = _normalize_field(display["x"], display.get("xtype", defaults["x"]))
    y = _normalize_field(display["y"], display.get("ytype", defaults["y"]))

    encoding: dict[str, t.Any] = {"x": x, "y": y}
    result: dict[str, t.Any] = {
        "mark": {"type": "line", "tooltip": True},
    }

    _apply_color_highlight(display, encoding, result)
    result["encoding"] = encoding
    return result


def _convert_area(display: dict[str, t.Any]) -> dict[str, t.Any]:
    """Convert a high-level area chart spec to Vega-Lite.

    When a color field is present, adds interactive legend highlighting.
    """
    defaults = _DEFAULT_TYPES["area"]
    x = _normalize_field(display["x"], display.get("xtype", defaults["x"]))
    y = _normalize_field(display["y"], display.get("ytype", defaults["y"]))

    encoding: dict[str, t.Any] = {"x": x, "y": y}
    result: dict[str, t.Any] = {
        "mark": {"type": "area", "tooltip": True},
    }

    _apply_color_highlight(display, encoding, result)
    result["encoding"] = encoding
    return result


def _convert_bar(display: dict[str, t.Any]) -> dict[str, t.Any]:
    """Convert a high-level bar chart spec to Vega-Lite.

    Supports `horizontal: true` to flip axes.
    When a color field is present, adds interactive legend highlighting.
    """
    defaults = _DEFAULT_TYPES["bar"]
    horizontal = display.get("horizontal", False)

    if horizontal:
        x = _normalize_field(display["y"], display.get("ytype", defaults["y"]))
        y = _normalize_field(display["x"], display.get("xtype", defaults["x"]))
    else:
        x = _normalize_field(display["x"], display.get("xtype", defaults["x"]))
        y = _normalize_field(display["y"], display.get("ytype", defaults["y"]))

    encoding: dict[str, t.Any] = {"x": x, "y": y}
    result: dict[str, t.Any] = {
        "mark": {"type": "bar", "tooltip": True},
    }

    _apply_color_highlight(display, encoding, result)
    result["encoding"] = encoding
    return result


def _convert_scatter(display: dict[str, t.Any]) -> dict[str, t.Any]:
    """Convert a high-level scatter chart spec to Vega-Lite.

    When a color field is present, adds interactive legend highlighting.
    """
    defaults = _DEFAULT_TYPES["scatter"]
    x = _normalize_field(display["x"], display.get("xtype", defaults["x"]))
    y = _normalize_field(display["y"], display.get("ytype", defaults["y"]))

    encoding: dict[str, t.Any] = {"x": x, "y": y}
    result: dict[str, t.Any] = {
        "mark": {"type": "point", "tooltip": True},
    }

    _apply_color_highlight(display, encoding, result)
    if "size" in display:
        encoding["size"] = _normalize_field(display["size"], "quantitative")

    result["encoding"] = encoding
    return result


def _convert_pie(display: dict[str, t.Any]) -> dict[str, t.Any]:
    """Convert a high-level pie chart spec to Vega-Lite.

    Includes interactive legend highlighting by default.
    """
    color = _normalize_field(display["label"], "nominal")
    theta = _normalize_field(display["value"], "quantitative")

    return {
        "mark": {"type": "arc", "tooltip": True},
        "params": [
            {
                "name": "highlight",
                "select": {
                    "type": "point",
                    "fields": [color["field"]],
                    "on": "mouseover",
                },
                "bind": "legend",
            }
        ],
        "encoding": {
            "color": color,
            "theta": theta,
            "opacity": {
                "condition": {"param": "highlight", "value": 1},
                "value": 0.2,
            },
        },
    }


def _convert_choropleth(display: dict[str, t.Any]) -> dict[str, t.Any]:
    """Convert a high-level choropleth chart spec to Vega-Lite.

    Required display keys:
      - label: field name containing geographic feature labels (matched against geodata)
      - value: field name containing the numeric value for coloring
      - geodata_url: URL to a GeoJSON file
      - geodata_key: property path in GeoJSON to match on (e.g. "properties.nom")

    Optional:
      - projection: projection type (default "mercator")
      - color_scheme: Vega color scheme name (default "blues")
    """
    label = display["label"]
    value = display["value"]
    geodata_url = display["geodata_url"]
    geodata_key = display["geodata_key"]
    projection = display.get("projection", "mercator")
    color_scheme = display.get("color_scheme", "blues")

    label_field = _normalize_field(label, "nominal")
    value_field = _normalize_field(value, "quantitative")

    return {
        "mark": "geoshape",
        "projection": {"type": projection},
        "transform": [
            {
                "lookup": label_field["field"],
                "from": {
                    "data": {
                        "url": geodata_url,
                        "format": {"type": "json", "property": "features"},
                    },
                    "key": geodata_key,
                    "fields": ["type", "geometry"],
                },
            }
        ],
        "encoding": {
            "fill": {
                **value_field,
                "scale": {"scheme": color_scheme},
            },
            "stroke": {"value": "white"},
            "tooltip": [
                label_field,
                value_field,
            ],
        },
    }


def _convert_wordcloud(display: dict[str, t.Any]) -> dict[str, t.Any]:
    """Convert a high-level word-cloud spec to a Vega spec.

    Required display keys:
      - text: field name containing words
      - size: field name containing word frequency / size value

    Optional:
      - colors: list of color hex strings (default: ["#d5a928", "#652c90", "#939597"])
      - font: font family (default: "Helvetica Neue, Arial")
      - rotate: rotation angle in degrees (default: 0)
      - font_size_range: [min, max] font size range (default: [12, 56])
    """
    text_field = display["text"]
    size_field = display["size"]
    colors = display.get("colors", ["#d5a928", "#652c90", "#939597"])
    font = display.get("font", "Helvetica Neue, Arial")
    rotate = display.get("rotate", 0)
    font_size_range = display.get("font_size_range", [12, 56])
    height = display.get("height", 200)

    return {
        "height": height,
        "scales": [
            {
                "name": "color",
                "type": "ordinal",
                "domain": {"data": "table", "field": text_field},
                "range": colors,
            }
        ],
        "marks": [
            {
                "type": "text",
                "from": {"data": "table"},
                "encode": {
                    "enter": {
                        "text": {"field": text_field},
                        "align": {"value": "center"},
                        "baseline": {"value": "alphabetic"},
                        "fill": {"scale": "color", "field": text_field},
                    },
                    "update": {"fillOpacity": {"value": 1}},
                    "hover": {"fillOpacity": {"value": 0.5}},
                },
                "transform": [
                    {
                        "type": "wordcloud",
                        "size": [{"signal": "width"}, {"signal": "height"}],
                        "text": {"field": text_field},
                        "rotate": rotate,
                        "font": font,
                        "fontSize": {"field": f"datum.{size_field}"},
                        "fontWeight": "300",
                        "fontSizeRange": font_size_range,
                        "padding": 2,
                    }
                ],
            }
        ],
    }


_CONVERTERS: dict[str, t.Callable[[dict[str, t.Any]], dict[str, t.Any]]] = {
    "line": _convert_line,
    "area": _convert_area,
    "bar": _convert_bar,
    "scatter": _convert_scatter,
    "pie": _convert_pie,
    "choropleth": _convert_choropleth,
    "wordcloud": _convert_wordcloud,
}

# Chart types that convert to raw Vega instead of Vega-Lite
_VEGA_TARGETS: set[str] = {"wordcloud"}


def convert_chart_type(chart: dict[str, t.Any]) -> dict[str, t.Any]:
    """Convert a high-level chart spec to a Vega or Vega-Lite chart spec.

    If the chart's library is a known chart type, converts the display spec
    and sets library to "vega-lite" (or "vega" for wordcloud).

    Returns a new dict (does not mutate the original).
    If the chart library is not a known chart type, returns the original unchanged.
    """
    library = chart.get("library", "")
    if library not in CHART_TYPES:
        return chart

    converter = _CONVERTERS[library]
    display = chart.get("display", {})
    converted_display = converter(display)

    result = copy.copy(chart)
    result["library"] = "vega" if library in _VEGA_TARGETS else "vega-lite"
    result["display"] = converted_display
    return result
