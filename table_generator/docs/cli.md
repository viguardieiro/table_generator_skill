# CLI Reference

## Commands

### `tablegen render`

Render a table from records and a spec.

```bash
tablegen render --records records.json --spec spec.json --out table.tex
```

Arguments:
- `--records`: JSON or JSONL records file (long-form).
- `--spec`: spec JSON file.
- `--out`: optional output path. If omitted, output is printed to stdout.
- `--preview`: render an HTML preview instead of the main output.
- `--open`: open the HTML preview in the default browser (best-effort). If `--out` is not set, a temp file is created.
- `--export`: write computed stats to a JSON or CSV file.
- `--export-format`: `json` or `csv` (defaults to JSON unless path ends with `.csv`).

Behavior:
- Exits non-zero on schema errors.
- Does not modify input files.

### `tablegen template`

Emit a starter spec and record example.

```bash
tablegen template --out spec_template.json
```

## Error format

Errors include the spec path that failed validation, e.g.:

```
Error: CI level must be between 0 and 1 (path: spec.aggregate.uncertainty.level)
```

Use the path to fix the exact field in the spec.
