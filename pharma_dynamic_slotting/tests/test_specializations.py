import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'specializations'))
from demand_analytics import sku_demand_profile
from storage_safety import check_assignment
from travel_analytics import compare
from replenishment_workload import check_limits
from governance import authorised_override, confidence_from_margin
from operations_monitoring import kpi_snapshot

def test_demand_abc_profile():
    rows=sku_demand_profile([{'sku_id':'a','qty':8,'ordered_at':'2026-01-01'},{'sku_id':'b','qty':2,'ordered_at':'2026-01-01'}])
    assert rows[0]['sku_id']=='A' and rows[0]['abc_class']=='A'

def test_storage_safety_blocks_zone_mismatch():
    s={'zone':'COLD','length_cm':10,'width_cm':10,'height_cm':10,'case_pack':1,'weight_kg':1}
    l={'zone':'AMBIENT','capacity_cm3':10000,'max_weight_kg':10,'blocked':False}
    assert not check_assignment(s,l)['feasible']

def test_travel_compare():
    assert compare([{'estimated_travel_m':10,'pick_frequency':10}],[{'estimated_travel_m':5,'pick_frequency':10}])['reduction_pct']==50.0

def test_workload_guardrail():
    out=check_limits([{'worker_id':'W1','minutes':500}],420)
    assert out['worker_violations']

def test_override_requires_authority_and_reason():
    out=authorised_override({'sku_id':'S1'},{'user_id':'u1','role':'quality_supervisor'},'approved by QA')
    assert out['override_required']

def test_confidence_and_release_guardrail():
    assert confidence_from_margin(.01)=='low'
    assert not kpi_snapshot({'travel_reduction_pct':10,'congestion_change_pct':2},0,0)['safe_to_release']
