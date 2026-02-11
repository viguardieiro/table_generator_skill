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

    lines = []
    lines.append(top_rule)
    lines.append(" & ".join(header) + " \\\\")
    lines.append(mid_rule)

    for r in rows:
        row_label = _escape_latex(str(r)) if escape else str(r)
        row_cells = [row_label]
        for c in cols:
            cell = cells.get((r, c))
            if cell is None:
                text = spec["format"].get("missing", "--")
                text = _escape_latex(text) if escape else text
            else:
                text = _cell_to_text(cell, spec)
                if escape:
                    # Only escape row/col labels; cell numeric text is safe.
                    pass
                highlight = highlights.get((r, c))
                if highlight:
                    style = highlight_spec.get(highlight, {}).get("style")
                    if style:
                        text = _apply_style(text, style)
            row_cells.append(text)
        lines.append(" & ".join(row_cells) + " \\\\")

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
        table_lines.append("\\end{table}")
        text = "\n".join(table_lines)
    else:
        text = tabular_block

    return text, preamble
