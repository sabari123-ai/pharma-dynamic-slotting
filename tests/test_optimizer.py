import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from optimizer import build_plan, Config

def sample():
    skus=[{'sku_id':'S1','length_cm':10,'width_cm':10,'height_cm':10,'weight_kg':1,'zone':'COLD','compatibility':'standard','case_pack':1,'max_temp_c':8},{'sku_id':'S2','length_cm':10,'width_cm':10,'height_cm':10,'weight_kg':1,'zone':'AMBIENT','compatibility':'standard','case_pack':1,'max_temp_c':25}]
    orders=[{'order_id':'O1','sku_id':'S1','qty':1},{'order_id':'O2','sku_id':'S2','qty':1}]
    locs=[{'location_id':'C1','zone':'COLD','x_m':1,'y_m':1,'capacity_cm3':5000,'max_weight_kg':5,'blocked':False},{'location_id':'A1','zone':'AMBIENT','x_m':1,'y_m':1,'capacity_cm3':5000,'max_weight_kg':5,'blocked':False},{'location_id':'C2','zone':'COLD','x_m':5,'y_m':5,'capacity_cm3':5000,'max_weight_kg':5,'blocked':True}]
    reps=[]
    return skus,orders,locs,reps

def test_zone_and_blocked_hard_constraints():
    p=build_plan(*sample(),Config())['plan']
    assert {x['sku_id']:x['location_id'] for x in p}=={'S1':'C1','S2':'A1'}

def test_no_compatible_location_is_reported():
    s,o,l,r=sample(); l[0]['blocked']=True
    out=build_plan(s,o,l,r,Config())
    assert out['hard_violations'] and out['hard_violations'][0]['sku_id']=='S1'

def test_worker_limit_is_not_traded_away():
    s,o,l,r=sample(); r=[{'sku_id':'S1','location_id':'C1','minutes':500,'worker_id':'W1'}]
    out=build_plan(s,o,l,r,Config(max_worker_minutes=420))
    assert out['workload_violations']

def test_uncertainty_is_exposed():
    out=build_plan(*sample(),Config())
    assert all(x['confidence'] in ('high','medium','low') for x in out['uncertainty'])
