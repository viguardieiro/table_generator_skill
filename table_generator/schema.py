"""Spec validation and defaults."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


class SchemaError(ValueError):
    """Raised when the spec schema is invalid."""


DEFAULTS = {
    "format": {
        "mode": "pm",
        "mean_decimals": 2,
        "unc_decimals": 2,
        "trailing_zeros": True,
        "scientific": False,
        "missing": "--",
    },
    "output": {
        "format": "latex",
        "markdown": {
            "include_caption": True,
            "alignment": "auto",
            "separator": "|",
            "bold": "**",
            "underline": "_",
        },
    },
    "latex": {
        "environment": True,
        "booktabs": True,
        "tabular": "tabular",
        "alignment": None,
        "caption": None,
        "label": None,
        "escape": True,
        "resize": None,
    },
}


VALID_FORMATS = {"latex", "markdown"}
VALID_FORMAT_MODES = {"pm", "ci_brackets"}
VALID_STATS = {"mean", "median"}
VALID_UNCERTAINTY = {"none", "std", "sem", "ci"}
VALID_CI_METHODS = {"bootstrap_percentile"}
VALID_DIRECTION = {"min", "max"}
VALID_HIGHLIGHT_SCOPE = {"column", "row", "table"}
VALID_HIGHLIGHT_STYLE = {"bold", "underline"}
VALID_TIES = {"all", "first"}


def _path_err(path: str, message: str) -> SchemaError:
    return SchemaError(f"{message} (path: {path})")


def _merge_defaults(spec: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(spec)
    for key, default_block in DEFAULTS.items():
        if key not in merged or merged[key] is None:
            merged[key] = deepcopy(default_block)
        else:
            for subkey, value in default_block.items():
                merged[key].setdefault(subkey, deepcopy(value))
    return merged


def validate_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(spec, dict):
        raise _path_err("spec", "Spec must be a dict")

    merged = _merge_defaults(spec)

    for required in ("rows", "cols", "metric", "aggregate"):
        if required not in merged:
            raise _path_err(f"spec.{required}", "Missing required block")

    # Rows/cols
    for axis in ("rows", "cols"):
        block = merged[axis]
        if not isinstance(block, dict):
            raise _path_err(f"spec.{axis}", "Must be an object")
        if "field" not in block:
            raise _path_err(f"spec.{axis}.field", "Missing required field")

    # Metric
    metric = merged["metric"]
    if "field" not in metric:
        raise _path_err("spec.metric.field", "Missing required field")
    if "value" not in metric:
        raise _path_err("spec.metric.value", "Missing required field")
    if metric.get("direction") not in VALID_DIRECTION:
        raise _path_err("spec.metric.direction", "Must be 'min' or 'max'")

    # Aggregate
    agg = merged["aggregate"]
    if "over" not in agg or not isinstance(agg["over"], list) or not agg["over"]:
        raise _path_err("spec.aggregate.over", "Must be a non-empty list")
    stat = agg.get("stat", "mean")
    if stat not in VALID_STATS:
        raise _path_err("spec.aggregate.stat", "Unsupported stat")

    unc = agg.get("uncertainty", {"type": "none"})
    if not isinstance(unc, dict):
        raise _path_err("spec.aggregate.uncertainty", "Must be an object")
    unc_type = unc.get("type", "none")
    if unc_type not in VALID_UNCERTAINTY:
        raise _path_err("spec.aggregate.uncertainty.type", "Unsupported uncertainty type")
    if unc_type == "ci":
        if unc.get("method", "bootstrap_percentile") not in VALID_CI_METHODS:
            raise _path_err("spec.aggregate.uncertainty.method", "Unsupported CI method")
        level = unc.get("level", 0.95)
        if not (0 < level < 1):
            raise _path_err("spec.aggregate.uncertainty.level", "CI level must be between 0 and 1")
        n_boot = unc.get("n_boot", 1000)
        if not isinstance(n_boot, int) or n_boot <= 0:
            raise _path_err("spec.aggregate.uncertainty.n_boot", "n_boot must be a positive int")

    # Format
    fmt = merged.get("format", {})
    if fmt.get("mode") not in VALID_FORMAT_MODES:
        raise _path_err("spec.format.mode", "Unsupported format mode")

    # Output
    output = merged.get("output", {})
    if output.get("format") not in VALID_FORMATS:
        raise _path_err("spec.output.format", "Unsupported output format")

    # Highlight
    highlight = merged.get("highlight")
    if highlight is not None:
        if not isinstance(highlight, dict):
            raise _path_err("spec.highlight", "Must be an object")
        scope = highlight.get("scope", "column")
        if scope not in VALID_HIGHLIGHT_SCOPE:
            raise _path_err("spec.highlight.scope", "Unsupported scope")
        ties = highlight.get("ties", "all")
        if ties not in VALID_TIES:
            raise _path_err("spec.highlight.ties", "Unsupported ties mode")
        for key in ("best", "second"):
            if key in highlight:
                style = highlight[key].get("style")
                if style is None:
                    continue
                if style.startswith("cellcolor:"):
                    continue
                if style not in VALID_HIGHLIGHT_STYLE:
                    raise _path_err(f"spec.highlight.{key}.style", "Unsupported style")

    # Ranking (not implemented)
    ranking = merged.get("ranking")
    if ranking and ranking.get("enabled"):
        raise _path_err("spec.ranking", "Ranking is not implemented yet")

    return merged
