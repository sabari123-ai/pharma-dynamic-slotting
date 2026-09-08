"""Governance specialization: uncertainty communication and authorised overrides."""
from datetime import datetime, timezone

def confidence_from_margin(margin):
    return 'high' if margin>.20 else 'medium' if margin>.05 else 'low'

def review_queue(recommendations):
    return [r for r in recommendations if str(r.get('confidence','')).lower()=='low' or r.get('override_required')]

def authorised_override(recommendation, user, reason, allowed_roles=('warehouse_manager','quality_supervisor')):
    if user.get('role') not in allowed_roles: raise PermissionError('authorised role required')
    if not reason or not reason.strip(): raise ValueError('override reason is required')
    return {**recommendation,'override_required':True,'override_user':user.get('user_id'),'override_role':user.get('role'),'override_reason':reason.strip(),'override_at':datetime.now(timezone.utc).isoformat()}
# Sample recommendations
recommendations = [
    {
        'sku_id': 'SKU001',
        'confidence': 'high',
        'override_required': False
    },
    {
        'sku_id': 'SKU002',
        'confidence': 'low',
        'override_required': False
    },
    {
        'sku_id': 'SKU003',
        'confidence': 'medium',
        'override_required': True
    }
]

# Test confidence_from_margin()
print("Confidence tests:")
print(confidence_from_margin(0.25))
print(confidence_from_margin(0.10))
print(confidence_from_margin(0.03))

# Test review_queue()
print("\nReview queue:")
print(review_queue(recommendations))

# Test authorised_override()
user = {
    'user_id': 'USR001',
    'role': 'warehouse_manager'
}

updated = authorised_override(
    recommendations[1],
    user,
    "Manual review required due to unusual demand pattern"
)

print("\nAuthorised override:")
print(updated)