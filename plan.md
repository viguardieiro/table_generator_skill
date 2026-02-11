# table_generator (skill + Python package)

## Overview

`table_generator` is a **local, deterministic table-generation tool** (a Python package + CLI) that produces **publication-ready LaTeX tables** (and optionally Markdown tables) for scientific/ML papers from raw experimental results.

It is intentionally **data-agnostic** (no assumption about W&B, Hydra, etc.) and operates on **long-form result records** plus a **declarative table specification**. The goal is to encode *paper conventions* (aggregation, uncertainty, highlighting, formatting) once and reuse them reliably.

This document is a **full implementation plan and spec** intended to be consumed by Codex / Claude Code (or any coding agent) via a **skill** (`SKILL.md`) that explains how to call the local CLI/library.

Key property: **no server**. Everything runs in-repo (or in your Python environment), making iteration fast and outputs reproducible.

---

## Design goals

1. Produce LaTeX tables that compile on first try
2. Match common ML / NLP paper conventions
3. Keep configuration declarative and explicit
4. Make defaults sensible but overridable
5. Support incremental extension without breaking schemas

Non-goals:

* Interactive visualization
* Plotting
* Tight integration with experiment trackers

---

## Package & CLI names

- Python package: **`table_generator`** (import as `table_generator` or `tablegen`)
- CLI entrypoint (recommended): **`tablegen`**

The skill will instruct the agent to call the CLI (or Python API) locally; the spec and data formats below stay the same.
NOTE: Keep skill naming consistent with the project and CLI (`table-generator` recommended). Avoid mismatched names like `table_generator_mcp`.

---

## Core concepts

### 1. Records (input data)

All inputs are provided in **long format** as a list of dictionaries.

Each record represents *one scalar measurement*, typically one seed/run.

Required keys (by convention, configurable via spec):

* `row_field` (e.g., model name)
* `col_field` (e.g., dataset name)
* `metric_field` (e.g., metric name)
* `value` (numeric)
* `seed` or `run_id` (used for aggregation)

Example record:

```json
{
  "model": "Ours",
  "dataset": "MNLI",
  "metric": "acc",
  "seed": 2,
  "value": 85.4
}
```

Notes for Codex:

* Expect heterogeneous ordering
* Expect missing combinations
* Do NOT assume wide format

---

### 2. Table specification (the `spec` object)

The `spec` is a **pure configuration object** that controls *everything* about aggregation, formatting, and LaTeX output.

The tool should never infer intent implicitly beyond documented defaults.

---

## Full spec definition

### Spec defaults (explicit)

If a block is omitted, use these defaults to keep behavior deterministic:

- `output.format`: `"latex"`
- `format.mode`: `"pm"`
- `format.missing`: `"--"`
- `format.trailing_zeros`: `true`
- `latex.booktabs`: `true`
- `latex.environment`: `true`
- `latex.escape`: `true`

If a required field is missing (e.g., `metric.direction`), fail fast.

### 2.1 Row specification

```json
"rows": {
  "field": "model",
  "order": ["Baseline", "Ours"],
  "rename": {
    "baseline_v1": "Baseline"
  }
}
```

Semantics:

* `field`: key in records used for table rows
* `order`: optional explicit ordering (others appended or dropped)
* `rename`: mapping applied *before* ordering

Edge cases:

* Missing rows should still appear if present in data
* Ordering should be stable

---

### 2.2 Column specification

```json
"cols": {
  "field": "dataset",
  "order": ["MNLI", "SST2"],
  "rename": {
    "sst-2": "SST2"
  }
}
```

Identical semantics to rows.

---

### 2.3 Metric selection

```json
"metric": {
  "field": "metric",
  "value": "acc",
  "direction": "max"
}
```

Semantics:

* `field`: key containing metric name
* `value`: which metric to render
* `direction`: `"max"` or `"min"` (used for highlighting and ranking)

Notes:

* Direction is **mandatory** for correct highlighting

---

### 2.4 Aggregation specification

```json
"aggregate": {
  "over": ["seed"],
  "stat": "mean",
  "uncertainty": {
    "type": "ci",
    "level": 0.95,
    "method": "bootstrap_percentile",
    "n_boot": 2000,
    "seed": 0
  }
}
```

#### 2.4.1 Center statistics

Supported:

* `mean`
* `median`

#### 2.4.2 Uncertainty types

| type   | Description                |
| ------ | -------------------------- |
| `none` | point estimate only        |
| `std`  | standard deviation         |
| `sem`  | standard error of the mean |
| `ci`   | confidence interval        |

#### 2.4.3 CI methods

Minimum required:

* `bootstrap_percentile`

