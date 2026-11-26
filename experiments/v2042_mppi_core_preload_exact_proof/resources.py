"""Stage grants within unchanged task/root caps; terminal ownership is separate."""
import json
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

def save_terminal(quota,value,save):
 # Closure only: no model/actuator/source command follows. Retiring an expired
 # grant restores original exact all-runs/holds checking for this small record.
 from quota import base
 raw=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False,default=lambda x:x.tolist()).encode()+b'\n'
 assert TERMINAL_KEY in quota.holds
 assert 2*base.round_block(len(raw))+2*base.BLOCK<=quota.holds[TERMINAL_KEY],'TERMINAL_RECORD_EXCEEDS_RESERVED_CAP'
 quota.retire_grant()
 with quota.spend(TERMINAL_KEY):answer=save()
 quota.release(TERMINAL_KEY)
 return answer

def prepare_closed_capture(quota,phase,inflight):
 # Only after the last actuator request and before first complete-state save.
 # No old grant credit or assumed compressed-file discount is carried forward.
 assert phase in {'normal','error_stop'} and not inflight,'CLOSE_REFRESH_REQUIRES_QUIESCENT_ACTUAL'
 assert TERMINAL_KEY in quota.holds and 'canonical-physical-prefix'in quota.holds,'CLOSE_REFRESH_HOLDS_REQUIRED'
 return prepare(quota,'COMPLETE_ZERO_TAIL_OR_CLOSURE',ttl=300)


def prepare_nplus1_after_capture(quota,phase,inflight,evidence_saved):
 # Only quiescent closure after ORIGINAL CaptureBudget.finish returned and
 # released its own exact pending hold. No model/control work follows capture.
 assert phase in {'normal','error_stop'} and not inflight,'NPLUS1_REQUIRES_QUIESCENT_ACTUAL'
 assert evidence_saved is True,'NPLUS1_REQUIRES_COMPLETE_PHYSICAL_CAPTURE'
 assert TERMINAL_KEY in quota.holds,'NPLUS1_TERMINAL_HOLD_REQUIRED'
 assert 'canonical-physical-prefix'not in quota.holds,'NPLUS1_CANNOT_SPEND_PENDING_CAPTURE'
 return prepare(quota,'COMPLETE_ZERO_TAIL_OR_CLOSURE',ttl=300)
