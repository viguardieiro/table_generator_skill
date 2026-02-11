---
name: table-generator
description: Generate publication-ready LaTeX or Markdown tables from long-form experimental results using the local table_generator tool (tablegen CLI). Use when any agent needs to aggregate results (mean/median), compute uncertainty (std/sem/CI), highlight best/second-best, and render ML conference-style tables from JSON records + a declarative spec.
---

# Table Generator

## Quick start

1. Prepare records and spec JSON.

- Start from the templates in `skills/table-generator/resources/spec_template.json` and `skills/table-generator/resources/records_example.json`.
- Records are long-form: one scalar per row/seed/run.

2. Render the table.

- If `tablegen` is installed (CLI name):  
  - `tablegen render --records records.json --spec spec.json --out table.tex`
- Otherwise run from repo root via the Python package `table_generator`:  
  - `python -m table_generator.cli render --records records.json --spec spec.json --out table.tex`

3. Paste the output into your paper/repo. For LaTeX package requirements, see `skills/table-generator/resources/latex_preamble.md`.

## Spec guidance (minimal)

- Required blocks: `rows`, `cols`, `metric`, `aggregate`.
- Required fields: `rows.field`, `cols.field`, `metric.field`, `metric.value`, `metric.direction`, `aggregate.over`.
- Output format: set `output.format` to `latex` or `markdown`.

## Error handling

- If the CLI exits with an error, read the path in the message (e.g., `spec.aggregate.uncertainty.level`) and fix the spec or the records accordingly.
- Do not infer missing intent; update the spec explicitly.

## Data safety (must follow)

- Treat the user's raw results as read-only. Do not edit, overwrite, or reformat original results files.
- If you need to change structure/format, write to a new file (e.g., `records_clean.json`) or use a temp copy.
- If an error occurs, do not “fix” or rewrite the source results. Adjust the spec or generate derived files only.

## When to use resources

- Use `spec_template.json` as the starting point for any new table.
- Use `records_example.json` as a schema reference for valid record keys.
- Use `latex_preamble.md` to add required LaTeX packages when you use booktabs or cell colors.
