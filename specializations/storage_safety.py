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
