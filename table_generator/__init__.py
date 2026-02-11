"""Public API for table_generator."""

from .api import render_table  # noqa: F401
from .schema import SchemaError  # noqa: F401

__all__ = ["render_table", "SchemaError"]
