# Dynamic Slotting Optimiser: Robustness and Safety Validation Report

## Executive conclusion

The original prototype reported a **98.6% travel reduction**. This revision tests whether that result was robust to the baseline definition and whether it was achieved by under-penalising replenishment congestion. The validation shows that the original percentage was not a safe headline metric for the current scoring design. After adding an explicit convex replenishment-congestion penalty and retaining the same cleaned inputs, the measured travel reduction is **77.5% for `travel_first`** and **77.0% for `balanced`**. Both alternatives reduce replenishment congestion, and the reduction remains positive under a neutral same-zone baseline and 200 bootstrap resamples of replenishment history.

This is a more defensible result. It is lower than 98.6%, but it is less likely to be inflated by an artificially distant inferred baseline or by a plan that ignores replenishment workload.

## Mathematical formulation of travel distance

Each storage location `l` has coordinates `(x_l, y_l)` in metres. The depot or route-origin reference is `(x_0, y_0)`. The prototype uses the following straight-line distance proxy:

> `d_l = sqrt((x_l - x_0)^2 + (y_l - y_0)^2)`

For SKU `i`, let `f_i` be observed pick frequency and `a(i)` be its assigned location. The frequency-weighted travel metric is:

> `T = sum_i f_i * d_(a(i))`

For a candidate plan `P` and baseline `B`, the percentage reduction is:

> `R(P,B) = 100 * (T_B - T_P) / max(T_B, epsilon)`

where `epsilon = 1e-9` avoids division by zero. Frequencies act as weights. They do not create extra physical route points. This prevents high-frequency SKUs from being treated as if they were separate locations.

The metric is a proxy, not a route-optimal path length. A production validation should replace it with aisle-network distance or actual scanner/GPS path distance. Because the prototype uses a common coordinate system and the same frequency weights for the baseline and candidate, the comparison is internally consistent even though it is not a full route simulation.

## Baseline sensitivity and anti-distortion validation

The observed baseline infers each SKU's current slot as the most frequent replenishment location for that SKU. This is operationally plausible, but it can be distorted if replenishment history is sparse or if a SKU was temporarily placed far from the depot. Therefore, the prototype now reports three checks.

| Check | Definition | Result |
|---|---|---:|
| Observed replenishment baseline | Most frequent replenishment location per SKU | 77.45% reduction |
| Neutral same-zone counterfactual | Median distance among feasible, unblocked locations in the SKU's zone | 76.96% reduction |
| Bootstrap baseline sensitivity | 200 resamples of replenishment events, re-inferring the baseline each time | 5th percentile 72.04%; median 77.18%; 95th percentile 80.19% |

The 98.6% value from the prior version is therefore not retained as the validated headline. The new result remains positive across the neutral counterfactual and the bootstrap interval. The sensitivity test is not causal proof. It only reduces the risk that one arbitrary baseline reconstruction explains the result.

The exact machine-readable output is `outputs/travel_robustness.json`. The validator can be rerun with:

```bash
python src/validate_travel.py
```

## Replenishment congestion penalty

Let `n_l` be the current or projected number of replenishment events at location `l` in the planning window. Let `s` be a soft congestion limit and `h` be a hard operational limit. The prototype implements:

> `P_l(n_l) = infinity, if n_l > h`
>
> `P_l(n_l) = w * max(0, n_l - s)^2, otherwise`

The default values are `s = 3`, `h = 30`, and `w = 0.8` for the balanced objective. The penalty is zero up to the soft limit. It grows quadratically after the soft limit, so a location with 10 events is more than proportionally less attractive than a location with 5 events. The infinite value is implemented as candidate rejection, which stops a soft objective from trading away an operational hard limit.

For `travel_first`, the penalty is retained with a smaller coefficient so travel remains the primary objective. For `balanced`, the full penalty weight is applied together with replenishment minutes and move churn. The scoring terms are:

> `Score_travel = d_l + 0.10 * sku_replenishment_events + 0.01 * P_l + 2 * move`
>
> `Score_balanced = 0.65 * d_l + 0.05 * sku_replenishment_minutes + P_l + 4 * move`

These coefficients are policy parameters, not learned truths. A live deployment should calibrate them against actual walking time, replenishment queue time, and change-control cost.

## Baseline, target, and corrected measured result

The experiment uses 30 cleaned SKUs, 1,717 order lines, 36 locations, and 300 replenishment events. The target is to reduce frequency-weighted travel without increasing replenishment congestion or violating safety/workload constraints.

| Objective | Baseline travel | Optimised travel | Travel reduction | Baseline congestion events | Optimised congestion events | Congestion change |
|---|---:|---:|---:|---:|---:|---:|
| travel_first | 112,442.1 m | 25,351.6 m | 77.5% | 196 | 68 | -65.3% |
| balanced | 112,442.1 m | 25,878.0 m | 77.0% | 196 | 61 | -68.9% |

The reported values are generated by `src/main.py` and stored in `outputs/evaluation.json`. Some SKUs may remain in `hard_violations` when no feasible location exists. They are not silently assigned to an unsafe location.

## Explicit safety and operational failure cases

The test suite now includes 19 passing tests. In addition to the original zone, blocked-location, workload, and uncertainty tests, it covers the following failure cases:

| Failure case | Expected behaviour |
|---|---|
| Sudden temperature excursion | Candidate location is rejected as a hard failure |
| Current temperature outside SKU range | Candidate location is rejected |
| Hazardous SKU in a cross-contamination-risk location | Candidate location is rejected |
| Hazardous SKU in a standard location | Candidate location is rejected |
| Item volume exceeds location capacity | Candidate location is rejected |
| Item volume exceeds remaining zone capacity | Candidate location is rejected |
| Replenishment events exceed hard congestion limit | Candidate receives infinite penalty and is rejected |
| High replenishment minutes exceed worker limit | Workload violation is surfaced, not traded away |

The tests live in `tests/test_safety_and_robustness.py` and `tests/test_optimizer.py`. Run them with:

```bash
python -m pytest -q
```

## Uncertainty and interpretation limits

A recommendation's confidence is based on the relative score margin between the best and second-best feasible locations. A low margin means the alternatives are nearly tied. It is not a probability of correctness. The bootstrap interval describes sensitivity to replenishment-history sampling; it is not a confidence interval for future warehouse performance.

The straight-line proxy can understate actual walking because aisles, one-way routes, doors, lifts, and restricted areas are not represented. Synthetic demand does not represent seasonality. Replenishment records may not capture wave timing. Missing critical fields should be quarantined in a production pipeline rather than defaulted automatically.

## Recommendation

Use the balanced objective as the default review queue. Use the corrected 77.5% result, not the original 98.6%, as the current scenario measurement. Before any live release, replace straight-line distance with aisle-network distance, collect actual replenishment queue time, validate temperature and hazardous-material segregation with Quality, and run a controlled pilot with signed change control.

## References

This prototype uses no external operational dataset. The synthetic data, formulas, implementation, and validation tests are included in the repository so the experiment can be reproduced locally.
