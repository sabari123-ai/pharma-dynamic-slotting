from __future__ import annotations
import csv, math, re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    objective: str = 'balanced'  # travel_first or balanced
    max_worker_minutes: float = 420.0
    congestion_limit: int = 3
    allow_override: bool = False


def norm(s): return re.sub(r'[^a-z0-9]', '', str(s).strip().lower())

def num(v, default=0.0):
    if v in (None, ''): return default
    try: return float(str(v).replace(',','.'))
    except ValueError: return default

def clean_zone(v):
    x=norm(v)
    if '2' in x or '8' in x: return 'COLD'
    if 'controlled' in x: return 'CONTROLLED'
    return 'AMBIENT'

def load_clean(root: Path):
    def read(name):
        with (root/'data'/name).open(encoding='utf-8') as f: return list(csv.DictReader(f))
    raw_skus=read('skus_unclean.csv'); seen=set(); skus=[]
    for r in raw_skus:
        sid=norm(r['sku_id']).upper();
        if sid in seen: continue
        seen.add(sid)
        skus.append({'sku_id':sid,'length_cm':num(r['length_cm'],10),'width_cm':num(r['width_cm'],10),'height_cm':num(r['height_cm'],10),'weight_kg':num(r['weight_kg'],1),'zone':clean_zone(r['storage_zone']),'compatibility':norm(r['compatibility_class']) or 'standard','case_pack':int(num(r['case_pack'],1)),'max_temp_c':num(r['max_pick_temp_c'],25)})
    orders=read('order_lines_unclean.csv'); clean_orders=[]
    for r in orders:
        sid=norm(r['sku_id']).upper()
        if sid in seen: clean_orders.append({'order_id':norm(r['order_id']).upper(),'sku_id':sid,'qty':int(num(r['qty'],1))})
    locs=[]
    for r in read('locations_unclean.csv'):
        blocked=norm(r['blocked']) in ('y','yes','true','1')
        locs.append({'location_id':norm(r['location_id']).upper(),'zone':clean_zone(r['zone']),'x_m':num(r['x_m']),'y_m':num(r['y_m']),'capacity_cm3':num(r['capacity_cm3'],12000),'max_weight_kg':num(r['max_weight_kg'],30),'blocked':blocked})
    reps=[]
    for r in read('replenishment_events_unclean.csv'):
        reps.append({'sku_id':norm(r['sku_id']).upper(),'location_id':norm(r['location_id']).upper(),'minutes':num(r['minutes'],8),'worker_id':norm(r['worker_id']).upper()})
    return skus, clean_orders, locs, reps

def compatible(sku, loc):
    return sku['zone']==loc['zone'] and not loc['blocked']

def build_plan(skus, orders, locs, reps, cfg=Config()):
    sku_by={s['sku_id']:s for s in skus}; demand=Counter(o['sku_id'] for o in orders); qty=Counter();
    for o in orders: qty[o['sku_id']]+=o['qty']
    rep_count=Counter(r['sku_id'] for r in reps); rep_minutes=Counter()
    for r in reps: rep_minutes[r['sku_id']]+=r['minutes']
    # Existing location is inferred from most frequent replenishment location.
    existing={}
    for sku in sku_by:
        candidates=[r['location_id'] for r in reps if r['sku_id']==sku]
        if candidates: existing[sku]=Counter(candidates).most_common(1)[0][0]
    valid=[l for l in locs if not l['blocked']]
    plan=[]; used=set(); uncertainty=[]; hard_violations=[]
    for sid, d in sorted(demand.items(), key=lambda x:-x[1]):
        sku=sku_by[sid]; volume=sku['length_cm']*sku['width_cm']*sku['height_cm']*max(1, qty[sid]/sku['case_pack'])
        options=[]
        for loc in valid:
            if not compatible(sku,loc): continue
            if volume > loc['capacity_cm3']: continue
            if sku['weight_kg']*max(1,qty[sid]/sku['case_pack']) > loc['max_weight_kg']: continue
            travel=math.hypot(loc['x_m'],loc['y_m'])
            move=0 if existing.get(sid)==loc['location_id'] else 1
            congestion=sum(1 for r in reps if r['location_id']==loc['location_id'])
            # Soft penalties: travel, replenishment frequency/effort, congestion, move churn.
            if cfg.objective=='travel_first': score=travel*1.0 + rep_count[sid]*0.10 + congestion*0.05 + move*2
            else: score=travel*0.65 + rep_minutes[sid]*0.05 + congestion*0.8 + move*4
            options.append((score,loc,travel,congestion,move))
        if not options:
            hard_violations.append({'sku_id':sid,'reason':'no compatible, unblocked, capacity-valid location'})
            continue
        options.sort(key=lambda x:x[0]); score,loc,travel,cong,move=options[0]
        used.add(loc['location_id'])
        # Communicate uncertainty: confidence depends on margin and demand volume.
        margin=(options[1][0]-score)/max(1,score) if len(options)>1 else 0
        confidence='high' if margin>.20 else 'medium' if margin>.05 else 'low'
        uncertainty.append({'sku_id':sid,'confidence':confidence,'score_margin':round(margin,3),'alternatives_considered':len(options)})
        plan.append({'sku_id':sid,'location_id':loc['location_id'],'pick_frequency':d,'order_qty':qty[sid],'estimated_travel_m':round(travel,1),'replenishment_events':rep_count[sid],'replenishment_minutes':round(rep_minutes[sid],1),'location_congestion_events':cong,'objective_score':round(score,2),'confidence':confidence,'override_required':False})
    # A worker limit is a hard operational guardrail, not an optimisation trade-off.
    total_repl=sum(p['replenishment_minutes'] for p in plan)
    workload_violations=[]
    if total_repl>cfg.max_worker_minutes:
        workload_violations.append({'worker':'ALL','minutes':round(total_repl,1),'limit':cfg.max_worker_minutes,'reason':'replenishment workload exceeds shift limit'})
    return {'plan':plan,'uncertainty':uncertainty,'hard_violations':hard_violations,'workload_violations':workload_violations,'objective':cfg.objective}

def evaluate(plan, baseline, reps):
    def congestion(rows): return sum(r['location_id']==x for r in rows for x in [r['location_id']]) / max(1,len(rows))
    base_travel=sum(x['travel_m']*x['pick_frequency'] for x in baseline)
    opt_travel=sum(x['estimated_travel_m']*x['pick_frequency'] for x in plan['plan'])
    base_cong=sum(1 for r in reps if r['location_id'] in {x['location_id'] for x in baseline})
    opt_cong=sum(x['location_congestion_events'] for x in plan['plan'])
    return {'baseline_weighted_travel_m':round(base_travel,1),'optimised_weighted_travel_m':round(opt_travel,1),'travel_reduction_pct':round(100*(base_travel-opt_travel)/max(1,base_travel),1),'baseline_replenishment_congestion':base_cong,'optimised_replenishment_congestion':opt_cong,'congestion_change_pct':round(100*(opt_cong-base_cong)/max(1,base_cong),1)}
