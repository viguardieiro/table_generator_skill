"""Statistical helpers."""

from __future__ import annotations

import math
import random
from typing import Callable, List, Tuple


def mean(values: List[float]) -> float:
    return sum(values) / len(values)


def median(values: List[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return ordered[mid]
    return 0.5 * (ordered[mid - 1] + ordered[mid])


def std(values: List[float]) -> float:
    n = len(values)
    if n <= 1:
        return 0.0
    mu = mean(values)
    var = sum((x - mu) ** 2 for x in values) / (n - 1)
    return math.sqrt(var)


def sem(values: List[float]) -> float:
    n = len(values)
    if n <= 1:
        return 0.0
    return std(values) / math.sqrt(n)


def bootstrap_percentile(
    values: List[float],
    stat_fn: Callable[[List[float]], float],
    level: float,
    n_boot: int,
    seed: int,
) -> Tuple[float, float]:
    rng = random.Random(seed)
    n = len(values)
    if n == 0:
        return (float("nan"), float("nan"))
    stats = []
    for _ in range(n_boot):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        stats.append(stat_fn(sample))
    stats.sort()
    alpha = (1.0 - level) / 2.0
    lo_idx = int(math.floor(alpha * (n_boot - 1)))
    hi_idx = int(math.ceil((1.0 - alpha) * (n_boot - 1)))
    return (stats[lo_idx], stats[hi_idx])


def bootstrap_diff_ci(
    values_a: List[float],
    values_b: List[float],
    stat_fn: Callable[[List[float]], float],
    level: float,
    n_boot: int,
    seed: int,
) -> Tuple[float, float]:
    rng = random.Random(seed)
    n_a = len(values_a)
    n_b = len(values_b)
    if n_a == 0 or n_b == 0:
        return (float("nan"), float("nan"))
    diffs = []
    for _ in range(n_boot):
        sample_a = [values_a[rng.randrange(n_a)] for _ in range(n_a)]
        sample_b = [values_b[rng.randrange(n_b)] for _ in range(n_b)]
        diffs.append(stat_fn(sample_a) - stat_fn(sample_b))
    diffs.sort()
    alpha = (1.0 - level) / 2.0
    lo_idx = int(math.floor(alpha * (n_boot - 1)))
    hi_idx = int(math.ceil((1.0 - alpha) * (n_boot - 1)))
    return (diffs[lo_idx], diffs[hi_idx])
