"""Nominal baseline receiver; original native safety, no RP-CCR proof claim."""
import math,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from handshake import Startup as Original,require
class Startup(Original):
 def _journals(self):
  if not hasattr(self,'receipts'):self.receipts=[];self.execution=[]
 def receive(self,p,now,tick,stamp):
  self._journals();record=dict(received_at=now,native_tick=tick,packet=p)
  try:
   require(p.get('run_id')==self.run_id,'FOREIGN_RUN')
   if p.get('kind')=='command':
    require(type(p.get('issued_at'))in(int,float)and math.isfinite(p['issued_at'])and 0<=now-p['issued_at']<=.2,'COMMAND_RECEIPT_AGE')
    require(all(type(p.get(k))in(int,float)and math.isfinite(p[k])for k in ['v','w']),'NONFINITE_BODY_COMMAND')
    require(abs(p['v'])<=.100001 and abs(p['w'])<=abs(p['v'])/1.32+1e-6,'UNEXECUTABLE_BODY_COMMAND')
    from twist_contract import require_representable
    require_representable(p['v'],p['w'])
    if self.phase=='STOPPING':record['decision']='POST_STOP_COMMAND_IGNORED';return
   super().receive(p,now,tick,stamp);record['decision']='ACCEPTED'
  except BaseException as e:record.update(decision='ABORT',error=repr(e));raise
  finally:self.receipts.append(record)
 def step(self,vehicle,now):
  self._journals();before=vehicle.count;control=self.controls(now);super().step(vehicle,now)
  self.execution.append(dict(native_tick=before+1,at=now,controls=list(control),sequence=None if self.command is None else self.command['sequence']))
  b=vehicle.body();require(abs(b[3])<=.13 and abs(b[4])<=.16,'QUALIFIED_BODY_SPEED_EXCEEDED')