Optional extensions:

* `bootstrap_bca`
* `t_interval`

Notes for Codex:

* Bootstrap should resample along `aggregate.over`
* CI should return `(lo, hi)`
* For display, CI may be converted to half-width

---

### 2.5 Formatting specification

```json
"format": {
  "mode": "pm",
  "mean_decimals": 2,
  "unc_decimals": 2,
  "trailing_zeros": true,
  "scientific": false,
  "missing": "--"
}
```

Modes:

* `pm`: `mean ± unc`
* `ci_brackets`: `mean [lo, hi]`

Formatting rules:

* Rounding happens **after aggregation**
* Missing values must not crash rendering

Optional future:

* uncertainty-aware rounding

---

### 2.6 Highlighting specification

```json
"highlight": {
  "scope": "column",
  "best": {"style": "bold"},
  "second": {"style": "underline"},
  "ties": "all"
}
```

#### Scope options

* `column` (most common in ML papers)
* `row`
* `table`

#### Styles

Supported:

* `bold`
* `underline`
* `cellcolor:<color>` (requires `xcolor`)

Tie handling:

* `all`: highlight all equal values
* `first`: highlight only first occurrence

Edge case: If multiple cells tie for best, do not highlight any second-best (deterministic).

---

### 2.7 Ranking (optional but common)

```json
"ranking": {
  "enabled": false,
  "method": "average",
  "output": "none"
}
```

Semantics:

* Rank models per column
* Average ranks across columns
* Optionally add rank column or footnote

---

### 2.8 LaTeX output specification

```json
"latex": {
  "environment": true,
  "booktabs": true,
  "tabular": "tabular",
  "alignment": "lcc",
  "caption": "Main results",
  "label": "tab:main",
  "escape": true,
  "resize": null
}
```

Semantics:

* `environment`: wrap in `table` env
* `booktabs`: use `\\toprule` etc.
* `tabular`: `tabular`, `tabularx`, etc.
* `alignment`: explicit column alignment
* `resize`: e.g. `"\\resizebox{\\linewidth}{!}"`

Codex notes:

* Emit required `\\usepackage{}` lines
* Never assume packages are already loaded
* Suggested preamble mapping:
  - `booktabs` if `latex.booktabs=true`
  - `xcolor` only if any `cellcolor:*` is used
  - `ulem` only if you choose `\uline{}` for underline (otherwise use `\underline{}`)
  - `array` if using `tabularx` or custom column types

Escaping rule:

- If `latex.escape=true`, escape LaTeX special characters in all string fields.
- If `latex.escape=false`, treat all strings as raw LaTeX and do not escape.

---

## Output formats

The tool must support **multiple output backends** driven by a single aggregated table representation.

Supported formats:

* `latex` (default, publication-ready)
* `markdown` (GitHub / README / rebuttal friendly)

Output format selection is controlled by an explicit `output` block in the spec.

---

### Output specification

```json
"output": {
  "format": "latex",
  "markdown": {
    "include_caption": true,
    "alignment": "auto",
    "separator": "|",
    "bold": "**",
    "underline": "_"
  }
}
```

Semantics:

* `format`: one of `"latex"` or `"markdown"`
* `include_caption`: if true, emit caption above (Markdown) or below (LaTeX)
* `alignment`: Markdown alignment hint (`auto`, `left`, `center`, `right`)
* `separator`: column separator character
* `bold` / `underline`: tokens used for emphasis in Markdown

Notes for Codex:

* Markdown has no native cell background color; ignore `cellcolor` styles
* Highlight styles must degrade gracefully (e.g., bold only)

---

## Interfaces (local library + CLI)

Instead of exposing an tool server, we expose the same functionality through:

1) a small **Python library API** (for programmatic use), and  
2) a **CLI** (for agents to call deterministically from a repo).

Both interfaces are thin wrappers around the same core pipeline.

### Python API

Recommended public functions (exact names can vary, but keep the I/O stable):

- `render_table(records, spec) -> dict`

Input:

```json
{
  "records": [ ... ],
  "spec": { ... }
}
```

Output (shape is stable across backends):

```json
{
  "format": "latex",
  "text": "<table string>",
  "preamble": ["\usepackage{booktabs}", "..."],
  "meta": {
    "rows": 4,
    "cols": 3,
    "metric": "acc",
    "uncertainty": "ci"
  }
}
```

Notes:

- `format` and `text` change depending on `spec.output.format` (`latex` or `markdown`).
- `preamble` is only meaningful for LaTeX; for Markdown return an empty list.

### CLI

The CLI should be the *default* interface for the skill because it’s simple, explicit, and easy to test.

