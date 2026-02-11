# table_generator skill

This repo is a **skill for agents** that generates publication-ready LaTeX or Markdown tables from experimental results. It is meant to be used by tools like Claude Code or Codex to summarize results for ML/AI papers.

## What the skill does

- Reads your results (JSON/JSONL)
- Creates or uses a declarative table spec
- Produces camera-ready LaTeX or Markdown tables
- Highlights best/second-best results

## What you can ask for

- Aggregations: mean or median, with uncertainty (std/sem/CI)
- Confidence intervals: bootstrap percentile CIs with a fixed seed
- Row/column ordering and renaming (explicit order or default order)
- Highlighting: best/second-best per row or per column
- Formatting: decimal precision for mean/uncertainty, `mean ± unc` or `mean [lo, hi]`
- Output format: LaTeX (booktabs-style) or Markdown (pipe tables)
- LaTeX details: alignment, table environment on/off, optional caption/label

## How to use with an agent (Claude Code / Codex)

1. Clone this repo on the machine running the agent.
2. Make sure the agent can read `skills/table-generator/SKILL.md`.
3. Install the package locally (editable install is fine).
4. In your agent UI, enable/select the **table-generator** skill.
5. Ask the agent to generate a table from your results.

Important: the agent must treat raw results as **read-only** and only write derived files (e.g., a new spec or cleaned copy).

## Skill files

- Skill instructions: `skills/table-generator/SKILL.md`
- Templates: `skills/table-generator/resources/`

## Example prompts

- "Generate a LaTeX table from `results.json` using the table-generator skill."
- "Create a spec for my results and render a Markdown table."

## If you want the package/CLI docs

See `table_generator/README.md`.
