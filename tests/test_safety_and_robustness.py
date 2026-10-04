import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from optimizer import Config, build_plan, compatibility_reasons, replenishment_congestion_penalty, travel_reduction_pct

def sku(**overrides):
    x={'sku_id':'S1','length_cm':10,'width_cm':10,'height_cm':10,'weight_kg':1,'zone':'COLD','compatibility':'standard','hazardous':False,'case_pack':1,'min_temp_c':2,'max_temp_c':8}
    x.update(overrides); return x

def loc(**overrides):
    x={'location_id':'C1','zone':'COLD','x_m':1,'y_m':1,'capacity_cm3':5000,'max_weight_kg':5,'blocked':False,'current_temp_c':5,'temperature_excursion':False,'hazard_class':'standard','cross_contamination_risk':False}
    x.update(overrides); return x

def test_sudden_temperature_excursion_is_hard_failure():
    reasons=compatibility_reasons(sku(),loc(temperature_excursion=True),1000,1)
    assert 'temperature_excursion_or_out_of_range' in reasons

def test_out_of_range_temperature_is_hard_failure():
    reasons=compatibility_reasons(sku(),loc(current_temp_c=12),1000,1)
    assert 'temperature_excursion_or_out_of_range' in reasons

def test_hazardous_cross_contamination_is_hard_failure():
    reasons=compatibility_reasons(sku(hazardous=True,compatibility='hazmat'),loc(cross_contamination_risk=True),1000,1)
    assert 'hazardous_cross_contamination_risk' in reasons

def test_hazardous_item_cannot_use_standard_location():
    reasons=compatibility_reasons(sku(hazardous=True,compatibility='hazmat'),loc(),1000,1)
    assert 'hazardous_cross_contamination_risk' in reasons

def test_over_capacity_zone_is_hard_failure():
    reasons=compatibility_reasons(sku(),loc(zone_capacity_cm3=1000,zone_used_cm3=500),1000,1)
    assert 'zone_capacity_exceeded' in reasons

def test_over_capacity_location_is_hard_failure():
    reasons=compatibility_reasons(sku(),loc(capacity_cm3=500),1000,1)
    assert 'location_capacity_exceeded' in reasons

def test_congestion_penalty_is_zero_then_convex_then_infinite():
    assert replenishment_congestion_penalty(3,3,30,1)==0
    assert replenishment_congestion_penalty(5,3,30,1)==4
    assert replenishment_congestion_penalty(10,3,30,1)>replenishment_congestion_penalty(5,3,30,1)
    assert replenishment_congestion_penalty(31,3,30,1)==float('inf')

def test_build_plan_surfaces_temperature_failure_instead_of_assigning():
    s=[sku()]; o=[{'order_id':'O1','sku_id':'S1','qty':1}]; l=[loc(temperature_excursion=True)]
    out=build_plan(s,o,l,[],Config())
    assert not out['plan'] and out['hard_violations'][0]['sku_id']=='S1'

def test_travel_reduction_uses_frequency_weighted_distance():
    base=[{'travel_m':100,'pick_frequency':10}]; candidate=[{'estimated_travel_m':50,'pick_frequency':10}]
    assert travel_reduction_pct(base,candidate)==50.0
