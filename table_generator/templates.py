"""Default spec and records templates."""

DEFAULT_SPEC = {
    "rows": {"field": "model", "order": ["Baseline", "Ours"]},
    "cols": {"field": "dataset", "order": ["MNLI", "SST2"]},
    "metric": {"field": "metric", "value": "acc", "direction": "max"},
    "aggregate": {
        "over": ["seed"],
        "stat": "mean",
        "uncertainty": {"type": "std"},
    },
    "format": {"mode": "pm", "mean_decimals": 2, "unc_decimals": 2},
    "highlight": {
        "scope": "column",
        "best": {"style": "bold"},
        "second": {"style": "underline"},
    },
    "output": {"format": "latex"},
}

DEFAULT_RECORDS = [
    {"model": "Baseline", "dataset": "MNLI", "metric": "acc", "seed": 0, "value": 84.1},
    {"model": "Baseline", "dataset": "MNLI", "metric": "acc", "seed": 1, "value": 84.3},
    {"model": "Baseline", "dataset": "MNLI", "metric": "acc", "seed": 2, "value": 84.5},
    {"model": "Ours", "dataset": "MNLI", "metric": "acc", "seed": 0, "value": 85.0},
    {"model": "Ours", "dataset": "MNLI", "metric": "acc", "seed": 1, "value": 85.2},
    {"model": "Ours", "dataset": "MNLI", "metric": "acc", "seed": 2, "value": 85.4},
]
