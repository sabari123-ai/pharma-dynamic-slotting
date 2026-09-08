"""Travel analytics specialization: weighted walking estimates and route summaries."""
import math

def distance(a,b): return round(math.hypot(float(a.get('x_m',0))-float(b.get('x_m',0)),float(a.get('y_m',0))-float(b.get('y_m',0))),2)

def weighted_travel(assignments):
    return round(sum(float(x.get('estimated_travel_m',0))*int(x.get('pick_frequency',0)) for x in assignments),2)

def compare(baseline, candidate):
    b=weighted_travel(baseline); c=weighted_travel(candidate)
    return {'baseline_weighted_travel_m':b,'candidate_weighted_travel_m':c,'reduction_pct':round(100*(b-c)/max(1,b),2)}
# Sample locations
location_a = {
    'x_m': 0,
    'y_m': 0
}

location_b = {
    'x_m': 3,
    'y_m': 4
}

print("Distance Test:")
print(distance(location_a, location_b))


# Sample travel assignments
baseline = [
    {'estimated_travel_m': 100, 'pick_frequency': 10},
    {'estimated_travel_m': 200, 'pick_frequency': 5},
    {'estimated_travel_m': 150, 'pick_frequency': 4}
]

candidate = [
    {'estimated_travel_m': 80, 'pick_frequency': 10},
    {'estimated_travel_m': 150, 'pick_frequency': 5},
    {'estimated_travel_m': 120, 'pick_frequency': 4}
]

print("\nWeighted Travel - Baseline:")
print(weighted_travel(baseline))

print("\nWeighted Travel - Candidate:")
print(weighted_travel(candidate))

print("\nTravel Comparison:")
print(compare(baseline, candidate))