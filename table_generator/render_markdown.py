"""Markdown rendering."""

from __future__ import annotations

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


def _cell_to_text(cell: Dict[str, Any], spec: Dict[str, Any]) -> str:
    fmt = spec["format"]
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


def _apply_style(text: str, style: str, bold_token: str, underline_token: str) -> str:
    if style == "bold":
        return f"{bold_token}{text}{bold_token}"
    if style == "underline":
        return f"{underline_token}{text}{underline_token}"
    return text


def _title_case(text: str) -> str:
    return " ".join([part.capitalize() for part in text.replace("_", " ").split()])


def render_markdown(
    table: Dict[str, Any],
    highlights: Dict[Tuple[Any, Any], str],
    spec: Dict[str, Any],
) -> str:
    rows = table["rows"]
    cols = table["cols"]
    cells = table["cells"]

    fmt = spec["format"]
    highlight_spec = spec.get("highlight", {})
    output_md = spec["output"]["markdown"]

    bold_token = output_md.get("bold", "**")
    underline_token = output_md.get("underline", "_")
    separator = output_md.get("separator", "|")

    header = [_title_case(table["row_field"])] + [str(c) for c in cols]

    body_rows: List[List[str]] = []
    for r in rows:
        row = [str(r)]
        for c in cols:
            cell = cells.get((r, c))
            if cell is None:
                text = fmt.get("missing", "--")
            else:
                text = _cell_to_text(cell, spec)
                highlight = highlights.get((r, c))
                if highlight:
                    style = highlight_spec.get(highlight, {}).get("style")
                    if style:
                        text = _apply_style(text, style, bold_token, underline_token)
            row.append(text)
        body_rows.append(row)

    alignment = output_md.get("alignment", "auto")
    if alignment == "auto":
        align_row = [":---"] + [":---:" for _ in cols]
    elif alignment == "left":
        align_row = [":---" for _ in header]
    elif alignment == "right":
        align_row = ["---:" for _ in header]
    else:
        align_row = [":---:" for _ in header]

    lines = []
    if output_md.get("include_caption") and spec["latex"].get("caption"):
        lines.append(f"*{spec['latex']['caption']}*")

    lines.append(separator + " " + (" {} ".format(separator)).join(header) + " " + separator)
    lines.append(separator + " " + (" {} ".format(separator)).join(align_row) + " " + separator)
    for row in body_rows:
        lines.append(separator + " " + (" {} ".format(separator)).join(row) + " " + separator)

    return "\n".join(lines)
