"""Journaled ingress; late NEW motion is never admitted or re-timestamped."""
import math
from certified_contract import Startup as Previous
from handshake import require
from cycle_backup import retained_allowed
class Startup(Previous):
    def _journals(self):
        if not hasattr(self,'receipts'):self.receipts=[];self.execution=[]
    def receive(self,packet,now,native_tick,sim_time):
        self._journals()
        before=None if self.command is None else self.command['sequence']
        row=dict(packet=packet,received_at=now,native_tick=native_tick,sim_time=sim_time,prior_sequence=before)
        try:
            if packet.get('kind')!='command':
                super().receive(packet,now,native_tick,sim_time);row['decision']='CONTROL_EVENT';return
            require(packet.get('run_id')==self.run_id,'FOREIGN_RUN')
            require(self.phase=='RUNNING','COMMAND_BEFORE_ARM')
            sequence=packet.get('sequence');require(type(sequence)is int and sequence>self.last_sequence,'NONINCREASING_COMMAND_SEQUENCE')
            proof=packet.get('tube',{});require(proof.get('passed')is True,'COMMAND_WITHOUT_TUBE')
            require(proof['v']==packet['v']and proof['w']==packet['w'],'COMMAND_PROOF_MISMATCH')
            require(proof['issued_at']==packet['issued_at'],'COMMAND_TIME_MISMATCH')
            require(all(type(packet.get(k))in(int,float)and math.isfinite(packet[k])for k in ['v','w','issued_at']),'NONFINITE_BODY_COMMAND')
            require(proof['source_native_tick']<=proof['body_native_tick']<=native_tick,'COMMAND_FUTURE_SOURCE')
            age=now-packet['issued_at'];require(math.isfinite(now)and age>=0.,'FUTURE_COMMAND_TIME')
            if age>.05:
                require(age<=.2,'STALE_OR_FUTURE_COMMAND')
                old=None if self.command is None else self.command['tube'];elapsed=0 if old is None else (native_tick-old['body_native_tick'])*.01
                require(old is not None and retained_allowed(old,elapsed),'LATE_COMMAND_WITHOUT_VALID_BACKUP')
                self.last_sequence=sequence;row['decision']='LATE_NEW_COMMAND_DISCARDED'
                self.events.append(dict(event=row['decision'],at=now,native_tick=native_tick,new_sequence=sequence,delivery_age_s=age,retained_sequence=before,retained_anchor_tick=old['body_native_tick'],retained_issued_at=old['issued_at']))
                return
            super().receive(packet,now,native_tick,sim_time);row['decision']='ACCEPTED'
        except BaseException as e:row.update(decision='REJECTED_ABORT',error=repr(e));raise
        finally:
            row['retained_sequence']=None if self.command is None else self.command['sequence'];self.receipts.append(row)
    def step(self,vehicle,now):
        self._journals()
        row=dict(native_tick=vehicle.count+1,at=now,phase=self.phase,sequence=None if self.command is None else self.command['sequence'],controls=list(self.controls(now)),completed=False)
        self.execution.append(row);super().step(vehicle,now);row['completed']=True
