"""Export computed table statistics."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def _cell_payload(cell: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "center": cell.get("center"),
        "unc": cell.get("unc"),
        "n": cell.get("n"),
        "delta": bool(cell.get("delta")),
        "delta_mode": cell.get("delta_mode"),
    }
    ci = cell.get("ci")
    if ci is not None:
        payload["ci_lo"] = ci[0]
        payload["ci_hi"] = ci[1]
    else:
        payload["ci_lo"] = None
        payload["ci_hi"] = None
    return payload


def build_export_rows(
    table: Dict[str, Any],
    highlights: Dict[Tuple[Any, Any], str],
    markers: Dict[Tuple[Any, Any], str],
) -> List[Dict[str, Any]]:
    rows = table["rows"]
    cols = table["cols"]
    cells = table["cells"]

    out: List[Dict[str, Any]] = []
    for r in rows:
        for c in cols:
            cell = cells.get((r, c))
            payload = {
                "row": r,
                "col": c,
                "missing": cell is None,
                "highlight": highlights.get((r, c)),
                "significant": markers.get((r, c)),
            }
            if cell is not None:
                payload.update(_cell_payload(cell))
            else:
                payload.update({
                    "center": None,
                    "unc": None,
                    "n": None,
                    "delta": False,
                    "delta_mode": None,
                    "ci_lo": None,
                    "ci_hi": None,
                })
            out.append(payload)
    return out


def write_export_json(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    Path(path).write_text(json.dumps(list(rows), indent=2))


def write_export_csv(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    rows_list = list(rows)
    if not rows_list:
        Path(path).write_text("")
        return
    fieldnames = list(rows_list[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_list)
