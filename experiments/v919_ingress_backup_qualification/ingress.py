"""Unexecuted native-ingress candidate. Zero-model qualification only.
Preserve the .05s new-command delivery limit; a late NEW packet cannot erase
an already valid old stationary/braking resource. Never admit late actuation.
"""
import math,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'experiments/v918_reference_backup_balance'),str(R/'experiments/v862_ready_static')]
from native_contract import Startup as Previous
from handshake import require
from cycle_backup import retained_allowed
class Startup(Previous):
 def receive(self,packet,now,native_tick,sim_time):
  if packet.get('kind')!='command':return super().receive(packet,now,native_tick,sim_time)
  require(packet.get('run_id')==self.run_id,'FOREIGN_RUN')
  require(self.phase=='RUNNING','COMMAND_BEFORE_ARM')
  sequence=packet.get('sequence');require(type(sequence)is int and sequence>self.last_sequence,'NONINCREASING_COMMAND_SEQUENCE')
  proof=packet.get('tube',{});require(proof.get('passed')is True,'COMMAND_WITHOUT_TUBE')
  require(proof['v']==packet['v']and proof['w']==packet['w'],'COMMAND_PROOF_MISMATCH')
  require(proof['issued_at']==packet['issued_at'],'COMMAND_TIME_MISMATCH')
  require(all(isinstance(packet.get(k),(int,float))and math.isfinite(packet[k])for k in ['v','w','issued_at']),'NONFINITE_BODY_COMMAND')
  require(proof['source_native_tick']<=proof['body_native_tick']<=native_tick,'COMMAND_FUTURE_SOURCE')
  age=now-packet['issued_at'];require(math.isfinite(now)and age>=0.,'FUTURE_COMMAND_TIME')
  if age>.05:
   require(age<=.2,'STALE_OR_FUTURE_COMMAND')
   old=None if self.command is None else self.command['tube'];elapsed=0 if old is None else (native_tick-old['body_native_tick'])*.01
   require(old is not None and retained_allowed(old,elapsed),'LATE_COMMAND_WITHOUT_VALID_BACKUP')
   self.last_sequence=sequence
   self.events.append(dict(event='LATE_NEW_COMMAND_DISCARDED',at=now,native_tick=native_tick,new_sequence=sequence,new_issued_at=packet['issued_at'],delivery_age_s=age,retained_anchor_tick=old['body_native_tick'],retained_issued_at=old['issued_at']))
   return
  return super().receive(packet,now,native_tick,sim_time)
