"""HTML preview rendering."""

from __future__ import annotations

from html import escape as html_escape
from typing import Any, Dict, List, Tuple


def _format_number(value: float, decimals: int, trailing_zeros: bool, scientific: bool) -> str:
    if scientific:
        fmt = f"{{:.{decimals}e}}"
    else:
        fmt = f"{{:.{decimals}f}}"
    text = fmt.format(value)
    if not trailing_zeros and not scientific:
        if "." in text:
            text = text.rstrip("0").rstrip(".")
    return text


def _format_for_column(spec: Dict[str, Any], column: Any) -> Dict[str, Any]:
    fmt = spec["format"]
    overrides = fmt.get("overrides", {})
    if column in overrides:
        merged = dict(fmt)
        merged.update(overrides[column])
        return merged
    return fmt


def _cell_to_text(cell: Dict[str, Any], spec: Dict[str, Any], column: Any) -> str:
    fmt = _format_for_column(spec, column)
    mode = fmt["mode"]
    mean_decimals = fmt.get("mean_decimals", 2)
    unc_decimals = fmt.get("unc_decimals", 2)
    trailing = fmt.get("trailing_zeros", True)
    scientific = fmt.get("scientific", False)

    center = cell["center"]
    mean_text = _format_number(center, mean_decimals, trailing, scientific)

    if cell["unc"] is None and cell["ci"] is None:
        return mean_text

    if mode == "pm":
        if cell["ci"] is not None:
            lo, hi = cell["ci"]
            unc = (hi - lo) / 2.0
        else:
            unc = cell["unc"]
        unc_text = _format_number(unc, unc_decimals, trailing, scientific)
        return f"{mean_text} ± {unc_text}"

    if cell["ci"] is not None:
        lo, hi = cell["ci"]
    else:
        unc = cell["unc"]
        lo, hi = center - unc, center + unc
    lo_text = _format_number(lo, unc_decimals, trailing, scientific)
    hi_text = _format_number(hi, unc_decimals, trailing, scientific)
    return f"{mean_text} [{lo_text}, {hi_text}]"


def _apply_style(text: str, style: str) -> str:
    if style == "bold":
        return f"<strong>{text}</strong>"
    if style == "underline":
        return f"<u>{text}</u>"
    if style.startswith("cellcolor:"):
        color = style.split(":", 1)[1]
        return f"<span style=\"background-color:{html_escape(color)};\">{text}</span>"
    return text


def render_html(
    table: Dict[str, Any],
    highlights: Dict[Tuple[Any, Any], str],
    spec: Dict[str, Any],
) -> str:
    rows = table["rows"]
    cols = table["cols"]
    cells = table["cells"]

    highlight_spec = spec.get("highlight", {})

    # Build column group header (if any)
    col_groups = spec.get("cols", {}).get("groups") or []
    group_lookup = {}
    for group in col_groups:
        for member in group.get("members", []):
            group_lookup[member] = group.get("label", "")

    # Row groups
    row_groups = spec.get("rows", {}).get("groups") or []
    group_map = {}
    group_last = {}
    for group in row_groups:
        members = [m for m in group.get("members", []) if m in rows]
        for member in members:
            group_map[member] = group
        if members:
            group_last[group.get("label", "")] = members[-1]

    # Build HTML
    parts: List[str] = []
    parts.append("<style>table{border-collapse:collapse}th,td{border:1px solid #ccc;padding:4px 8px}th{background:#f5f5f5}</style>")
    parts.append("<table>")
    parts.append("<thead>")

    if col_groups:
        # Build contiguous segments
        segments = []
        current = None
        for col in cols:
            label = group_lookup.get(col, "")
            if current is None or current["label"] != label:
                current = {"label": label, "span": 1}
                segments.append(current)
            else:
                current["span"] += 1
        parts.append("<tr>")
        parts.append("<th></th>")
        for seg in segments:
            label = html_escape(seg["label"])
            parts.append(f"<th colspan=\"{seg['span']}\">{label}</th>")
        parts.append("</tr>")

    parts.append("<tr>")
    parts.append("<th></th>")
    for c in cols:
        parts.append(f"<th>{html_escape(str(c))}</th>")
    parts.append("</tr>")
    parts.append("</thead>")
    parts.append("<tbody>")

    current_group = None
    for r in rows:
        group = group_map.get(r)
        if group is not None and group is not current_group:
            label = html_escape(group.get("label", ""))
            parts.append(f"<tr><th colspan=\"{len(cols)+1}\">{label}</th></tr>")
            current_group = group

        row_cells: List[str] = []
        row_cells.append(f"<th>{html_escape(str(r))}</th>")
        for c in cols:
            cell = cells.get((r, c))
            if cell is None:
                text = html_escape(spec["format"].get("missing", "--"))
            else:
                text = html_escape(_cell_to_text(cell, spec, c))
                highlight = highlights.get((r, c))
                if highlight:
                    style = highlight_spec.get(highlight, {}).get("style")
                    if style:
                        text = _apply_style(text, style)
            row_cells.append(f"<td>{text}</td>")
        parts.append("<tr>" + "".join(row_cells) + "</tr>")

        if group is not None and group_last.get(group.get("label", "")) == r:
            if group.get("separator"):
                parts.append(f"<tr><td colspan=\"{len(cols)+1}\"></td></tr>")

    parts.append("</tbody>")
    parts.append("</table>")
    return "\n".join(parts)
