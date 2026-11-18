"""Explicit binding of the unchanged full native auditor."""
from worker_context import *
_original=load('v1209_frozen_native_audit',R/'experiments/v1204_goal_audit_worker/native_audit.py')
audit=_original.audit
