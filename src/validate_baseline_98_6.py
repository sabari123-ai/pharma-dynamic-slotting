"""Additive robustness validation for the legacy 98.6% travel-delta claim.

This module deliberately does NOT modify the existing optimizer, main pipeline,
or published output metrics.  It treats 98.6% as a legacy/reference claim and
checks whether the current cleaned data can reproduce it under multiple baseline
constructions.

Formulation
------------
For location l and depot (x0, y0):
    d_l = sqrt((x_l-x0)^2 + (y_l-y0)^2)

For SKU i assigned to location a(i), with pick frequency f_i:
    T = sum_i f_i * d_{a(i)}

Travel delta:
    Delta% = 100 * (T_baseline - T_candidate) / T_baseline

Robustness checks:
1. Observed replenishment baseline (the repository's existing baseline logic).
2. Neutral same-zone median-distance counterfactual.
3. Bootstrap resampling of replenishment history.

The 98.6% value is retained as a reference claim.  It is not silently
substituted for the measured result and is not asserted as validated unless the
current inputs reproduce it.
"""
from __future__ import annotations

import json
import random
import statistics
from collections import Counter
from pathlib import Path

from optimizer import Config, load_clean, build_plan, travel_distance, weighted_travel

ROOT = Path(__file__).resolve().parents[1]
LEGACY_REFERENCE_DELTA_PCT = 98.6


def infer_locations(skus, reps):
    inferred = {}
    for sku in skus:
        locations = [r["location_id"] for r in reps if r["sku_id"] == sku["sku_id"]]
        if locations:
            inferred[sku["sku_id"]] = Counter(locations).most_common(1)[0][0]
    return inferred


def demand_counts(orders):
    counts = Counter()
    for order in orders:
        counts[order["sku_id"]] += 1
    return counts


def observed_baseline(skus, orders, locs, reps):
    by_location = {x["location_id"]: x for x in locs}
    inferred = infer_locations(skus, reps)
    demand = demand_counts(orders)
    return [
        {
            "sku_id": sku_id,
            "location_id": location_id,
            "pick_frequency": demand[sku_id],
            "travel_m": travel_distance(by_location[location_id]),
        }
        for sku_id, location_id in inferred.items()
        if location_id in by_location
    ]


def neutral_same_zone_baseline(skus, orders, locs):
    demand = demand_counts(orders)
    rows = []
    for sku in skus:
        if sku["sku_id"] not in demand:
            continue
        candidates = [
            loc for loc in locs
            if loc["zone"] == sku["zone"] and not loc["blocked"]
        ]
        if not candidates:
            continue
        distances = sorted(travel_distance(loc) for loc in candidates)
        rows.append(
            {
                "sku_id": sku["sku_id"],
                "location_id": "ZONE_MEDIAN",
                "pick_frequency": demand[sku["sku_id"]],
                "travel_m": statistics.median(distances),
            }
        )
    return rows


def reduction_pct(baseline, candidate):
    baseline_travel = weighted_travel(baseline, "travel_m", "pick_frequency")
    candidate_travel = weighted_travel(candidate, "estimated_travel_m", "pick_frequency")
    return 100.0 * (baseline_travel - candidate_travel) / max(1e-9, baseline_travel)


def bootstrap_reduction(skus, orders, locs, reps, candidate, iterations=200, seed=11):
    rng = random.Random(seed)
    values = []
    for _ in range(iterations):
        sample = [rng.choice(reps) for _ in reps]
        baseline = observed_baseline(skus, orders, locs, sample)
        if baseline:
            values.append(reduction_pct(baseline, candidate))
    values.sort()
    if not values:
        return {"iterations": 0}
    return {
        "iterations": len(values),
        "p05_reduction_pct": round(values[int(0.05 * (len(values) - 1))], 2),
        "median_reduction_pct": round(statistics.median(values), 2),
        "p95_reduction_pct": round(values[int(0.95 * (len(values) - 1))], 2),
        "min_reduction_pct": round(min(values), 2),
        "max_reduction_pct": round(max(values), 2),
    }


def validate():
    skus, orders, locs, reps = load_clean(ROOT)
    plan = build_plan(skus, orders, locs, reps, Config(objective="travel_first"))["plan"]

    observed = observed_baseline(skus, orders, locs, reps)
    neutral = neutral_same_zone_baseline(skus, orders, locs)
    observed_delta = reduction_pct(observed, plan)
    neutral_delta = reduction_pct(neutral, plan)
    bootstrap = bootstrap_reduction(skus, orders, locs, reps, plan)

    # This is deliberately a separate reference check. It does not overwrite
    # the 98.6% claim and does not alter the existing evaluation.json output.
    result = {
        "legacy_reference_delta_pct": LEGACY_REFERENCE_DELTA_PCT,
        "formula": {
            "location_distance": "d_l = sqrt((x_l-x_0)^2 + (y_l-y_0)^2)",
            "weighted_travel": "T = sum_i f_i * d_{a(i)}",
            "travel_delta": "Delta% = 100 * (T_baseline - T_candidate) / T_baseline",
        },
        "current_validation": {
            "observed_replenishment_baseline_pct": round(observed_delta, 2),
            "neutral_same_zone_median_pct": round(neutral_delta, 2),
            "bootstrap": bootstrap,
        },
        "legacy_reference_reproduced_by_current_observed_baseline": abs(observed_delta - LEGACY_REFERENCE_DELTA_PCT) < 0.05,
        "legacy_reference_reproduced_by_current_neutral_baseline": abs(neutral_delta - LEGACY_REFERENCE_DELTA_PCT) < 0.05,
        "interpretation": (
            "98.6% is retained as the legacy/reference delta. The current cleaned "
            "inputs validate robustness by checking observed, neutral same-zone, "
            "and bootstrap baselines. A reference value is considered robust only "
            "if it is reproduced across these baseline constructions; otherwise "
            "the validator flags baseline sensitivity without changing the legacy claim."
        ),
    }
    out = ROOT / "outputs" / "baseline_98_6_robustness.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    validate()
