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
VALID_TIES = {"all", "first", "none"}


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
        groups = block.get("groups")
        if groups is not None:
            if not isinstance(groups, list):
                raise _path_err(f"spec.{axis}.groups", "Must be a list")
            for idx, group in enumerate(groups):
                if not isinstance(group, dict):
                    raise _path_err(f"spec.{axis}.groups[{idx}]", "Must be an object")
                if "label" not in group:
                    raise _path_err(f"spec.{axis}.groups[{idx}].label", "Missing required field")
                if "members" not in group or not isinstance(group["members"], list) or not group["members"]:
                    raise _path_err(
                        f"spec.{axis}.groups[{idx}].members", "Must be a non-empty list"
                    )
                if axis == "rows":
                    sep = group.get("separator")
                    if sep is not None and sep not in ("midrule", "hline", "none"):
                        raise _path_err(
                            f"spec.{axis}.groups[{idx}].separator",
                            "Unsupported separator",
                        )
                if axis == "cols":
                    cmid = group.get("cmidrule")
                    if cmid is not None and not isinstance(cmid, bool):
                        raise _path_err(
                            f"spec.{axis}.groups[{idx}].cmidrule",
                            "Must be true or false",
                        )

    # Metric
    metric = merged["metric"]
    if "field" not in metric:
        raise _path_err("spec.metric.field", "Missing required field")
    if "value" not in metric:
        raise _path_err("spec.metric.value", "Missing required field")
    direction = metric.get("direction")
    if isinstance(direction, str):
        if direction not in VALID_DIRECTION:
            raise _path_err("spec.metric.direction", "Must be 'min' or 'max'")
    elif isinstance(direction, dict):
        for key, value in direction.items():
            if value not in VALID_DIRECTION:
                raise _path_err(
                    f"spec.metric.direction.{key}", "Must be 'min' or 'max'"
                )
    else:
        raise _path_err("spec.metric.direction", "Must be 'min'/'max' or a map")

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

    # Summary rows/cols
    for key in ("row_summary", "col_summary"):
        summary = agg.get(key)
        if summary is not None:
            if not isinstance(summary, dict):
                raise _path_err(f"spec.aggregate.{key}", "Must be an object")
            if "label" not in summary:
                raise _path_err(f"spec.aggregate.{key}.label", "Missing required field")
            stat = summary.get("stat", "mean")
            if stat not in VALID_STATS:
                raise _path_err(f"spec.aggregate.{key}.stat", "Unsupported stat")
            position = summary.get("position")
            if position is not None and position not in ("start", "end"):
                raise _path_err(f"spec.aggregate.{key}.position", "Must be 'start' or 'end'")

    # Format
    fmt = merged.get("format", {})
    if fmt.get("mode") not in VALID_FORMAT_MODES:
        raise _path_err("spec.format.mode", "Unsupported format mode")
    overrides = fmt.get("overrides")
    if overrides is not None:
        if not isinstance(overrides, dict):
            raise _path_err("spec.format.overrides", "Must be an object")
        for key, value in overrides.items():
            if not isinstance(value, dict):
                raise _path_err(f"spec.format.overrides.{key}", "Must be an object")

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

    # Row ordering by performance (optional)
    rows = merged.get("rows", {})
    order_by = rows.get("order_by")
    if order_by is not None:
        if not isinstance(order_by, dict):
            raise _path_err("spec.rows.order_by", "Must be an object")
        if "column" not in order_by:
            raise _path_err("spec.rows.order_by.column", "Missing required field")
        direction = order_by.get("direction")
        if direction is not None and direction not in VALID_DIRECTION:
            raise _path_err("spec.rows.order_by.direction", "Must be 'min' or 'max'")

    # LaTeX footnotes
    latex = merged.get("latex", {})
    footnotes = latex.get("footnotes")
    if footnotes is not None:
        if not isinstance(footnotes, list):
            raise _path_err("spec.latex.footnotes", "Must be a list of strings")
        for idx, note in enumerate(footnotes):
            if not isinstance(note, str):
                raise _path_err(f"spec.latex.footnotes[{idx}]", "Must be a string")

    # Significance markers
    sig = merged.get("significance")
    if sig is not None:
        if not isinstance(sig, dict):
            raise _path_err("spec.significance", "Must be an object")
        if "baseline" not in sig:
            raise _path_err("spec.significance.baseline", "Missing required field")
        scope = sig.get("scope", "column")
        if scope not in ("column",):
            raise _path_err("spec.significance.scope", "Only 'column' is supported")
        method = sig.get("method", "bootstrap_ci")
        if method not in ("bootstrap_ci",):
            raise _path_err("spec.significance.method", "Only 'bootstrap_ci' is supported")
        level = sig.get("level", 0.95)
        if not (0 < level < 1):
            raise _path_err("spec.significance.level", "level must be between 0 and 1")
        n_boot = sig.get("n_boot", 1000)
        if not isinstance(n_boot, int) or n_boot <= 0:
            raise _path_err("spec.significance.n_boot", "n_boot must be a positive int")

    # Delta vs baseline columns
    delta = merged.get("delta")
    if delta is not None:
        if not isinstance(delta, dict):
            raise _path_err("spec.delta", "Must be an object")
        if "baseline" not in delta:
            raise _path_err("spec.delta.baseline", "Missing required field")
        mode = delta.get("mode", "absolute")
        if mode not in ("absolute", "relative"):
            raise _path_err("spec.delta.mode", "Must be 'absolute' or 'relative'")
        position = delta.get("position", "after")
        if position not in ("after", "end"):
            raise _path_err("spec.delta.position", "Must be 'after' or 'end'")
        if "columns" in delta and not isinstance(delta["columns"], list):
            raise _path_err("spec.delta.columns", "Must be a list of column labels")
        fmt = delta.get("format")
        if fmt is not None and not isinstance(fmt, dict):
            raise _path_err("spec.delta.format", "Must be an object")

    return merged
