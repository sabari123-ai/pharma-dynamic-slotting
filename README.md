# Pharmaceutical Dynamic Slotting Optimiser

This repository is an end-to-end prototype for a pharmaceutical warehouse with ambient, cold-chain, and controlled-storage zones. It addresses unnecessary picker travel caused by slotting no longer matching demand. The prototype cleans deliberately unclean synthetic source data, computes demand and replenishment features, proposes slots under safety constraints, compares two objectives, reports uncertainty, and exports measurable results.

## Run in VS Code

1. Open this folder in VS Code.
2. Run `python src/generate_data.py`.
3. Run `python src/main.py`.
4. Run `python -m pytest -q`.
5. Run `python src/validate_travel.py` to validate baseline sensitivity.
6. Open `outputs/evaluation.json`, `outputs/travel_robustness.json`, `outputs/plan_travel_first.csv`, `outputs/plan_balanced.csv`, and `docs/evaluation_report.md`.
7. To create the demo video after installing FFmpeg, run `python src/demo_video.py`.

The project uses only the Python standard library for the optimiser and data pipeline. Python 3.10+ is recommended. Pytest and FFmpeg are optional for tests and video creation.

## What is included

| Area | Implementation |
|---|---|
| Inputs | SKU dimensions, temperature/compatibility class, order lines, pick frequency, locations, replenishment events |
| Data quality | Case/whitespace normalisation, mixed decimal parsing, missing-value defaults, duplicate SKU removal, blocked-location parsing |
| Hard constraints | Storage-zone compatibility, blocked locations, capacity, maximum weight, worker workload limit, no silent fallback |
| Soft constraints | Picker travel, replenishment effort, convex replenishment congestion penalty, slot churn |
| Objectives | `travel_first` prioritises walking reduction; `balanced` gives more weight to replenishment congestion and move churn |
| Safety | A plan can be infeasible. Violations are returned instead of assigning an unsafe slot. Worker minutes are checked separately from travel efficiency |
| Uncertainty | Each recommendation includes `confidence`, score margin, and number of alternatives. Low confidence means human review is appropriate; it is not a probability of correctness |
| Override | `Config(allow_override=True)` is an explicit extension point. Production use should require an authorised user, reason, timestamp, and audit log. The prototype never silently overrides hard safety constraints |
| Evaluation | Frequency-weighted travel formula, neutral same-zone counterfactual, 200-event bootstrap sensitivity, and replenishment congestion comparison |

## Operational workflow

The suggested workflow is: ingest the daily extracts; clean and validate records; calculate demand, frequency, item volume, and replenishment effort; generate feasible locations; score two objective functions; review low-confidence recommendations and any violations; obtain authorised override only where policy permits; publish a pick-face change list; and monitor travel, replenishment minutes, congestion, temperature exceptions, and worker workload after rollout.

## Edge and failure cases covered

The tests cover a temperature-zone mismatch or blocked location, sudden temperature excursion, out-of-range temperature, hazardous cross-contamination, hazardous item in a standard location, location over-capacity, zone over-capacity, replenishment workload above the shift limit, hard congestion limit, and low-confidence recommendations. The data also includes missing capacity, missing weight, inconsistent casing, mixed decimal separators, a duplicate SKU, and an event with a blank duration. These cases are cleaned or surfaced explicitly rather than hidden.

## Important interpretation limit

This is a decision-support prototype, not a validated GDP/GMP warehouse control system. Synthetic data is used because no real warehouse extract was supplied. Reported travel reduction is an experiment result on this generated scenario, not a guarantee. Before live use, validate temperature mapping, segregation rules, hazardous-material policy, operator walking paths, replenishment waves, ergonomic limits, and change-control requirements with authorised warehouse and quality stakeholders.

## Files

- `src/generate_data.py`: creates dirty source CSVs.
- `src/optimizer.py`: cleaning, feasibility checks, objective scoring, uncertainty, and evaluation.
- `src/main.py`: runs both objectives and exports outputs.
- `src/validate_travel.py`: mathematical travel metric and baseline robustness validation.
- `tests/test_optimizer.py`: core optimiser safety and failure tests.
- `tests/test_safety_and_robustness.py`: temperature, hazardous-material, capacity, congestion, and travel metric tests.
- `docs/evaluation_report.md`: formulas, baseline sensitivity, congestion penalty, measured result, error analysis, and validation.
- `src/demo_video.py`: generates a three-minute narrated-style MP4 slide demo when FFmpeg is available.
