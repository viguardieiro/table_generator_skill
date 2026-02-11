# table_generator

`table_generator` is a **local, deterministic table-generation tool** (Python package + CLI) for producing **camera-ready tables** (LaTeX or Markdown) from raw experimental results, designed for scientific/ML papers.

Instead of manually editing tables every time results change, you provide:

- **records**: long-form experimental results (e.g., per-seed metrics)
- **spec**: a declarative table specification (aggregation, formatting, highlighting)

…and the tool generates reproducible, publication-quality tables.

---

## Motivation

Writing tables is tedious, error-prone, and hard to reproduce.

Common pain points:
- Copy-paste errors when updating results
- Inconsistent rounding across tables
- Manually bolding best results
- Rewriting tables for LaTeX vs Markdown

`table_generator` solves this by making tables **generated artifacts**, not handwritten ones.

---

## What it does

Given:
- raw experiment records (e.g., per-seed metrics)
- a declarative table specification

the tool outputs:
- LaTeX tables (booktabs-style, paper-ready)
- Markdown tables (GitHub-friendly)

---

## Installation

Editable install (recommended during development):

```bash
pip install -e .
```

---

## Typical workflow

1) Export experimental results from your training/evaluation code (JSON, JSONL, CSV → JSON, etc.)

Records are **long format**: one scalar measurement per row/run/seed, e.g.:

```json
[
  {"model": "Ours", "dataset": "MNLI", "metric": "acc", "seed": 0, "value": 85.4},
  {"model": "Ours", "dataset": "MNLI", "metric": "acc", "seed": 1, "value": 85.1}
]
```

2) Define a table specification (`spec.json`).

A starter template is provided by the CLI:

```bash
tablegen template --out spec.json
```

3) Render the table:

```bash
tablegen render --records records.json --spec spec.json --out table.tex
```

- The rendered table is also printed to stdout by default (useful for quick copy/paste).
- Output format is controlled by `spec.output.format` (`latex` or `markdown`). (An override flag can be added later if desired.)

4) Paste the output directly into:
- your paper
- a rebuttal
- a README

---

## CLI

Minimum CLI surface (MVP):

- `tablegen render --records <path> --spec <path> [--out <path>]`
  - Reads JSON (or JSONL) records + JSON spec
  - Writes the rendered table to stdout (and optionally `--out`)
  - Exits non-zero on schema errors

- `tablegen template [--out <path>]`
  - Emits a default spec template + a minimal record example

Optional (nice-to-have):
- `tablegen validate --spec <path>`

---

## Supported features (MVP)

### Aggregation

- Mean, median
- Standard deviation (std)
- Standard error of the mean (SEM)
- Bootstrap confidence intervals (deterministic via seed)

### Formatting

- Mean ± std / CI
- Independent decimal control for mean and uncertainty
- Scientific notation (optional)
- Custom value templates

### Highlighting

- Best / worst / second-best values
- Per-row or per-column comparison
- Styles:
  - bold
  - underline
  - background color (LaTeX only)

### Output formats

- LaTeX (booktabs-style)
- Markdown (pipe tables, GitHub-compatible)

---

## Using with Codex / Claude Code

This repo includes a skill at:

- `skills/table-generator/SKILL.md`

The skill tells the agent how to:
- serialize `records` + `spec` to JSON
- run `tablegen render`
- paste the resulting LaTeX/Markdown back into your paper/repo
- diagnose schema validation errors (fix spec vs fix records)

---

## Design principles

- Declarative: describe what the table should look like, not how
- Deterministic: same inputs → same table (given fixed seed)
- Backend-agnostic: stats and rendering are cleanly separated
- Reproducible: tables can be regenerated at any time

---

## Status

This project is a minimal but extensible table generator.

The MVP is designed to cover the majority of tables found in modern ML papers, with room to grow toward:

- multi-level column or row headers
- tables combining multiple metrics with heterogeneous aggregation/formatting
- statistical significance testing
- automatic footnotes and annotations

For the full spec and implementation plan, see `plan_updated.md`.
