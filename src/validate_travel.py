from __future__ import annotations
import json, random, statistics
from collections import Counter
from pathlib import Path
from optimizer import Config, load_clean, build_plan, travel_distance, weighted_travel

ROOT=Path(__file__).resolve().parents[1]

def infer_locations(skus, reps):
    by={}
    for s in skus:
        xs=[r['location_id'] for r in reps if r['sku_id']==s['sku_id']]
        if xs: by[s['sku_id']]=Counter(xs).most_common(1)[0][0]
    return by

def demand_counts(orders):
    c=Counter()
    for o in orders: c[o['sku_id']]+=1
    return c

def baseline_rows(skus, orders, locs, reps):
    byloc={x['location_id']:x for x in locs}; inferred=infer_locations(skus,reps); demand=demand_counts(orders)
    return [{'sku_id':sid,'location_id':lid,'pick_frequency':demand[sid],'travel_m':travel_distance(byloc[lid])} for sid,lid in inferred.items() if lid in byloc]

def neutral_zone_baseline(skus, orders, locs):
    demand=demand_counts(orders); rows=[]
    for sku in skus:
        candidates=[l for l in locs if l['zone']==sku['zone'] and not l['blocked']]
        if not candidates or sku['sku_id'] not in demand: continue
        distances=sorted(travel_distance(l) for l in candidates); median=statistics.median(distances)
        rows.append({'sku_id':sku['sku_id'],'location_id':'ZONE_MEDIAN','pick_frequency':demand[sku['sku_id']],'travel_m':median})
    return rows

def reduction(baseline, candidate):
    b=weighted_travel(baseline,'travel_m','pick_frequency'); c=weighted_travel(candidate,'estimated_travel_m','pick_frequency')
    return 100*(b-c)/max(1e-9,b)

def bootstrap_baseline(skus, orders, locs, reps, candidate, iterations=200, seed=11):
    rng=random.Random(seed); values=[]
    for _ in range(iterations):
        sample=[rng.choice(reps) for _ in reps]
        rows=baseline_rows(skus,orders,locs,sample)
        if rows: values.append(reduction(rows,candidate))
    values.sort()
    return {'iterations':len(values),'p05_reduction_pct':round(values[int(.05*(len(values)-1))],2),'median_reduction_pct':round(statistics.median(values),2),'p95_reduction_pct':round(values[int(.95*(len(values)-1))],2),'min_reduction_pct':round(min(values),2),'max_reduction_pct':round(max(values),2)}

def main():
    skus,orders,locs,reps=load_clean(ROOT)
    plan=build_plan(skus,orders,locs,reps,Config(objective='travel_first'))
    candidate=plan['plan']; observed=baseline_rows(skus,orders,locs,reps); neutral=neutral_zone_baseline(skus,orders,locs)
    result={'formulas':{'location_distance':'d_l = sqrt((x_l-x_0)^2 + (y_l-y_0)^2)','weighted_travel':'T = sum_i f_i * d_{a(i)}','reduction':'R = 100 * (T_baseline - T_candidate) / T_baseline'},'observed_replenishment_baseline':{'rows':len(observed),'reduction_pct':round(reduction(observed,candidate),2)},'zone_median_counterfactual':{'rows':len(neutral),'reduction_pct':round(reduction(neutral,candidate),2)},'bootstrap_replenishment_baseline':bootstrap_baseline(skus,orders,locs,reps,candidate),'interpretation':'The observed baseline is not accepted as the only proof. Robustness is supported when the reduction remains positive under bootstrap resampling and a neutral same-zone median-distance counterfactual. These are sensitivity checks, not causal proof.'}
    (ROOT/'outputs'/'travel_robustness.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
