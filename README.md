# table_generator skill

This repo is a **skill for agents** that generates publication-ready LaTeX or Markdown tables from experimental results. It is meant to be used by tools like Claude Code or Codex to summarize results for ML/AI papers.

## What the skill does

- Reads your results (JSON/JSONL/CSV and other tabular formats once converted to records)
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
2. From the repo root (`table_generator_skill`), install the package locally:
   - `pip install -e .` (editable install; changes to the code take effect without reinstalling)
3. Point your agent to the skill file:
   - Claude Code UI: add the skill from `skills/table-generator/SKILL.md`
   - Claude Code CLI: `claude code --skill /path/to/table_generator_skill/skills/table-generator/SKILL.md`
   - Codex CLI: `codex --skill /path/to/table_generator_skill/skills/table-generator/SKILL.md`
4. Ask the agent to generate a table from your results.

Important: the agent is instructed to treat raw results as **read-only** and only write derived files (e.g., a new spec or cleaned copy). It is still a good idea to keep backups of your results; you are responsible for protecting your data.

## Skill files

- Skill instructions: `skills/table-generator/SKILL.md`
- Templates: `skills/table-generator/resources/`

## Example prompts

- "Generate a LaTeX table from `results.json` using the table-generator skill."
- "Create a spec for my results and render a Markdown table."

## Potential next features

- Multiple metrics per table (single spec, adjacent metric columns)
- Delta vs baseline columns
- Per-column sorting (auto-sort by a chosen column)
- Row/column filtering by regex or allowlist
- Auto-generated footnotes/notes (e.g., “mean ± std over 5 seeds”)
- Regex or partial-match renaming rules

## If you want the package/CLI docs

See `table_generator/README.md`.
