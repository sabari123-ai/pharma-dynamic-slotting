from __future__ import annotations
import csv, math, re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    objective: str = 'balanced'  # travel_first or balanced
    max_worker_minutes: float = 420.0
    congestion_limit: int = 30
    congestion_soft_limit: int = 3
    congestion_penalty_weight: float = 0.8
    allow_override: bool = False


def norm(s): return re.sub(r'[^a-z0-9]', '', str(s).strip().lower())

def num(v, default=0.0):
    if v in (None, ''): return default
    try: return float(str(v).replace(',','.'))
    except (ValueError, TypeError): return default

def bool_value(v): return norm(v) in ('y','yes','true','1')

def clean_zone(v):
    x=norm(v)
    if '2' in x or '8' in x or 'cold' in x: return 'COLD'
    if 'controlled' in x: return 'CONTROLLED'
    return 'AMBIENT'

def load_clean(root: Path):
    def read(name):
        with (root/'data'/name).open(encoding='utf-8') as f: return list(csv.DictReader(f))
    raw_skus=read('skus_unclean.csv'); seen=set(); skus=[]
    for r in raw_skus:
        sid=norm(r['sku_id']).upper()
        if sid in seen: continue
        seen.add(sid)
        compatibility=norm(r['compatibility_class']) or 'standard'
        skus.append({'sku_id':sid,'length_cm':num(r['length_cm'],10),'width_cm':num(r['width_cm'],10),'height_cm':num(r['height_cm'],10),'weight_kg':num(r['weight_kg'],1),'zone':clean_zone(r['storage_zone']),'compatibility':compatibility,'hazardous':compatibility in ('hazmat','hazardous','flammable','cytotoxic'),'case_pack':int(num(r['case_pack'],1)),'min_temp_c':num(r.get('min_pick_temp_c'),0),'max_temp_c':num(r.get('max_pick_temp_c'),25)})
    orders=read('order_lines_unclean.csv'); clean_orders=[]
    for r in orders:
        sid=norm(r['sku_id']).upper()
        if sid in seen: clean_orders.append({'order_id':norm(r['order_id']).upper(),'sku_id':sid,'qty':int(num(r['qty'],1))})
    locs=[]
    for r in read('locations_unclean.csv'):
        locs.append({'location_id':norm(r['location_id']).upper(),'zone':clean_zone(r['zone']),'x_m':num(r['x_m']),'y_m':num(r['y_m']),'capacity_cm3':num(r['capacity_cm3'],12000),'max_weight_kg':num(r['max_weight_kg'],30),'blocked':bool_value(r['blocked']),'current_temp_c':num(r.get('current_temp_c'),None) if r.get('current_temp_c') not in (None,'') else None,'temperature_excursion':bool_value(r.get('temperature_excursion')),'hazard_class':norm(r.get('hazard_class')) or 'standard','cross_contamination_risk':bool_value(r.get('cross_contamination_risk')),'zone_capacity_cm3':num(r.get('zone_capacity_cm3'),None) if r.get('zone_capacity_cm3') not in (None,'') else None,'zone_used_cm3':num(r.get('zone_used_cm3'),0)})
    reps=[]
    for r in read('replenishment_events_unclean.csv'):
        reps.append({'sku_id':norm(r['sku_id']).upper(),'location_id':norm(r['location_id']).upper(),'minutes':num(r['minutes'],8),'worker_id':norm(r['worker_id']).upper()})
    return skus, clean_orders, locs, reps

def travel_distance(location, depot=(0.0,0.0)):
    """Euclidean proxy: d(l)=sqrt((x-x0)^2+(y-y0)^2), in metres."""
    return math.hypot(float(location.get('x_m',0))-depot[0], float(location.get('y_m',0))-depot[1])

def weighted_travel(assignments, distance_key='estimated_travel_m', frequency_key='pick_frequency'):
    """T = sum_i f_i d_i; frequencies are weights, not additional locations."""
    return sum(float(row.get(distance_key,0))*float(row.get(frequency_key,0)) for row in assignments)

def travel_reduction_pct(baseline, candidate):
    b=weighted_travel(baseline, 'travel_m'); c=weighted_travel(candidate, 'estimated_travel_m')
    return 100.0*(b-c)/max(1e-9,b)

def temperature_safe(sku, loc):
    if bool(loc.get('temperature_excursion',False)): return False
    current=loc.get('current_temp_c')
    if current is not None and not (float(sku.get('min_temp_c',0)) <= float(current) <= float(sku.get('max_temp_c',25))): return False
    return True

def hazard_safe(sku, loc):
    hazardous=bool(sku.get('hazardous',False))
    hazard_class=norm(loc.get('hazard_class','standard')) or 'standard'
    if hazardous and (loc.get('cross_contamination_risk',False) or hazard_class in ('standard','ambient')): return False
    if not hazardous and hazard_class in ('hazmat','cytotoxic','flammable'): return False
    return True

