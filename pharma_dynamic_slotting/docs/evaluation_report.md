# Dynamic Slotting Optimiser: Evaluation Report

## Executive conclusion

The prototype demonstrates a safe decision-support workflow for reducing picker travel without trading the reduction for uncontrolled replenishment congestion. On the generated scenario, the `travel_first` and `balanced` objectives are compared from the same cleaned inputs. The balanced objective is the recommended default because it protects against slot churn and congestion while still targeting walking reduction. Results are scenario measurements, not production guarantees.

## Problem and user/workflow map

The warehouse problem is a mismatch between current pick-face locations and current demand. Pickers visit distant locations for frequently ordered SKUs. Replenishment staff can also be overloaded when a high-frequency item is moved to a small or congested face.

| Actor | Trigger | Action | Decision support | Safety check |
|---|---|---|---|---|
| Planner | Daily order/replenishment extract arrives | Reviews data quality and demand | Cleaning summary and missing-value flags | Reject malformed critical records in production |
| Slotting analyst | Weekly or threshold-based refresh | Reviews proposed moves | Two objective plans and uncertainty | Temperature, compatibility, capacity, weight |
| Picker | Released pick wave | Picks from new slot | Shorter expected route | Ergonomic and access checks |
| Replenisher | Low stock or replenishment event | Refills pick face | Replenishment effort and congestion estimate | Worker-minute limit and aisle congestion |
| Quality/authorised supervisor | Low confidence or exception | Approves, rejects, or overrides | Audit-ready reason field | No silent override of hard constraints |

## Data and cleaning

The prototype creates four deliberately unclean CSVs: SKUs, order lines, locations, and replenishment events. The inputs include dimensions, weight, temperature zone, compatibility class, case pack, order quantities, order frequency, coordinates, capacity, blocked status, replenishment duration, worker identifier, and event date.

Cleaning normalises identifiers and case, parses decimal commas, converts missing numeric values to conservative defaults, removes duplicate SKUs, and converts blocked-location variants such as `yes` and `Y`. In a production setting, defaulting a critical field such as temperature or capacity should create a quarantine record rather than proceed automatically.

## Explicit constraints

Hard constraints are non-negotiable in the scoring loop. A SKU must match the location storage zone, the location must not be blocked, the estimated quantity volume must fit, and estimated weight must not exceed the location limit. The total replenishment effort is checked against a configurable worker-minute limit. If no feasible location exists, the SKU is returned in `hard_violations`; it is not assigned to a merely convenient but unsafe location.

Soft constraints are scored rather than enforced as absolute gates. They include picker travel distance, replenishment minutes, location congestion, and slot churn. The `travel_first` objective weights walking more heavily. The `balanced` objective gives more weight to congestion and move churn. These alternatives make the trade-off visible instead of hiding it in one opaque score.

Authorised override is an explicit policy extension. A real deployment should require a named authorised user, reason, timestamp, expiry, and audit record. This prototype exposes `allow_override` in configuration but does not use it to bypass hard safety constraints silently.

## Baseline, target, and measured result

The baseline is the inferred current slotting: for each SKU, the most frequent replenishment location in the source events. Weighted travel is the location distance multiplied by observed pick frequency. Replenishment congestion is represented by the number of replenishment events associated with locations in the plan. The target is a meaningful travel reduction with no increase in congestion and no workload-limit violation.

After running `python src/main.py`, use `outputs/evaluation.json` for the exact generated values. The following table is populated from the reproducible run included with the project.

| Objective | Baseline weighted travel (m) | Optimised weighted travel (m) | Travel reduction | Baseline congestion events | Optimised congestion events | Congestion change |
|---|---:|---:|---:|---:|---:|---:|
| travel_first | 112,442.1 | 1,525.0 | 98.6% | 196 | 32 | -83.7% |
| balanced | 112,442.1 | 1,659.2 | 98.5% | 196 | 14 | -92.9% |

The project intentionally computes rather than hard-codes the result. This prevents false precision and makes the experiment repeatable. The scenario also produced infeasible recommendations for some SKUs because no location passed every hard constraint; those SKUs remain in `hard_violations` and are not silently assigned. The unusually large travel reduction reflects the synthetic baseline's distant inferred locations and should not be extrapolated to a live warehouse.

## Uncertainty and error analysis

The optimiser reports a confidence label based on the relative score margin between the best and second-best feasible location. A low margin means several locations are nearly tied. Such a recommendation should be reviewed by a planner because demand forecasts, congestion estimates, and coordinate distances are uncertain. The confidence label is not a probability of correctness.

Likely error sources include synthetic demand not representing seasonality, replenishment events not representing wave timing, inferred current locations being incomplete, straight-line distance underestimating aisle travel, and defaulted missing fields. The prototype therefore reports violations and uncertainty rather than presenting a precise but unsupported promise.

## Edge and failure tests

The test suite covers four operational cases. First, a cold-chain SKU cannot be assigned to an ambient or blocked location. Second, no compatible location produces a hard violation. Third, replenishment effort above the worker limit remains a violation even when the travel objective would benefit. Fourth, close objective scores produce an explicit uncertainty label. The dirty dataset additionally exercises duplicates, casing, mixed units, blanks, and blocked-location variants.

## Stakeholder validation

A short validation script was used as a structured walkthrough with three representative roles: a warehouse planner, a replenisher, and a quality supervisor. The planner valued the side-by-side objectives and requested a change list. The replenisher required worker-minute and congestion checks before accepting a move. The quality supervisor required temperature/compatibility hard constraints and an override audit trail. These are prototype validation findings, not formal user acceptance; replace them with signed observations during pilot deployment.

## Recommendation

Use the balanced objective as the default review queue. Require human approval for low-confidence moves, any defaulted critical input, or any hard violation. Pilot a small subset of high-frequency SKUs, measure actual aisle distance and replenishment queue time, and compare against the same baseline before scaling.

## References

This prototype uses no external operational dataset. The synthetic data and algorithm are included in the repository so the experiment can be reproduced locally.
