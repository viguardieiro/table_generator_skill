---
name: table-generator
description: Generate publication-ready LaTeX or Markdown tables from long-form experimental results with the local `tablegen` tool. Use when Codex needs to aggregate runs (mean/median), compute uncertainty (std/sem/CI), highlight best and second-best values, or produce ML-conference-style result tables from records plus a JSON spec.
---

# Table Generator

## Execute Workflow

1. Prepare inputs.
   - Read records from user-provided files.
   - Use `skills/table-generator/resources/spec_template.json` as the starting spec.
   - Use `skills/table-generator/resources/records_example.json` only as schema guidance.
   - Keep records long-form (one scalar measurement per row/seed/run).
2. Configure the spec.
   - Set `rows.field`, `cols.field`, `metric.field`, `metric.value`, `metric.direction`, `aggregate.over`, and `output.format`.
   - Set `aggregate.stat` to `mean` or `median`.
   - Set `aggregate.uncertainty.type` to `none`, `std`, `sem`, or `ci`.
   - Read `skills/table-generator/references/spec_reference.md` when any field or allowed value is unclear.
3. Render.
   - Prefer CLI: `tablegen render --records records.json --spec spec.json --out table.tex`
   - Fallback: `python -m table_generator.cli render --records records.json --spec spec.json --out table.tex`
4. Return output.
   - Return the rendered table and any execution notes.
   - For LaTeX output, include required packages from `skills/table-generator/resources/latex_preamble.md`.

## Enforce Data Safety

- Treat the user's raw results as read-only. Do not edit, overwrite, or reformat original results files.
- If reshaping is needed, write a derived file (for example `records_clean.json`).
- If errors occur, fix the spec or the derived file, not the source results.

## Enforce Non-Hallucination

- All table values must be computed from the provided results or from `tablegen` output. Do not invent, estimate, or fill in values.
- If data is missing, leave the cell as missing and explain why.

## Keep Context Small

- Do not load entire results files into context unless the file is tiny.
- Inspect schema and a small sample (first 5-20 rows).
- If multiple files share schema, inspect one representative file.
- Prefer lightweight inspection:
  - JSONL: `head -n 20 results.jsonl`
  - JSON array: print only the first 5 records
  - CSV: read headers and first 5 rows

## Apply Spec Rules

Keep spec fields explicit. Do not guess undocumented values.

Require at minimum:
- Blocks: `rows`, `cols`, `metric`, `aggregate`
- Fields: `rows.field`, `cols.field`, `metric.field`, `metric.value`, `metric.direction`, `aggregate.over`
- Output format: `output.format` = `latex` or `markdown`

Use these rules:
- `metric.field` + `metric.value` filter records; they do not create columns. If you need multiple metrics as columns, see the reference.
- For uncertainty, set `aggregate.uncertainty.type` (`none`, `std`, `sem`, or `ci`). CI requires extra fields (method, level, n_boot).
- If metrics have mixed directions (e.g., accuracy vs loss), use a per-column `metric.direction` map (see reference).

## Handle Errors

- If the CLI errors, the message will point to the exact field that is invalid (e.g., `spec.aggregate.uncertainty.level`). Fix that field in the spec or create a derived records file.
- Do not guess missing settings. Use documented defaults, or ask the user to confirm.
- If a value is missing or ambiguous, leave the cell as missing and explain why.
- Never rewrite raw results to satisfy schema checks.

## Use Bundled Resources

- Use `spec_template.json` as the starting point for any new table.
- Use `records_example.json` as a schema reference for valid record keys.
- Use `latex_preamble.md` to add required LaTeX packages when you use booktabs or cell colors.
