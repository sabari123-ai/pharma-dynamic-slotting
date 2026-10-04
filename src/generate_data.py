from __future__ import annotations
import csv, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
random.seed(7)

def write_csv(path, rows):
    path.parent.mkdir(exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)

# Deliberately unclean: inconsistent case, whitespace, missing values, mixed units, duplicate row.
skus=[]
for i in range(1,31):
    temp = random.choice(['2-8C','15-25 C','AMBIENT','2–8 °C'])
    compat = random.choice(['standard','hazmat','controlled','cold_chain'])
    skus.append({'sku_id':f'SKU-{i:03d}','description':f'Medicine {i}','length_cm':round(random.uniform(8,35),1),'width_cm':round(random.uniform(5,25),1),'height_cm':round(random.uniform(3,18),1),'weight_kg':round(random.uniform(.1,4),2),'storage_zone':temp,'compatibility_class':compat,'case_pack':random.choice([1,6,12,24]),'min_pick_temp_c':2 if '2' in temp else 15,'max_pick_temp_c':8 if '2' in temp else 25})
skus[3]['storage_zone']=' 2-8c '; skus[7]['length_cm']='30,0'; skus[12]['weight_kg']=''; skus.append(skus[4].copy())
write_csv(DATA/'skus_unclean.csv', skus)

orders=[]
for order in range(1,501):
    lines=random.randint(1,6)
    for _ in range(lines):
        sku=f'SKU-{random.randint(1,30):03d}'
        qty=random.choices([1,2,4,8,12],[.35,.3,.2,.1,.05])[0]
        orders.append({'order_id':f'ORD-{order:04d}','sku_id':sku,'qty':qty,'ordered_at':f'2026-08-{random.randint(1,28):02d} {random.randint(6,21):02d}:00'})
orders.append({'order_id':'ORD-0001','sku_id':' sku-001 ','qty':'2','ordered_at':'2026/08/01 08:00'})
write_csv(DATA/'order_lines_unclean.csv', orders)

locations=[]
for z, prefix, n in [('AMBIENT','A',18),('COLD','C',10),('CONTROLLED','K',8)]:
    for i in range(1,n+1):
        locations.append({'location_id':f'{prefix}-{i:02d}','zone':z,'aisle':i,'bay':random.randint(1,10),'level':random.choice([1,2,3]),'x_m':round((i-1)*3.2 + (0 if z=='AMBIENT' else 65 if z=='COLD' else 100),1),'y_m':round(random.choice([0,4,8,12]),1),'capacity_cm3':random.choice([12000,18000,24000]),'max_weight_kg':random.choice([30,50,80]),'blocked':random.choice(['N','N','N','Y'])})
locations[2]['zone']='ambient'; locations[6]['capacity_cm3']=''; locations[15]['blocked']=' yes '
write_csv(DATA/'locations_unclean.csv', locations)

repls=[]
for i in range(1,301):
    sku=f'SKU-{random.randint(1,30):03d}'
    repls.append({'event_id':f'REP-{i:04d}','sku_id':sku,'location_id':f'{random.choice(["A","C","K"])}-{random.randint(1,10):02d}','qty':random.choice([6,12,24]),'minutes':round(random.uniform(3,18),1),'worker_id':f'W-{random.randint(1,5):02d}','event_date':f'2026-08-{random.randint(1,28):02d}'})
repls[4]['minutes']=''; repls[9]['location_id']=' c-02 '
write_csv(DATA/'replenishment_events_unclean.csv', repls)
print('Generated dirty CSVs in', DATA)
