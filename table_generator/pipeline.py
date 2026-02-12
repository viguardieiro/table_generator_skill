"""Main pipeline for rendering tables."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .render_latex import render_latex
from .render_markdown import render_markdown
from .stats import bootstrap_diff_ci, bootstrap_percentile, mean, median, sem, std


def build_table(records: List[Dict[str, Any]], spec: Dict[str, Any]) -> Dict[str, Any]:
    return _aggregate(records, spec)


def compute_highlights(table: Dict[str, Any], spec: Dict[str, Any]) -> Dict[Tuple[Any, Any], str]:
    return _compute_highlights(table, spec)


def render_pipeline(records: List[Dict[str, Any]], spec: Dict[str, Any]) -> Dict[str, Any]:
    table = build_table(records, spec)
    highlights = compute_highlights(table, spec)
    markers = compute_significance(table, spec)
    if spec["output"]["format"] == "latex":
        text, preamble = render_latex(table, highlights, spec, markers)
    else:
        text = render_markdown(table, highlights, spec, markers)
        preamble = []

    return {
        "format": spec["output"]["format"],
        "text": text,
        "preamble": preamble,
        "meta": {
            "rows": len(table["rows"]),
            "cols": len(table["cols"]),
            "metric": spec["metric"]["value"],
            "uncertainty": spec["aggregate"].get("uncertainty", {}).get("type", "none"),
        },
    }


def _apply_rename(value: Any, rename_map: Dict[str, str]) -> Any:
    if rename_map is None:
        return value
    return rename_map.get(value, value)


def _ordered_unique(items: List[Any]) -> List[Any]:
    seen = set()
    ordered = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _resolve_order(values: List[Any], order: List[Any] | None) -> List[Any]:
    values = _ordered_unique(values)
    if not order:
        return values
    ordered = []
    remaining = [v for v in values if v not in order]
    for v in order:
        if v in values:
            ordered.append(v)
    ordered.extend(remaining)
    return ordered


def _aggregate(records: List[Dict[str, Any]], spec: Dict[str, Any]) -> Dict[str, Any]:
    rows_spec = spec["rows"]
    cols_spec = spec["cols"]
    metric_spec = spec["metric"]
    agg_spec = spec["aggregate"]

    row_field = rows_spec["field"]
    col_field = cols_spec["field"]
    metric_field = metric_spec["field"]
    metric_value = metric_spec["value"]

    row_rename = rows_spec.get("rename", {})
    col_rename = cols_spec.get("rename", {})

    filtered = []
    for rec in records:
        if metric_field not in rec:
            raise ValueError(f"Missing metric field '{metric_field}' in record")
        if rec[metric_field] != metric_value:
            continue
        if row_field not in rec or col_field not in rec:
            raise ValueError("Record missing row/col field")
        rec = dict(rec)
        rec[row_field] = _apply_rename(rec[row_field], row_rename)
        rec[col_field] = _apply_rename(rec[col_field], col_rename)
        filtered.append(rec)

    row_values = [rec[row_field] for rec in filtered]
    col_values = [rec[col_field] for rec in filtered]

    rows = _resolve_order(row_values, rows_spec.get("order"))
    cols = _resolve_order(col_values, cols_spec.get("order"))

    over_fields = agg_spec["over"]
    stat = agg_spec.get("stat", "mean")
    unc_spec = agg_spec.get("uncertainty", {"type": "none"})
    unc_type = unc_spec.get("type", "none")

    stat_fn = mean if stat == "mean" else median

    grouped: Dict[Tuple[Any, Any], List[float]] = {}
    for rec in filtered:
        key = (rec[row_field], rec[col_field])
        if "value" not in rec:
            raise ValueError("Record missing 'value'")
        grouped.setdefault(key, []).append(float(rec["value"]))

    cells: Dict[Tuple[Any, Any], Dict[str, Any]] = {}
    for key, values in grouped.items():
        center = stat_fn(values)
        cell = {"center": center, "n": len(values), "unc": None, "ci": None, "values": values}
        if unc_type == "std":
            cell["unc"] = std(values)
        elif unc_type == "sem":
            cell["unc"] = sem(values)
        elif unc_type == "ci":
            level = unc_spec.get("level", 0.95)
            n_boot = unc_spec.get("n_boot", 1000)
            seed = unc_spec.get("seed", 0)
            lo, hi = bootstrap_percentile(values, stat_fn, level, n_boot, seed)
            cell["ci"] = (lo, hi)
        cells[key] = cell

    table = {
        "rows": rows,
        "cols": cols,
        "cells": cells,
        "row_field": row_field,
        "col_field": col_field,
    }
    table["rows"] = _apply_row_order_by(table, spec)
    _validate_groups(table["rows"], rows_spec.get("groups"), axis="rows")
    _validate_groups(table["cols"], cols_spec.get("groups"), axis="cols")
    _apply_summaries(table, spec)
    return table


def _direction_for_column(spec: Dict[str, Any], column: Any) -> str:
    direction = spec["metric"]["direction"]
    if isinstance(direction, dict):
        if column in direction:
            return direction[column]
        raise ValueError(f"Missing direction for column '{column}'")
    return direction


def _apply_row_order_by(table: Dict[str, Any], spec: Dict[str, Any]) -> List[Any]:
    rows_spec = spec.get("rows", {})
    order_by = rows_spec.get("order_by")
    if not order_by:
        return table["rows"]

    column = order_by["column"]
    direction = order_by.get("direction") or _direction_for_column(spec, column)
    cells = table["cells"]

    def key_fn(row: Any) -> Tuple[int, float]:
        cell = cells.get((row, column))
        if cell is None:
            return (1, 0.0)
        return (0, cell["center"])

    reverse = direction == "max"
    return sorted(table["rows"], key=key_fn, reverse=reverse)


def _validate_groups(items: List[Any], groups: Any, axis: str) -> None:
    if not groups:
        return
    seen = set()
    for group in groups:
        for member in group.get("members", []):
            if member in seen:
                raise ValueError(f"{axis} group member '{member}' appears in multiple groups")
            seen.add(member)
    # Validate members exist in final order
    missing = [m for m in seen if m not in items]
    if missing:
        raise ValueError(f"{axis} group members missing from {axis} order: {missing}")

    # Ensure each group's members are contiguous in final order
    index = {value: idx for idx, value in enumerate(items)}
    for group in groups:
        members = [m for m in group.get("members", []) if m in index]
        if not members:
            raise ValueError(f"{axis} group '{group.get('label')}' has no valid members")
        positions = sorted(index[m] for m in members)
        if positions != list(range(min(positions), max(positions) + 1)):
            raise ValueError(
                f"{axis} group '{group.get('label')}' members are not contiguous in {axis} order"
            )


def _compute_highlights(table: Dict[str, Any], spec: Dict[str, Any]) -> Dict[Tuple[Any, Any], str]:
    highlight = spec.get("highlight")
    if not highlight:
        return {}

    scope = highlight.get("scope", "column")
    direction = spec["metric"]["direction"]
    ties = highlight.get("ties", "all")

    def sorted_items(items: List[Tuple[Any, Any, float]], dir_value: str) -> List[Tuple[Any, Any, float]]:
        reverse = dir_value == "max"
        return sorted(items, key=lambda x: x[2], reverse=reverse)

    cells = table["cells"]
    rows = table["rows"]
    cols = table["cols"]
    summary_rows = set(table.get("summary_rows", []))
    summary_cols = set(table.get("summary_cols", []))
    summary_rows = set(table.get("summary_rows", []))
    summary_cols = set(table.get("summary_cols", []))
    summary_rows = set(table.get("summary_rows", []))
    summary_cols = set(table.get("summary_cols", []))

    highlights: Dict[Tuple[Any, Any], str] = {}

    def apply_group(items: List[Tuple[Any, Any, float]], dir_value: str):
        if not items:
            return
        ordered = sorted_items(items, dir_value)
        best_val = ordered[0][2]
        best_items = [x for x in ordered if x[2] == best_val]
        if ties == "first":
            best_items = best_items[:1]
        if ties == "none" and len(best_items) > 1:
            return
        for r, c, _ in best_items:
            highlights[(r, c)] = "best"

        if ties == "all" and len(best_items) > 1:
            return

        second_items = [x for x in ordered if x[2] != best_val]
        if not second_items:
            return
        second_val = second_items[0][2]
        second_group = [x for x in second_items if x[2] == second_val]
        if ties == "first":
            second_group = second_group[:1]
        if ties == "none" and len(second_group) > 1:
            return
        for r, c, _ in second_group:
            highlights.setdefault((r, c), "second")

    if scope == "column":
        for c in cols:
            dir_value = _direction_for_column(spec, c) if isinstance(direction, dict) else direction
            items = []
            for r in rows:
                if r in summary_rows or c in summary_cols:
                    continue
                cell = cells.get((r, c))
                if cell is None:
                    continue
                items.append((r, c, cell["center"]))
            apply_group(items, dir_value)
    elif scope == "row":
        if isinstance(direction, dict):
            raise ValueError("Row-scope highlighting does not support per-column directions")
        for r in rows:
            items = []
            for c in cols:
                if r in summary_rows or c in summary_cols:
                    continue
                cell = cells.get((r, c))
                if cell is None:
                    continue
                items.append((r, c, cell["center"]))
            apply_group(items, direction)
    else:  # table
        if isinstance(direction, dict):
            unique = set(direction.values())
            if len(unique) > 1:
                raise ValueError("Table-scope highlighting requires a single direction")
            direction = next(iter(unique))
        items = []
        for (r, c), cell in cells.items():
            if r in summary_rows or c in summary_cols:
                continue
            items.append((r, c, cell["center"]))
        apply_group(items, direction)

    return highlights


def compute_significance(table: Dict[str, Any], spec: Dict[str, Any]) -> Dict[Tuple[Any, Any], str]:
    sig = spec.get("significance")
    if not sig:
        return {}
    baseline = sig["baseline"]
    level = sig.get("level", 0.95)
    n_boot = sig.get("n_boot", 1000)
    seed = sig.get("seed", 0)
    symbol = sig.get("symbol", "*")
    direction = spec["metric"]["direction"]

    markers: Dict[Tuple[Any, Any], str] = {}
    rows = table["rows"]
    cols = table["cols"]
    summary_rows = set(table.get("summary_rows", []))
    summary_cols = set(table.get("summary_cols", []))
    cells = table["cells"]

    if baseline not in rows:
        return markers

    for c in cols:
        if c in summary_cols:
            continue
        dir_value = _direction_for_column(spec, c) if isinstance(direction, dict) else direction
        base_cell = cells.get((baseline, c))
        if base_cell is None:
            continue
        base_vals = base_cell.get("values") or []
        for r in rows:
            if r == baseline:
                continue
            if r in summary_rows:
                continue
            cell = cells.get((r, c))
            if cell is None:
                continue
            vals = cell.get("values") or []
            if not vals or not base_vals:
                continue
            lo, hi = bootstrap_diff_ci(vals, base_vals, mean, level, n_boot, seed)
            # If direction is min, flip sign so "better" is positive
            if dir_value == "min":
                lo, hi = -hi, -lo
            if lo > 0:
                markers[(r, c)] = symbol
    return markers


def _apply_summaries(table: Dict[str, Any], spec: Dict[str, Any]) -> None:
    agg = spec.get("aggregate", {})
    row_summary = agg.get("row_summary")
    col_summary = agg.get("col_summary")
    cells = table["cells"]
    table.setdefault("summary_cols", [])
    table.setdefault("summary_rows", [])

    if row_summary:
        label = row_summary["label"]
        stat = row_summary.get("stat", "mean")
        position = row_summary.get("position", "end")
        summary_col = label
        table["summary_cols"].append(summary_col)
        if position == "start":
            table["cols"] = [summary_col] + table["cols"]
        else:
            table["cols"].append(summary_col)
        for r in table["rows"]:
            values = [cells[(r, c)]["center"] for c in table["cols"] if (r, c) in cells and c != summary_col]
            if not values:
                continue
            center = mean(values) if stat == "mean" else median(values)
            cells[(r, summary_col)] = {"center": center, "n": len(values), "unc": None, "ci": None, "values": values}

    if col_summary:
        label = col_summary["label"]
        stat = col_summary.get("stat", "mean")
        position = col_summary.get("position", "end")
        summary_row = label
        table["summary_rows"].append(summary_row)
        if position == "start":
            table["rows"] = [summary_row] + table["rows"]
        else:
            table["rows"].append(summary_row)
        for c in table["cols"]:
            values = [cells[(r, c)]["center"] for r in table["rows"] if (r, c) in cells and r != summary_row]
            if not values:
                continue
            center = mean(values) if stat == "mean" else median(values)
            cells[(summary_row, c)] = {"center": center, "n": len(values), "unc": None, "ci": None, "values": values}
