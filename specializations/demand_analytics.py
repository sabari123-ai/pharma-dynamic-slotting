"""Demand analytics specialization: SKU frequency, velocity, and ABC classification."""
from collections import Counter, defaultdict
from statistics import mean

def sku_demand_profile(order_lines):
    qty=Counter(); lines=Counter(); days=defaultdict(set)
    for row in order_lines:
        sku=str(row['sku_id']).strip().upper(); q=int(float(row.get('qty',1)))
        qty[sku]+=q; lines[sku]+=1
        if row.get('ordered_at'): days[sku].add(str(row['ordered_at'])[:10])
    total=sum(qty.values()) or 1
    rows=[]
    for sku in sorted(qty, key=lambda x:(-qty[x],x)):
        rows.append({'sku_id':sku,'units':qty[sku],'order_lines':lines[sku],'active_days':len(days[sku]),'share_pct':round(100*qty[sku]/total,2),'velocity_per_active_day':round(qty[sku]/max(1,len(days[sku])),2)})
    cumulative=0
    for row in rows:
        cumulative+=row['share_pct']; row['abc_class']='A' if cumulative<=80 else 'B' if cumulative<=95 else 'C'
    return rows

def run(order_lines): return sku_demand_profile(order_lines)
