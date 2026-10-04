# Additive Robustness Validation

This document is an **additive validation layer**. It does not replace the
existing project logic, `outputs/evaluation.json`, the existing specialization
outputs, or the legacy **98.6% travel-delta reference claim**.

## 1. Travel-distance formulation

For location `l` with coordinates `(x_l, y_l)` and depot/reference point
`(x_0, y_0)`:

\[
d_l = \sqrt{(x_l-x_0)^2 + (y_l-y_0)^2}
\]

For SKU `i`, let `f_i` be pick frequency and `a(i)` its assigned location:

\[
T = \sum_i f_i d_{a(i)}
\]

The percentage travel delta is:

\[
\Delta_{travel}(\%) = 100 \times
\frac{T_{baseline}-T_{candidate}}{T_{baseline}}
\]

The implementation uses the existing `travel_distance()` and
`weighted_travel()` functions, so the validation does not introduce a second
travel metric into the optimizer.

## 2. Baseline-sensitivity validation of the legacy 98.6% claim

The legacy/reference value **98.6%** is intentionally retained. The validator
checks it rather than silently replacing it.

Three baseline constructions are evaluated:

1. **Observed replenishment baseline** — the current slotting inferred from the
   most frequent replenishment location for each SKU.
2. **Neutral same-zone counterfactual** — each SKU is compared with the median
   travel distance among feasible, unblocked locations in its own storage zone.
3. **Bootstrap sensitivity** — replenishment history is resampled with
   replacement 200 times and the travel delta is recomputed.

A useful robustness signal is that the delta remains positive and reasonably
stable under the alternative baselines. This is a sensitivity analysis, not a
causal proof.

Run:

```powershell
python src\validate_baseline_98_6.py
```

The additive report is written to:

```text
outputs/baseline_98_6_robustness.json
```

## 3. Replenishment congestion penalty

For `n` replenishment events at a location, soft limit `s`, hard limit `h`, and
weight `w`:

\[
P(n)=
\begin{cases}
\infty, & n>h\\
w\max(0,n-s)^2, & n\le h
\end{cases}
\]

Current defaults are:

- soft limit `s = 3`
- hard limit `h = 30`
- balanced-objective weight `w = 0.8`

Interpretation:

- `n <= 3`: no congestion penalty.
- `n > 3`: penalty grows quadratically, so heavily congested locations become
  disproportionately unattractive.
- `n > 30`: infinite penalty, so the candidate is rejected as operationally
  infeasible.

This is already part of the existing optimizer; the validation layer documents
and tests its mathematical behavior without changing the formula.

## 4. Explicit failure and edge-case tests

The repository test suite includes explicit checks for:

- sudden temperature excursion;
- temperature outside the SKU's allowed range;
- hazardous SKU in a cross-contamination-risk location;
- hazardous SKU in a standard location;
- location capacity overflow;
- zone capacity overflow;
- hard replenishment congestion limit;
- convex congestion behavior;
- worker workload over the configured limit.

The additive robustness tests also verify the 98.6% reference is preserved as a
reference value and that the validation formulas produce deterministic,
frequency-weighted travel calculations.

Run the complete suite with:

```powershell
pytest -q
```

The existing project outputs and the existing main pipeline remain unchanged.
