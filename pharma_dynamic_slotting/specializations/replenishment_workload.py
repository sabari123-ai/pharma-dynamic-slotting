"""Replenishment specialization: workload limits, congestion, and safe capacity."""
from collections import Counter, defaultdict

def workload_by_worker(events):
    result=defaultdict(float)
    for e in events: result[str(e.get('worker_id','UNKNOWN')).strip().upper()]+=float(e.get('minutes',0) or 0)
    return {k:round(v,2) for k,v in result.items()}

def congestion_by_location(events):
    c=Counter(str(e.get('location_id','')).strip().upper() for e in events)
    return dict(c)

def check_limits(events, worker_limit_minutes=420, location_limit_events=30):
    workers=workload_by_worker(events); locations=congestion_by_location(events)
    return {'worker_violations':[{'worker_id':w,'minutes':m,'limit':worker_limit_minutes} for w,m in workers.items() if m>worker_limit_minutes],'location_violations':[{'location_id':l,'events':n,'limit':location_limit_events} for l,n in locations.items() if n>location_limit_events]}
# Sample replenishment events
events = [
    {'worker_id': 'W001', 'minutes': 120, 'location_id': 'A01'},
    {'worker_id': 'W001', 'minutes': 150, 'location_id': 'A01'},
    {'worker_id': 'W002', 'minutes': 200, 'location_id': 'A02'},
    {'worker_id': 'W002', 'minutes': 250, 'location_id': 'A02'},
    {'worker_id': 'W003', 'minutes': 100, 'location_id': 'A01'},
]

# Test workload_by_worker()
print("Workload by worker:")
print(workload_by_worker(events))

# Test congestion_by_location()
print("\nCongestion by location:")
print(congestion_by_location(events))

# Test check_limits()
print("\nLimit check:")
print(check_limits(events))