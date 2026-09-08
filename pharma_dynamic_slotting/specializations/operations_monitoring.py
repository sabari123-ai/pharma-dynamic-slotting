"""Operations monitoring specialization: pilot KPIs and guardrail checks."""

def kpi_snapshot(metrics, hard_violations=0, workload_violations=0):

    travel_change = metrics.get('travel_reduction_pct', 0)

    congestion_change = metrics.get('congestion_change_pct', 0)

    return {
        'travel_reduction_pct': travel_change,
        'congestion_change_pct': congestion_change,
        'hard_violations': hard_violations,
        'workload_violations': workload_violations,
        'safe_to_release': hard_violations == 0
            and workload_violations == 0
            and congestion_change <= 0
    }


def acceptance_check(before, after):

    return {
        'travel_improved': after.get('weighted_travel_m', 0)
            < before.get('weighted_travel_m', 0),

        'congestion_not_increased': after.get('congestion_events', 0)
            <= before.get('congestion_events', 0),

        'workload_within_limit': after.get('max_worker_minutes', 0)
            <= after.get('worker_limit_minutes', 420)
    }# Sample KPI metrics
metrics = {
    'travel_reduction_pct': 12.5,
    'congestion_change_pct': -5.0
}

# Test kpi_snapshot()
kpi_result = kpi_snapshot(metrics)

print("KPI Snapshot:")
print(kpi_result)


# Sample before and after metrics
before = {
    'weighted_travel_m': 1000,
    'congestion_events': 50
}

after = {
    'weighted_travel_m': 850,
    'congestion_events': 45,
    'max_worker_minutes': 390,
    'worker_limit_minutes': 420
}

# Test acceptance_check()
acceptance_result = acceptance_check(before, after)

print("\nAcceptance Check:")
print(acceptance_result)