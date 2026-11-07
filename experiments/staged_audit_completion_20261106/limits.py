"""Frozen per-stage budget rules and independent transition prerequisites."""
import math

def pilot_limits(deadline,now):
 hard=math.floor(deadline-now-200);soft=hard-60
 assert soft>=300,'INSUFFICIENT_PILOT_BUDGET'
 return dict(soft=soft,hard=hard,outer=hard+5)

def can_transition(final):
 return bool(final.get('development_passed')and final.get('source_and_decompressed_sha_verified')and final.get('independent_audit_passed')and final.get('complete_chain_passed')and final.get('native_replay_exact')and final.get('source_unchanged'))

def model_fits(deadline,now,cap):return now+cap+3<deadline
