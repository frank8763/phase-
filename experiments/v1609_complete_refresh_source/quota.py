"""Prepare a bounded byte grant before fresh actual-wire acquisition.

No full-tree scan is made by an admitted hot-path write. Credits are charged
conservatively, never replenished by assumed compression or file replacement.
This draft is not complete route admission or a source-freshness certificate.
"""
import importlib.util
import os
from pathlib import Path
import time
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v1432_original_held_byte_quota',Path(__file__).with_name('base_quota.py'));base=importlib.util.module_from_spec(s);s.loader.exec_module(base)

class EvidenceQuota(base.EvidenceQuota):
 def __init__(self,output,limits):
  super().__init__(output,limits);self.grant=None;self.sequence=0;self.write_enforcement_active=False;self.expected_external_names=None;self.spend_credits={}

 def prepare_grant(self,capacity_bytes,*,phase,valid_for_s,external_writers):
  assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
  assert phase in {'STOPPED_EVENT_PREPARATION','BEFORE_ACTUAL5_NATIVE_WIRE','COMPLETE_ZERO_TAIL_OR_CLOSURE','CANONICAL_INITIALIZER_PREPARATION'}
  assert type(capacity_bytes)is int and 0<capacity_bytes<=self.limits['maximum_task_evidence_bytes']
  assert 0<valid_for_s<=(1800 if phase=='STOPPED_EVENT_PREPARATION'else(300 if phase=='COMPLETE_ZERO_TAIL_OR_CLOSURE'else(180 if phase=='CANONICAL_INITIALIZER_PREPARATION'else 2)))
  # Actual integration must supply one independently verified reservation for
  # every live external writer; an empty list only covers a single-writer I/O
  # qualification with no ROS/model/planner/controller processes.
  assert self.write_enforcement_active,'BYTE_GRANT_REQUIRES_ACTUAL_WRITE_INTERCEPTION'
  assert isinstance(external_writers,list)and self.expected_external_names is not None
  names=set()
  for writer in external_writers:
   assert writer['source_and_byte_cap_verified']is True and writer['live']is True
   assert writer['name']not in names and writer['reservation_key']in self.holds
   names.add(writer['name']);assert self.holds[writer['reservation_key']]>=writer['remaining_byte_cap']>=0
  assert names==set(self.expected_external_names),'INCOMPLETE_EXTERNAL_WRITER_RESERVATIONS'
  self.grant=None
  snapshot=base.EvidenceQuota.admit(self,capacity_bytes,'PREPARE_BYTE_GRANT_BEFORE_FRESH_WIRE')
  self.sequence+=1;now=time.monotonic()
  self.grant=dict(sequence=self.sequence,owner_pid=os.getpid(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),phase=phase,prepared_monotonic=now,expires_monotonic=now+valid_for_s,capacity_bytes=capacity_bytes,remaining_bytes=capacity_bytes,maximum_held_bytes=self._held(),external_writer_names=sorted(names),snapshot=snapshot)
  return dict(self.grant)

 def admit(self,pending_bytes,stage):
  grant=self.grant
  if grant is None:return base.EvidenceQuota.admit(self,pending_bytes,stage)
  assert grant['owner_pid']==os.getpid()and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==grant['boot_id'],'BYTE_GRANT_OWNER_OR_BOOT_CHANGED'
  assert time.monotonic()<=grant['expires_monotonic'],'BYTE_GRANT_EXPIRED'
  pending=base.round_block(pending_bytes)
  held=self._held();growth=max(0,held-grant['maximum_held_bytes'])
  assert pending+growth<=grant['remaining_bytes']+sum(self.spend_credits.values()),'BYTE_GRANT_EXHAUSTED'
  charge=growth
  grant['remaining_bytes']-=charge;grant['maximum_held_bytes']=max(held,grant['maximum_held_bytes'])
  proof=dict(stage=stage,grant_sequence=grant['sequence'],charged_bytes=charge,remaining_grant_bytes=grant['remaining_bytes'],unwritten_holds_bytes=held,checked_monotonic=time.monotonic(),full_tree_scan_on_command_path=False)
  self.last=proof;return proof

 def retire_grant(self):
  value=self.grant;self.grant=None
  return None if value is None else dict(value)

 def charge_write(self,path,actual_bytes):
  path=Path(path);assert path.is_relative_to(self.output)and path.parent.resolve().is_relative_to(self.output)and not path.is_symlink()
  assert type(actual_bytes)is int and actual_bytes>=0
  # admit() checks a worst-case future write; only the actual emitted bytes
  # are debited here. No credit is returned after either check or compression.
  self.admit(actual_bytes,'EMIT_ACTUAL_OUTPUT_BYTES:'+path.name)
  remaining=actual_bytes
  for key in list(self.spend_credits):
   amount=min(remaining,self.spend_credits[key]);self.spend_credits[key]-=amount;remaining-=amount
  if self.grant is not None:
   assert remaining<=self.grant['remaining_bytes'],'BYTE_GRANT_ACTUAL_WRITE_EXHAUSTED'
   self.grant['remaining_bytes']-=remaining

 def bind_external_names(self,names):
  assert self.grant is None and len(set(names))==len(names)
  self.expected_external_names=tuple(sorted(names))

 def spend(self,key):
  from contextlib import contextmanager
  @contextmanager
  def scope():
   assert key not in self.spend_credits
   self.spend_credits[key]=self.holds[key]
   try:
    with super(EvidenceQuota,self).spend(key):yield
   finally:self.spend_credits.pop(key,None)
  return scope()
