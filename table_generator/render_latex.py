"""LaTeX rendering."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _escape_latex(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    out = ""
    for ch in text:
        out += replacements.get(ch, ch)
    return out


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


def _cell_to_text(cell: Dict[str, Any], spec: Dict[str, Any], column: Any) -> str:
    if cell.get("delta"):
        return _format_delta(cell, spec)
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
        return f"{mean_text} \\(\\pm\\) {unc_text}"

    # ci_brackets
    if cell["ci"] is not None:
        lo, hi = cell["ci"]
    else:
        unc = cell["unc"]
        lo, hi = center - unc, center + unc
    lo_text = _format_number(lo, unc_decimals, trailing, scientific)
    hi_text = _format_number(hi, unc_decimals, trailing, scientific)
    return f"{mean_text} [{lo_text}, {hi_text}]"


def _format_delta(cell: Dict[str, Any], spec: Dict[str, Any]) -> str:
    delta_spec = spec.get("delta", {})
    fmt = delta_spec.get("format", {})
    decimals = fmt.get("decimals", spec["format"].get("mean_decimals", 2))
    show_plus = fmt.get("show_plus", True)
    percent = fmt.get("percent")
    if percent is None:
        percent = cell.get("delta_mode") == "relative"

    value = cell["center"]
    if percent:
        value = value * 100
    text = _format_number(value, decimals, True, False)
    if show_plus and value > 0:
        text = f"+{text}"
    if percent:
        text = f"{text}\\%"
    return text


def _apply_style(text: str, style: str) -> str:
    if style == "bold":
        return f"\\textbf{{{text}}}"
    if style == "underline":
        return f"\\underline{{{text}}}"
    if style.startswith("cellcolor:"):
        color = style.split(":", 1)[1]
        return f"\\cellcolor{{{color}}}{{{text}}}"
    return text


def render_latex(
    table: Dict[str, Any],
    highlights: Dict[Tuple[Any, Any], str],
    spec: Dict[str, Any],
    markers: Dict[Tuple[Any, Any], str] | None = None,
) -> Tuple[str, List[str]]:
    rows = table["rows"]
    cols = table["cols"]
    cells = table["cells"]

    latex_spec = spec["latex"]
    escape = latex_spec.get("escape", True)
    highlight_spec = spec.get("highlight", {})

    alignment = latex_spec.get("alignment")
    if not alignment:
        alignment = "l" + "c" * len(cols)

    top_rule = "\\toprule" if latex_spec.get("booktabs", True) else "\\hline"
    mid_rule = "\\midrule" if latex_spec.get("booktabs", True) else "\\hline"
    bottom_rule = "\\bottomrule" if latex_spec.get("booktabs", True) else "\\hline"

    header = [""] + [str(c) for c in cols]
    if escape:
        header = [_escape_latex(h) for h in header]

    col_groups = spec.get("cols", {}).get("groups") or []
    header_lines = []
    if col_groups:
        group_row = [""]  # empty top-left corner
        cmidrules = []
        group_lookup = {}
        for group in col_groups:
            for member in group.get("members", []):
                group_lookup[member] = group
        segments = []
        current = None
        for col in cols:
            group = group_lookup.get(col)
            label = group.get("label", "") if group else ""
            cmid = group.get("cmidrule", True) if group else False
            if current is None or current["label"] != label:
                current = {"label": label, "span": 1, "cmidrule": cmid}
                segments.append(current)
            else:
                current["span"] += 1
        col_index = 2
        for seg in segments:
            label = _escape_latex(seg["label"]) if escape else seg["label"]
            group_row.append(f"\\multicolumn{{{seg['span']}}}{{c}}{{{label}}}")
            if seg["cmidrule"] and seg["label"]:
                cmidrules.append(f"\\cmidrule(lr){{{col_index}-{col_index + seg['span'] - 1}}}")
            col_index += seg["span"]
        header_lines.append(" & ".join(group_row) + " \\\\")
        if cmidrules:
            header_lines.append(" ".join(cmidrules))

    lines = []
    lines.append(top_rule)
    if header_lines:
        lines.extend(header_lines)
    lines.append(" & ".join(header) + " \\\\")
    lines.append(mid_rule)

    row_groups = spec.get("rows", {}).get("groups") or []
    group_map = {}
    group_last = {}
    for group in row_groups:
        members = [m for m in group.get("members", []) if m in rows]
        for member in members:
            group_map[member] = group
        if members:
            group_last[group.get("label", "")] = members[-1]

    current_group = None
    for r in rows:
        group = group_map.get(r)
        if group is not None and group is not current_group:
            label = group.get("label", "")
            label = _escape_latex(label) if escape else label
            label_row = f"\\multicolumn{{{len(cols)+1}}}{{l}}{{\\textbf{{{label}}}}} \\\\"
            lines.append(label_row)
            current_group = group
        row_label = _escape_latex(str(r)) if escape else str(r)
        row_cells = [row_label]
        for c in cols:
            cell = cells.get((r, c))
            if cell is None:
                text = spec["format"].get("missing", "--")
                text = _escape_latex(text) if escape else text
            else:
                text = _cell_to_text(cell, spec, c)
                if escape:
                    # Only escape row/col labels; cell numeric text is safe.
                    pass
                highlight = highlights.get((r, c))
                if highlight:
                    style = highlight_spec.get(highlight, {}).get("style")
                    if style:
                        text = _apply_style(text, style)
                if markers and (r, c) in markers:
                    text = f"{text}\\textsuperscript{{{markers[(r, c)]}}}"
            row_cells.append(text)
        lines.append(" & ".join(row_cells) + " \\\\")
        if group is not None and group_last.get(group.get("label", "")) == r:
            sep = group.get("separator")
            if sep == "midrule":
                lines.append(mid_rule)
            elif sep == "hline":
                lines.append("\\hline")

    lines.append(bottom_rule)

    tabular_name = latex_spec.get("tabular", "tabular")
    tabular_block = "\n".join([
        f"\\begin{{{tabular_name}}}{{{alignment}}}",
        *lines,
        f"\\end{{{tabular_name}}}",
    ])

    if latex_spec.get("resize"):
        resize = latex_spec["resize"]
        tabular_block = f"{resize}{{\n{tabular_block}\n}}"

    preamble = []
    if latex_spec.get("booktabs", True):
        preamble.append("booktabs")
    if any(
        (spec.get("highlight", {}).get(k, {}).get("style", "").startswith("cellcolor:"))
        for k in ("best", "second")
    ):
        preamble.append("xcolor")
    if tabular_name == "tabularx":
        preamble.append("tabularx")

    if latex_spec.get("environment", True):
        table_lines = ["\\begin{table}[t]", "\\centering", tabular_block]
        caption = latex_spec.get("caption")
        label = latex_spec.get("label")
        if caption:
            table_lines.append(f"\\caption{{{_escape_latex(caption) if escape else caption}}}")
        if label:
            table_lines.append(f"\\label{{{_escape_latex(label) if escape else label}}}")
        footnotes = latex_spec.get("footnotes")
        if footnotes:
            notes = " ".join(footnotes)
            notes = _escape_latex(notes) if escape else notes
            table_lines.append(f"{{\\\\footnotesize {notes}}}")
        table_lines.append("\\end{table}")
        text = "\n".join(table_lines)
    else:
        text = tabular_block

    return text, preamble


def _format_for_column(spec: Dict[str, Any], column: Any) -> Dict[str, Any]:
    fmt = spec["format"]
    overrides = fmt.get("overrides", {})
    if column in overrides:
        merged = dict(fmt)
        merged.update(overrides[column])
        return merged
    return fmt
