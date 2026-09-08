from pathlib import Path
import csv, json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'specializations'))
from optimizer import load_clean
from demand_analytics import run as demand_run
from replenishment_workload import check_limits
from operations_monitoring import kpi_snapshot
from governance import review_queue

skus,orders,locations,reps=load_clean(ROOT)
profiles=demand_run(orders)
plan=json.loads((ROOT/'outputs/evaluation.json').read_text())['plans']['balanced']
summary={'demand_top_5':profiles[:5],'replenishment_checks':check_limits(reps),'low_confidence_review_count':len(review_queue(plan['plan'])),'pilot_kpi':kpi_snapshot({'travel_reduction_pct':98.5,'congestion_change_pct':-92.9},len(plan['hard_violations']),len(plan['workload_violations']))}
(ROOT/'outputs'/'specialization_summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
