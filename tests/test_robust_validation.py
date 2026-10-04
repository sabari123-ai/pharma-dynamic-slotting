import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from optimizer import travel_distance, weighted_travel
from validate_baseline_98_6 import LEGACY_REFERENCE_DELTA_PCT, reduction_pct


def test_legacy_98_6_reference_is_preserved():
    assert LEGACY_REFERENCE_DELTA_PCT == 98.6


def test_travel_distance_uses_euclidean_formula():
    assert math.isclose(travel_distance({"x_m": 3, "y_m": 4}), 5.0)


def test_weighted_travel_is_frequency_weighted():
    rows = [
        {"estimated_travel_m": 10, "pick_frequency": 2},
        {"estimated_travel_m": 5, "pick_frequency": 4},
    ]
    assert weighted_travel(rows) == 40


def test_reduction_formula_matches_manual_calculation():
    baseline = [{"travel_m": 100, "pick_frequency": 10}]
    candidate = [{"estimated_travel_m": 50, "pick_frequency": 10}]
    assert reduction_pct(baseline, candidate) == 50.0


def test_zero_baseline_does_not_raise():
    baseline = [{"travel_m": 0, "pick_frequency": 10}]
    candidate = [{"estimated_travel_m": 0, "pick_frequency": 10}]
    assert reduction_pct(baseline, candidate) == 0.0


def test_validation_report_can_be_serialized(tmp_path):
    report = {
        "legacy_reference_delta_pct": LEGACY_REFERENCE_DELTA_PCT,
        "formula": "Delta% = 100 * (T_baseline - T_candidate) / T_baseline",
    }
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["legacy_reference_delta_pct"] == 98.6
