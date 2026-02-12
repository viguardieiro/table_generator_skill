# Python API Reference

## `table_generator.render_table(records, spec) -> dict`

Render a table from long-form records and a spec.

### Parameters

- `records` (list[dict]): Long-form measurement records. Each record must contain:
  - row field (e.g., `model`)
  - column field (e.g., `dataset` or `metric_name`)
  - metric field (e.g., `metric`)
  - `value` (numeric)
  - aggregation key (e.g., `seed`)
- `spec` (dict): Table specification. See `table_generator/docs/spec.md` for full schema.

### Returns

A dict with:

- `format` (str): `"latex"` or `"markdown"`
- `text` (str): Rendered table
- `preamble` (list[str]): Required LaTeX packages (empty for markdown)
- `meta` (dict): metadata summary (rows, cols, metric, uncertainty)

### Example

```python
from table_generator import render_table

result = render_table(records, spec)
print(result["text"])
```

## `table_generator.SchemaError`

Raised when the spec is invalid. Error messages include a dotted path to the invalid field, for example:

```
CI level must be between 0 and 1 (path: spec.aggregate.uncertainty.level)
```

## CLI entrypoints (module)

You can call the CLI directly from Python:

```bash
python -m table_generator.cli render --records records.json --spec spec.json --out table.tex
```

See `table_generator/docs/cli.md` for all CLI details.
