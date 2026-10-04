from pathlib import Path
import csv, json
from optimizer import Config, load_clean, build_plan, evaluate
ROOT=Path(__file__).resolve().parents[1]

def write_csv(path, rows):
    if not rows: return
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

def main():
    skus,orders,locs,reps=load_clean(ROOT)
    baseline=[]
    # baseline is the inferred current slotting: same location, weighted demand.
    from collections import Counter
    for sid in {s['sku_id'] for s in skus}:
        rs=[r for r in reps if r['sku_id']==sid]
        if not rs: continue
        loc=Counter(r['location_id'] for r in rs).most_common(1)[0][0]
        l=next((x for x in locs if x['location_id']==loc),None)
        if l:
            baseline.append({'sku_id':sid,'location_id':loc,'pick_frequency':sum(o['sku_id']==sid for o in orders),'travel_m':round((l['x_m']**2+l['y_m']**2)**.5,1)})
    outputs={}
    for objective in ('travel_first','balanced'):
        plan=build_plan(skus,orders,locs,reps,Config(objective=objective))
        outputs[objective]=plan
        write_csv(ROOT/'outputs'/f'plan_{objective}.csv',plan['plan'])
    metrics={o:evaluate(p,baseline,reps) for o,p in outputs.items()}
    result={'input_summary':{'skus':len(skus),'order_lines':len(orders),'locations':len(locs),'replenishment_events':len(reps)},'baseline_rows':len(baseline),'metrics':metrics,'plans':outputs}
    (ROOT/'outputs'/'evaluation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    write_csv(ROOT/'outputs'/'baseline.csv',baseline)
    print(json.dumps({'input_summary':result['input_summary'],'metrics':metrics},indent=2))
if __name__=='__main__': main()
