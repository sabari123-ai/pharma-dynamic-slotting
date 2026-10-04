"""Operations monitoring specialization: pilot KPIs and guardrail checks."""

def kpi_snapshot(metrics, hard_violations=0, workload_violations=0):
    travel_change=metrics.get('travel_reduction_pct',0)
    congestion_change=metrics.get('congestion_change_pct',0)
    return {'travel_reduction_pct':travel_change,'congestion_change_pct':congestion_change,'hard_violations':hard_violations,'workload_violations':workload_violations,'safe_to_release':hard_violations==0 and workload_violations==0 and congestion_change<=0}

def acceptance_check(before, after):
    return {'travel_improved':after.get('weighted_travel_m',0)<before.get('weighted_travel_m',0),'congestion_not_increased':after.get('congestion_events',0)<=before.get('congestion_events',0),'workload_within_limit':after.get('max_worker_minutes',0)<=after.get('worker_limit_minutes',420)}
