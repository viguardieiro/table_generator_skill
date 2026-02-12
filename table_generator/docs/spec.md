# Table Generator Spec Reference

This document defines every spec field, its expected value type, and defaults. Use this as the authoritative reference.

## Required blocks

- `rows`
- `cols`
- `metric`
- `aggregate`

## Required fields

- `rows.field` (string)
- `cols.field` (string)
- `metric.field` (string)
- `metric.value` (string)
- `metric.direction` ("min" or "max", or a per-column map)
- `aggregate.over` (non-empty list of strings)

## `rows`

Example:
```json
"rows": {
  "field": "model",
  "order": ["Baseline", "Ours"],
  "rename": {"baseline_v1": "Baseline"},
  "order_by": {"column": "MNLI", "direction": "max"}
}
```

Fields:
- `field` (string, required): record key used for row labels.
- `order` (list[string], optional, default: none): explicit row order. Items not listed are appended in observed order.
- `rename` (object, optional, default: none): mapping applied before ordering.
- `order_by` (object, optional, default: none): sort rows by a column value.
- `groups` (list[object], optional, default: none): row grouping with header rows.

`order_by` fields:
- `column` (string, required): column label to sort by.
- `direction` (string, optional, default: `metric.direction` for that column): `"min"` or `"max"`.

Behavior:
- Missing values in `order_by.column` are sorted last.
- If `order` is provided, ordering is applied first and then `order_by` is applied to the resulting rows.

`groups` fields:
- `label` (string, required): group header label.
- `members` (list[string], required): row labels in the group.
- `separator` (string, optional, default: none): `\"midrule\"`, `\"hline\"`, or `\"none\"` (LaTeX only). Markdown inserts a blank line.

Grouping rules:
- Each row may appear in at most one group.
- All members must exist in final row labels.
- Members must be contiguous in the final row order; otherwise the spec is invalid.
- Rows not listed in any group are rendered outside groups.

## `cols`

Example:
```json
"cols": {
  "field": "dataset",
  "order": ["MNLI", "SST2"],
  "rename": {"sst-2": "SST2"}
}
```

Fields:
- `field` (string, required): record key used for column labels.
- `order` (list[string], optional, default: none): explicit column order. Items not listed are appended in observed order.
- `rename` (object, optional, default: none): mapping applied before ordering.
- `groups` (list[object], optional, default: none): column grouping with multi-level headers.

`groups` fields:
- `label` (string, required): column group label.
- `members` (list[string], required): column labels in the group.
- `cmidrule` (bool, optional, default: `true`): draw `\\cmidrule` under the group (LaTeX only).

Grouping rules:
- Each column may appear in at most one group.
- All members must exist in final column labels.
- Members must be contiguous in the final column order; otherwise the spec is invalid.
- Columns not listed in any group appear ungrouped.

## `metric`

Example:
```json
"metric": {
  "field": "metric",
  "value": "acc",
  "direction": "max"
}
```

Fields:
- `field` (string, required): record key containing metric name.
- `value` (string, required): only records with `record[field] == value` are included.
- `direction` (string or object, required):
  - string: `"min"` or `"max"` for a single direction.
  - object: per-column direction map.

Per-column direction example:
```json
"metric": {
  "field": "metric",
  "value": "result",
  "direction": {
    "Accuracy": "max",
    "Loss": "min"
  }
}
```

Rules:
- If you provide a direction map, include an entry for every column that will be highlighted or ordered.
- Row-scope highlighting does not support per-column directions.
- Table-scope highlighting requires a single direction.

Multiple metrics as columns:
- Store the metric name in the column field and use a dummy `metric.value` for filtering.

Example record:
```json
{"method": "Baseline", "col": "Accuracy", "metric": "result", "seed": 0, "value": 0.85}
```

## `aggregate`

Example:
```json
"aggregate": {
  "over": ["seed"],
  "stat": "mean",
  "uncertainty": {"type": "std"}
}
```

Fields:
- `over` (list[string], required): record keys to aggregate over.
- `stat` (string, optional, default: `"mean"`): `"mean"` or `"median"`.
- `uncertainty` (object, optional, default: `{ "type": "none" }`).

### `aggregate.uncertainty`

Fields:
- `type` (string, optional, default: `"none"`): `"none"`, `"std"`, `"sem"`, or `"ci"`.

If `type` is `"ci"`, add:
- `method` (string, optional, default: `"bootstrap_percentile"`)
- `level` (float, optional, default: `0.95`): fraction between 0 and 1.
- `n_boot` (int, optional, default: `1000`)
- `seed` (int, optional, default: `0`)

### `aggregate.row_summary` / `aggregate.col_summary`

Add a summary column (per row) or summary row (per column).

```json
"aggregate": {
  "row_summary": { "label": "Mean", "stat": "mean", "position": "end" },
  "col_summary": { "label": "Mean", "stat": "mean", "position": "end" }
}
```

Fields:
- `label` (string, required): label for the summary row/column.
- `stat` (string, optional, default: `"mean"`): `"mean"` or `"median"`.
- `position` (string, optional, default: `"end"`): `"start"` or `"end"`.

