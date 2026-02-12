---
name: table-generator
description: Generate publication-ready LaTeX or Markdown tables from long-form experimental results using the local `tablegen` tool. Use for aggregations (mean/median), uncertainty (std/sem/CI), highlighting best/second-best, and ML-style results tables.
---

# Table Generator

## Workflow

1. Prepare records and spec JSON.
   - Use templates in `skills/table-generator/resources/spec_template.json` and `skills/table-generator/resources/records_example.json`.
   - Records must be long-form (one scalar per row/seed/run).
2. Render the table.
   - Prefer the CLI: `tablegen render --records records.json --spec spec.json --out table.tex`
   - If the CLI is unavailable: `python -m table_generator.cli render --records records.json --spec spec.json --out table.tex`
3. Return the rendered table output and note any LaTeX package requirements (see `skills/table-generator/resources/latex_preamble.md`).

## Data safety

- Treat the user's raw results as read-only. Do not edit, overwrite, or reformat original results files.
- If you need to change structure/format, write to a new file (e.g., `records_clean.json`) or use a temp copy.
- If an error occurs, do not “fix” or rewrite the source results. Adjust the spec or generate derived files only.

## Non-hallucination rule

- All table values must be computed from the provided results or from `tablegen` output. Do not invent, estimate, or fill in values.
- If the data needed to compute a value is missing, leave the cell as missing and explain the limitation.

## Context hygiene

- Do not load entire results files into context unless the file is tiny.
- Inspect only the schema and a small sample (first 5–20 rows). If multiple files share the same schema, inspect one.
- Prefer lightweight inspection:
  - JSONL: `head -n 20 results.jsonl`
  - JSON array: print only the first 5 records
  - CSV: read headers and first 5 rows

## Spec guidance

Keep specs explicit. If unsure about any field or allowed values, read `skills/table-generator/references/spec_reference.md` before proceeding.

Minimum required fields:
- Blocks: `rows`, `cols`, `metric`, `aggregate`
- Fields: `rows.field`, `cols.field`, `metric.field`, `metric.value`, `metric.direction`, `aggregate.over`
- Output format: `output.format` = `latex` or `markdown`

General notes:
- `metric.field` + `metric.value` filter records; they do not create columns. If you need multiple metrics as columns, see the reference.
- For uncertainty, set `aggregate.uncertainty.type` (`none`, `std`, `sem`, or `ci`). CI requires extra fields (method, level, n_boot).
- If metrics have mixed directions (e.g., accuracy vs loss), use a per-column `metric.direction` map (see reference).

## Error handling

- If the CLI errors, the message will point to the exact field that is invalid (e.g., `spec.aggregate.uncertainty.level`). Fix that field in the spec or create a derived records file.
- Do not guess missing settings. Use documented defaults, or ask the user to confirm.
- If a value is missing or ambiguous, leave the cell as missing and explain why.
- Never “fix” raw results to satisfy the schema.

## When to use resources

- Use `spec_template.json` as the starting point for any new table.
- Use `records_example.json` as a schema reference for valid record keys.
- Use `latex_preamble.md` to add required LaTeX packages when you use booktabs or cell colors.
