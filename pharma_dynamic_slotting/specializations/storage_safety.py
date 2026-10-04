"""Storage safety specialization: hard compatibility and capacity checks."""

def check_assignment(sku, location, quantity=1):
    issues=[]
    if str(sku.get('zone','')).upper()!=str(location.get('zone','')).upper(): issues.append('storage_zone_mismatch')
    if location.get('blocked',False): issues.append('location_blocked')
    volume=float(sku.get('length_cm',0))*float(sku.get('width_cm',0))*float(sku.get('height_cm',0))*max(1,quantity/float(sku.get('case_pack',1) or 1))
    if volume>float(location.get('capacity_cm3',0)): issues.append('capacity_exceeded')
    if float(sku.get('weight_kg',0))*max(1,quantity/float(sku.get('case_pack',1) or 1))>float(location.get('max_weight_kg',0)): issues.append('weight_exceeded')
    return {'feasible':not issues,'issues':issues,'estimated_volume_cm3':round(volume,2)}

def audit_plan(plan, sku_by_id, location_by_id):
    return [{'sku_id':row['sku_id'],'location_id':row['location_id'],**check_assignment(sku_by_id[row['sku_id']],location_by_id[row['location_id']],row.get('order_qty',1))} for row in plan]
# Sample SKU data
sku = {
    'sku_id': 'SKU001',
    'zone': 'COLD',
    'length_cm': 10,
    'width_cm': 10,
    'height_cm': 10,
    'case_pack': 10,
    'weight_kg': 2
}

# Sample location data
location = {
    'location_id': 'LOC001',
    'zone': 'COLD',
    'blocked': False,
    'capacity_cm3': 5000,
    'max_weight_kg': 50
}


print("Test 1 - Valid Assignment:")
print(check_assignment(sku, location, quantity=10))


print("\nTest 2 - Wrong Storage Zone:")

wrong_zone_location = {
    'location_id': 'LOC002',
    'zone': 'AMBIENT',
    'blocked': False,
    'capacity_cm3': 5000,
    'max_weight_kg': 50
}

print(check_assignment(sku, wrong_zone_location, quantity=10))


print("\nTest 3 - Blocked Location:")

blocked_location = {
    'location_id': 'LOC003',
    'zone': 'COLD',
    'blocked': True,
    'capacity_cm3': 5000,
    'max_weight_kg': 50
}

print(check_assignment(sku, blocked_location, quantity=10))


print("\nTest 4 - Capacity Exceeded:")

small_location = {
    'location_id': 'LOC004',
    'zone': 'COLD',
    'blocked': False,
    'capacity_cm3': 500,
    'max_weight_kg': 50
}

print(check_assignment(sku, small_location, quantity=10))


print("\nTest 5 - Weight Exceeded:")

low_weight_location = {
    'location_id': 'LOC005',
    'zone': 'COLD',
    'blocked': False,
    'capacity_cm3': 5000,
    'max_weight_kg': 1
}

print(check_assignment(sku, low_weight_location, quantity=10))