Behavior:
- Summaries are computed over available center values (not raw seeds).
- Uncertainty is not shown for summary cells.

## `format`

Example:
```json
"format": {
  "mode": "pm",
  "mean_decimals": 2,
  "unc_decimals": 2,
  "trailing_zeros": true,
  "scientific": false,
  "missing": "--",
  "overrides": {
    "Loss": {"mean_decimals": 3, "unc_decimals": 3}
  }
}
```

Fields:
- `mode` (string, optional, default: `"pm"`): `"pm"` or `"ci_brackets"`.
- `mean_decimals` (int, optional, default: `2`)
- `unc_decimals` (int, optional, default: `2`)
- `trailing_zeros` (bool, optional, default: `true`)
- `scientific` (bool, optional, default: `false`)
- `missing` (string, optional, default: `"--"`)
- `overrides` (object, optional, default: none): per-column format overrides. Keys are column labels.

## `highlight`

Example:
```json
"highlight": {
  "scope": "column",
  "best": {"style": "bold"},
  "second": {"style": "underline"},
  "ties": "all"
}
```

Fields:
- `scope` (string, optional, default: `"column"`): `"column"`, `"row"`, or `"table"`.
- `best.style` (string, optional, default: none): `"bold"`, `"underline"`, or `"cellcolor:<color>"`.
- `second.style` (string, optional, default: none): same as `best.style`.
- `ties` (string, optional, default: `"all"`): `"all"`, `"first"`, or `"none"`.

Behavior:
- `ties=all`: highlight all tied values and skip second-best when best ties exist.
- `ties=first`: highlight first occurrence only.
- `ties=none`: if there is a tie for best or second-best, skip highlighting for that rank.

## `delta`

Add delta (difference) columns vs a baseline row.

```json
"delta": {
  "baseline": "Baseline",
  "mode": "absolute",
  "position": "after",
  "suffix": " Δ",
  "use_direction": true,
  "columns": ["acc", "f1", "loss"],
  "format": { "decimals": 3, "show_plus": true, "percent": false }
}
```

Fields:
- `baseline` (string, required): row label to compare against.
- `mode` (string, optional, default: `"absolute"`): `"absolute"` or `"relative"`.
- `position` (string, optional, default: `"after"`): `"after"` (insert after each column) or `"end"` (append at end).
- `suffix` (string, optional, default: `" Δ"`): appended to column label.
- `use_direction` (bool, optional, default: `true`): if `true`, deltas are flipped so “better” is positive.
- `columns` (list[string], optional): subset of columns to create deltas for. If omitted, all columns.
- `format` (object, optional): formatting for delta cells.

`delta.format` fields:
- `decimals` (int, optional, default: `format.mean_decimals`).
- `show_plus` (bool, optional, default: `true`).
- `percent` (bool, optional, default: `mode == "relative"`).

Behavior:
- Delta cells do not show uncertainty.
- Summary rows/cols and highlighting ignore delta columns.
- If column groups are defined and `position="after"`, delta columns are inserted into the same group.

## `significance`

Add significance markers relative to a baseline row (per column).

```json
"significance": {
  "baseline": "Baseline",
  "scope": "column",
  "method": "bootstrap_ci",
  "level": 0.95,
  "n_boot": 1000,
  "seed": 0,
  "symbol": "*"
}
```

Fields:
- `baseline` (string, required): row label to compare against.
- `scope` (string, optional, default: `"column"`): only `"column"` supported.
- `method` (string, optional, default: `"bootstrap_ci"`): only `"bootstrap_ci"` supported.
- `level` (float, optional, default: `0.95`): CI level in (0,1).
- `n_boot` (int, optional, default: `1000`).
- `seed` (int, optional, default: `0`).
- `symbol` (string, optional, default: `"*"`): marker appended to significant cells.

Behavior:
- Uses bootstrap CI on difference in means vs baseline.
- For `metric.direction="min"`, the sign is flipped so “better” is positive.

## `output`

Example:
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

Fields:
- `format` (string, optional, default: `"latex"`): `"latex"` or `"markdown"`.
- `markdown` (object, optional, default shown above).

`output.markdown` fields:
- `include_caption` (bool, optional, default: `true`): if `true`, uses `latex.caption` as the caption text.
- `alignment` (string, optional, default: `"auto"`): `"auto"`, `"left"`, `"center"`, `"right"`.
- `separator` (string, optional, default: `"|"`)
- `bold` (string, optional, default: `"**"`)
- `underline` (string, optional, default: `"_"`)

## `latex`

Example:
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

Fields:
- `environment` (bool, optional, default: `true`): wrap in `table` environment.
- `booktabs` (bool, optional, default: `true`): use `\\toprule`/`\\midrule`/`\\bottomrule`.
- `tabular` (string, optional, default: `"tabular"`): `"tabular"` or `"tabularx"`.
- `alignment` (string, optional, default: auto): alignment string; if omitted, uses `l` + `c` for each column.
- `caption` (string, optional, default: none)
- `label` (string, optional, default: none)
- `escape` (bool, optional, default: `true`)
- `resize` (string or null, optional, default: `null`): wrapper such as `"\\resizebox{\\linewidth}{!}"`.
