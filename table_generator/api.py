"""High-level API for rendering tables."""

from __future__ import annotations

from typing import Any, Dict, List

from .pipeline import render_pipeline
from .schema import validate_spec


def render_table(records: List[Dict[str, Any]], spec: Dict[str, Any]) -> Dict[str, Any]:
    """Render a table from records and spec.

    Returns a dict with keys: format, text, preamble, meta.
    """
    validated = validate_spec(spec)
    return render_pipeline(records, validated)
