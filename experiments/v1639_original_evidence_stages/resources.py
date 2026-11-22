"""Stage grants within unchanged task/root caps; terminal ownership is separate."""
import time
TERMINAL_KEY='original-contract-terminal-metadata'
TERMINAL_BYTES=1024**2

def reserve_terminal(quota):
 assert quota.grant is None and TERMINAL_KEY not in quota.holds
 quota.hold(TERMINAL_KEY,TERMINAL_BYTES)

def prepare(quota,stage,*,cap=None,ttl=1800):
 quota.retire_grant()
 if cap is None:
  # Use actual single-writer allocation, outstanding holds, and the original
  # error reserve; no credit for assumed compression/replacement is returned.
  from quota import base
  own=base.used(quota.output)
  available=quota.limits['maximum_task_evidence_bytes']-own-quota._held()-base.ERROR_RESERVE-2*base.BLOCK
  cap=(available//base.BLOCK)*base.BLOCK
 assert type(cap)is int and cap>0,'NO_RESOURCE_GRANT_HEADROOM'
 return quota.prepare_grant(cap,phase=stage,valid_for_s=ttl,external_writers=[])

def save_terminal(quota,save):
 # Closure only: no model/actuator/source command follows. Retiring an expired
 # grant restores original exact all-runs/holds checking for this small record.
 quota.retire_grant()
 assert TERMINAL_KEY in quota.holds
 with quota.spend(TERMINAL_KEY):answer=save()
 quota.release(TERMINAL_KEY)
 return answer