- `tablegen render --records <path> --spec <path> [--out <path>]`
  - Reads JSON (or JSONL) records + JSON spec
  - Writes the rendered table to stdout (and optionally `--out`)
  - Exits non-zero on schema errors

- `tablegen template [--out <path>]`
  - Emits a default spec template + minimal record example (as JSON)

Optional (nice-to-have):

- `tablegen validate --spec <path>`
- `tablegen normalize-records --in <path> --out <path>` (only if you find it necessary)

Determinism guarantees (same as before):

- Deterministic output given fixed `aggregate.uncertainty.seed`
- Idempotent
- Read-only

---

## Skill packaging (Codex / Claude Code)

Deliverables:

1) The Python package / scripts implementing the core logic + CLI.
2) A **skill file** (`SKILL.md`) that tells the agent:
   - how to serialize `records` + `spec` to JSON
   - which CLI command(s) to run
   - how to paste the resulting LaTeX/Markdown back into the paper/repo
   - what to do when schema validation fails (fix spec vs fix records)

Recommended repo layout:

```
table_generator/
  table_generator/          # Python package (core)
    __init__.py
    schema.py               # spec validation
    pipeline.py             # ingest->aggregate->pivot->highlight->format
    stats.py                # mean/median, std/sem, bootstrap CI
    render_latex.py
    render_markdown.py
  cli.py                    # `tablegen` entrypoint
  skills/
    table-generator/
      SKILL.md
      resources/
        spec_template.json
        records_example.json
        latex_preamble.md
  examples/
  tests/
```

The spec below remains the authoritative contract between the agent and the tool.

---

## Error handling principles

* Fail fast on schema violations
* Gracefully handle missing cells
* Never silently change user intent

Validation error contract (recommended):

- Error type: `SchemaError` or `ValueError`
- Message: human-readable
- Path: dotted spec path (e.g., `spec.aggregate.uncertainty.level`)

---

## Agent implementation guidance (Codex / Claude Code)

This section exists **explicitly to help a coding agent** implement the tool correctly and deterministically and deterministically.

### Schema discipline

* Treat the spec as authoritative; do not infer missing intent
* Validate enums eagerly and fail fast on invalid values
* Apply rename maps *before* ordering

### Data flow (must be followed in this order)

1. Ingest records → DataFrame
2. Apply renames
3. Filter metric
4. Group + aggregate
5. Compute uncertainty
6. Pivot to 2D table
7. Determine highlights (based on raw numeric center values)
8. Format numeric strings
9. Render backend (LaTeX or Markdown)

### Aggregation rules

* Aggregation happens only over `aggregate.over`
* Bootstrap resampling is over rows sharing identical row/col keys
* CI output must be deterministic given seed

### Highlighting rules

* Highlight comparisons use **center statistic only**
* Direction (`min`/`max`) must be respected
* Determine highlight ranks before formatting (use raw numeric center values), then apply highlight flags during rendering

### Rendering separation

* Statistical computation must be backend-agnostic
* Rendering functions must not recompute statistics

### Markdown-specific notes

* Use pipe-table format
* Align header separators correctly
* Degrade unsupported styles gracefully

### LaTeX-specific notes

* Always emit required packages
* Escape special characters unless explicitly disabled
* Prefer `booktabs` conventions

---

## Recommended implementation notes (for agents)

* Use pandas for grouping + pivoting
* Use NumPy for bootstrap
* Functional style preferred
* Keep rendering and statistics separate
* Avoid global state

---

## Installation & quickstart (local)

From the repo root:

```bash
python -m pip install -e .
```

Render a table:

```bash
tablegen render --records records.json --spec spec.json --out table.tex
```

Or render to stdout:

```bash
tablegen render --records records.json --spec spec.json
```

Generate a starter spec:

```bash
tablegen template --out spec_template.json
```

These commands are what the skill should instruct the agent to use.

---

## Possible future extensions

* Multi-level columns (Dataset → Metric)
* Paired statistical tests vs baseline
* siunitx column output
* Markdown / CSV output backends
* Automatic footnotes for CI definitions

---

## MVP checklist

Minimum viable demo should include:

* mean ± std
* bootstrap CI
* best / second-best highlighting
* booktabs LaTeX
* escaping

---

## Summary

`table_generator_mcp` encodes *paper logic* once and removes repetitive, error-prone table writing from the research loop. The spec-first design makes it ideal for tool usage and coding agents like Codex.


## Future extensions (sketch)

A future version may support tables combining multiple metrics by allowing:

- An array of metric specifications
- Per-metric aggregation, formatting, and highlighting rules
- Hierarchical column headers

This is intentionally deferred to preserve clarity in v1.
