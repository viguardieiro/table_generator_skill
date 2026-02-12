# Table Generator Spec Reference

This file provides the full spec reference for `table_generator`. If you are unsure about a field or allowed values, consult this file before proceeding.

## Required blocks

- `rows`
- `cols`
- `metric`
- `aggregate`

## Required fields

- `rows.field`
- `cols.field`
- `metric.field`
- `metric.value`
- `metric.direction` ("min" or "max")
- `aggregate.over` (non-empty list)

## Rows / Cols

```json
"rows": {
  "field": "model",
  "order": ["Baseline", "Ours"],
  "rename": {"baseline_v1": "Baseline"}
}
```

- `field`: record key to use for row/column labels
- `order`: explicit ordering; items not listed are appended in observed order
- `rename`: mapping applied before ordering

## Metric filtering

```json
"metric": {
  "field": "metric",
  "value": "acc",
  "direction": "max"
}
```

- `metric.field` and `metric.value` filter records; only matching records are included.
- `direction` controls best/second-best highlighting.

Per-column direction (for mixed metrics):
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

If you provide a direction map, include an entry for every column that will be highlighted or ordered.

**Multiple metrics as columns**

If you want multiple metrics as columns, store metric name in the column field and use a dummy `metric` value for filtering.

```json
{"method": "Baseline", "col": "Accuracy", "metric": "result", "seed": 0, "value": 0.85}
```

## Aggregation

```json
"aggregate": {
  "over": ["seed"],
  "stat": "mean",
  "uncertainty": {"type": "std"}
}
```

- `stat`: `"mean"` or `"median"`

### Uncertainty

Valid `aggregate.uncertainty.type` values:
- `"none"`
- `"std"`
- `"sem"`
- `"ci"`

For `"ci"`:
```json
"uncertainty": {
  "type": "ci",
  "method": "bootstrap_percentile",
  "level": 0.95,
  "n_boot": 1000,
  "seed": 0
}
```

- `level` is a fraction (0–1), not a percent
- `n_boot` must be a positive integer

## Formatting

```json
"format": {
  "mode": "pm",
  "mean_decimals": 2,
  "unc_decimals": 2,
  "trailing_zeros": true,
  "scientific": false,
  "missing": "--",
  "overrides": {
    "Loss": { "mean_decimals": 3, "unc_decimals": 3 }
  }
}
```

- `mode`: `"pm"` or `"ci_brackets"`
- `missing`: text for missing cells
- `overrides`: per-column formatting overrides

## Highlighting

```json
"highlight": {
  "scope": "column",
  "best": {"style": "bold"},
  "second": {"style": "underline"},
  "ties": "all"
}
```

- `scope`: `"column"`, `"row"`, or `"table"`
- `style`: `"bold"`, `"underline"`, or `"cellcolor:<color>"`
- `ties`: `"all"`, `"first"`, or `"none"`

## Output

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

- `format`: `"latex"` or `"markdown"`

## LaTeX

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

- `environment`: wrap in `table` environment
- `alignment`: column alignment string
- `escape`: escape LaTeX special chars if `true`
- `resize`: optional wrapper (e.g., `"\\resizebox{\\linewidth}{!}"`)

## Ordering by performance

```json
"rows": {
  "field": "model",
  "order_by": { "column": "MNLI", "direction": "max" }
}
```

- `order_by.column`: column label to sort by
- `order_by.direction`: optional; defaults to the metric direction for that column