def compatibility_reasons(sku, loc, required_volume=None, required_weight=None):
    reasons=[]
    if sku.get('zone') != loc.get('zone'): reasons.append('storage_zone_mismatch')
    if loc.get('blocked'): reasons.append('location_blocked')
    if not temperature_safe(sku,loc): reasons.append('temperature_excursion_or_out_of_range')
    if not hazard_safe(sku,loc): reasons.append('hazardous_cross_contamination_risk')
    if required_volume is not None and required_volume > float(loc.get('capacity_cm3',0)): reasons.append('location_capacity_exceeded')
    if required_weight is not None and required_weight > float(loc.get('max_weight_kg',0)): reasons.append('location_weight_exceeded')
    if loc.get('zone_capacity_cm3') is not None and float(loc.get('zone_used_cm3',0))+float(required_volume or 0)>float(loc['zone_capacity_cm3']): reasons.append('zone_capacity_exceeded')
    return reasons

def compatible(sku, loc): return not compatibility_reasons(sku,loc)

def replenishment_congestion_penalty(current_events, soft_limit=3, hard_limit=30, weight=1.0):
    """Piecewise convex penalty P(n)=w*max(0,n-s)^2 plus infinity at hard limit.

    n is current/projected replenishment events at a location per planning window.
    The quadratic term makes already-busy faces disproportionately unattractive;
    the hard-limit flag prevents a soft objective from trading away operations safety.
    """
    n=float(current_events)
    if n > hard_limit: return math.inf
    return float(weight)*max(0.0,n-float(soft_limit))**2

def build_plan(skus, orders, locs, reps, cfg=Config()):
    sku_by={s['sku_id']:s for s in skus}; demand=Counter(o['sku_id'] for o in orders); qty=Counter()
    for o in orders: qty[o['sku_id']]+=o['qty']
    rep_count=Counter(r['sku_id'] for r in reps); rep_minutes=Counter()
    for r in reps: rep_minutes[r['sku_id']]+=r['minutes']
    existing={}
    for sku in sku_by:
        candidates=[r['location_id'] for r in reps if r['sku_id']==sku]
        if candidates: existing[sku]=Counter(candidates).most_common(1)[0][0]
    plan=[]; uncertainty=[]; hard_violations=[]
    for sid, d in sorted(demand.items(), key=lambda x:-x[1]):
        sku=sku_by[sid]; units=max(1, qty[sid]/sku['case_pack']); volume=sku['length_cm']*sku['width_cm']*sku['height_cm']*units; weight=sku['weight_kg']*units
        options=[]
        for loc in locs:
            reasons=compatibility_reasons(sku,loc,volume,weight)
            if reasons: continue
            travel=travel_distance(loc); move=0 if existing.get(sid)==loc['location_id'] else 1
            congestion=sum(1 for r in reps if r['location_id']==loc['location_id'])
            congestion_penalty=replenishment_congestion_penalty(congestion,cfg.congestion_soft_limit,cfg.congestion_limit,cfg.congestion_penalty_weight)
            if not math.isfinite(congestion_penalty): continue
            if cfg.objective=='travel_first': score=travel + rep_count[sid]*0.10 + congestion_penalty*0.01 + move*2
            else: score=travel*0.65 + rep_minutes[sid]*0.05 + congestion_penalty + move*4
            options.append((score,loc,travel,congestion,move,congestion_penalty))
        if not options:
            hard_violations.append({'sku_id':sid,'reason':'no compatible location','checks':['zone','blocked','temperature','hazard','location_capacity','weight','zone_capacity']})
            continue
        options.sort(key=lambda x:x[0]); score,loc,travel,cong,move,cong_penalty=options[0]
        margin=(options[1][0]-score)/max(1,score) if len(options)>1 else 0
        confidence='high' if margin>.20 else 'medium' if margin>.05 else 'low'
        uncertainty.append({'sku_id':sid,'confidence':confidence,'score_margin':round(margin,3),'alternatives_considered':len(options)})
        plan.append({'sku_id':sid,'location_id':loc['location_id'],'pick_frequency':d,'order_qty':qty[sid],'estimated_travel_m':round(travel,1),'replenishment_events':rep_count[sid],'replenishment_minutes':round(rep_minutes[sid],1),'location_congestion_events':cong,'congestion_penalty':round(cong_penalty,2),'objective_score':round(score,2),'confidence':confidence,'override_required':False})
    total_repl=sum(p['replenishment_minutes'] for p in plan); workload_violations=[]
    if total_repl>cfg.max_worker_minutes: workload_violations.append({'worker':'ALL','minutes':round(total_repl,1),'limit':cfg.max_worker_minutes,'reason':'replenishment workload exceeds shift limit'})
    return {'plan':plan,'uncertainty':uncertainty,'hard_violations':hard_violations,'workload_violations':workload_violations,'objective':cfg.objective}

def evaluate(plan, baseline, reps):
    base_travel=weighted_travel(baseline,'travel_m','pick_frequency'); opt_travel=weighted_travel(plan['plan'],'estimated_travel_m','pick_frequency')
    base_locs={x['location_id'] for x in baseline}; base_cong=sum(1 for r in reps if r['location_id'] in base_locs); opt_cong=sum(x['location_congestion_events'] for x in plan['plan'])
    return {'baseline_weighted_travel_m':round(base_travel,1),'optimised_weighted_travel_m':round(opt_travel,1),'travel_reduction_pct':round(100*(base_travel-opt_travel)/max(1,base_travel),1),'baseline_replenishment_congestion':base_cong,'optimised_replenishment_congestion':opt_cong,'congestion_change_pct':round(100*(opt_cong-base_cong)/max(1,base_cong),1)}
