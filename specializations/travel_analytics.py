"""Travel analytics specialization: weighted walking estimates and route summaries."""
import math

def distance(a,b): return round(math.hypot(float(a.get('x_m',0))-float(b.get('x_m',0)),float(a.get('y_m',0))-float(b.get('y_m',0))),2)

def weighted_travel(assignments):
    return round(sum(float(x.get('estimated_travel_m',0))*int(x.get('pick_frequency',0)) for x in assignments),2)

def compare(baseline, candidate):
    b=weighted_travel(baseline); c=weighted_travel(candidate)
    return {'baseline_weighted_travel_m':b,'candidate_weighted_travel_m':c,'reduction_pct':round(100*(b-c)/max(1,b),2)}
