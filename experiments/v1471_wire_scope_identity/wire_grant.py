"""Reuse conservatively debited grants before sampling, never relax source age."""
import os
from pathlib import Path
import time

def before_wire(quota,*,native_tick):
 assert type(native_tick)is int and native_tick>=0
 grant=quota.grant
 if grant is not None:
  assert grant['owner_pid']==os.getpid()and grant['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'WIRE_GRANT_OWNER_OR_BOOT_CHANGED'
  permitted=grant['phase']=='BEFORE_ACTUAL5_NATIVE_WIRE'or(grant['phase']=='CANONICAL_INITIALIZER_PREPARATION'and native_tick==0)
  if permitted and time.monotonic()<grant['expires_monotonic']:
   # This does not replenish credits or assume compression. Every actual
   # write still debits quota. Held-index growth and external full role caps
   # remain covered by the same previously admitted worst-case grant.
   proof=quota.admit(65536,'REUSE_ALREADY_ADMITTED_GRANT_BEFORE_FRESH_WIRE')
   return dict(reused=True,phase=grant['phase'],sequence=grant['sequence'],native_tick=native_tick,proof=proof)
 quota.retire_grant()
 value=quota.prepare_grant(8*1024**2,phase='BEFORE_ACTUAL5_NATIVE_WIRE',valid_for_s=2,external_writers=quota.external_writers)
 return dict(reused=False,phase=value['phase'],sequence=value['sequence'],native_tick=native_tick)
