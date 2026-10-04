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
