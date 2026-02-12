# Examples

## 1) Single metric, per-column highlighting

```json
{
  "rows": { "field": "model" },
  "cols": { "field": "dataset" },
  "metric": { "field": "metric", "value": "acc", "direction": "max" },
  "aggregate": { "over": ["seed"], "stat": "mean", "uncertainty": { "type": "std" } },
  "format": { "mode": "pm", "mean_decimals": 2, "unc_decimals": 2 },
  "highlight": { "scope": "column", "best": { "style": "bold" }, "second": { "style": "underline" } },
  "output": { "format": "latex" }
}
```

## 2) Mixed metric directions (accuracy vs loss)

```json
{
  "rows": { "field": "model" },
  "cols": { "field": "metric_name" },
  "metric": {
    "field": "metric",
    "value": "result",
    "direction": {
      "Accuracy": "max",
      "Loss": "min"
    }
  },
  "aggregate": { "over": ["seed"], "stat": "mean", "uncertainty": { "type": "std" } },
  "format": {
    "mode": "pm",
    "mean_decimals": 2,
    "unc_decimals": 2,
    "overrides": { "Loss": { "mean_decimals": 3, "unc_decimals": 3 } }
  },
  "highlight": { "scope": "column", "best": { "style": "bold" } },
  "output": { "format": "latex" }
}
```

## 3) Order rows by performance

```json
{
  "rows": {
    "field": "model",
    "order_by": { "column": "MNLI", "direction": "max" }
  },
  "cols": { "field": "dataset" },
  "metric": { "field": "metric", "value": "acc", "direction": "max" },
  "aggregate": { "over": ["seed"], "stat": "mean", "uncertainty": { "type": "std" } },
  "format": { "mode": "pm", "mean_decimals": 2, "unc_decimals": 2 },
  "output": { "format": "markdown" }
}
```

## 4) Column and row groups

```json
{
  "rows": {
    "field": "model",
    "order": ["Base", "Base+Aug", "Large", "Large+Aug"],
    "groups": [
      { "label": "Base models", "members": ["Base", "Base+Aug"], "separator": "midrule" },
      { "label": "Large models", "members": ["Large", "Large+Aug"], "separator": "midrule" }
    ]
  },
  "cols": {
    "field": "metric",
    "order": ["Accuracy", "F1", "Loss"],
    "groups": [
      { "label": "Scores", "members": ["Accuracy", "F1"], "cmidrule": true },
      { "label": "Loss", "members": ["Loss"], "cmidrule": true }
    ]
  },
  "metric": { "field": "metric_filter", "value": "result", "direction": {
    "Accuracy": "max",
    "F1": "max",
    "Loss": "min"
  }},
  "aggregate": { "over": ["seed"], "stat": "mean", "uncertainty": { "type": "std" } },
  "format": { "mode": "pm", "mean_decimals": 2, "unc_decimals": 2 },
  "output": { "format": "latex" }
}
```
