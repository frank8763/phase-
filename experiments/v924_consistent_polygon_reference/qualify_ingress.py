"""Actual saved V918 command fields + recording-state native ingress, zero models."""
import copy,gzip,importlib.abc,json,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v924_consistent_polygon_reference';S=O/'saved'
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Block());sys.path.insert(0,str(C));from native_contract import Startup,Previous
rows=json.loads(gzip.decompress((S/'COMMAND_TUBES.json.gz').read_bytes()));row=rows[-2];proof=row['proof'];tick=proof['body_native_tick'];issued=proof['issued_at']
packet=dict(kind='command',run_id='qualification',sequence=2,issued_at=issued,v=proof['v'],w=proof['w'],tube=proof)
# Deliberate recorded-field late arrival reproduces the strict previous failure.
def make(cls=Startup,old=None):
 x=cls('qualification');x.phase='RUNNING';x.armed_at=issued-60;x.last_sequence=1;x.command=dict(packet,sequence=1,tube=copy.deepcopy(proof if old is None else old));return x
checks={}
x=make(Previous)
try:x.receive(packet,issued+.069,tick+7,0.)
except Exception as e:checks['previous_delivery_failure_reproduced']='COMMAND_DELIVERY_BUDGET'in str(e)
else:checks['previous_delivery_failure_reproduced']=False
x=make();anchor=x.command;x.receive(packet,issued+.069,tick+7,0.);checks['late_packet_discarded_without_new_actuation']=x.command is anchor and x.last_sequence==2 and len(x.events)==1
checks['old_anchor_and_issue_time_unchanged']=x.command['tube']['body_native_tick']==tick and x.command['issued_at']==issued
x=make();x.receive(packet,issued+.01,tick+1,0.);checks['timely_packet_uses_original_receiver']=x.command['sequence']==2
for label,mutate,now,old in [
 ('foreign',lambda p:p.update(run_id='other'),issued+.069,None),
 ('sequence_replay',lambda p:p.update(sequence=1),issued+.069,None),
 ('unqualified',lambda p:p['tube'].update(passed=False),issued+.069,None),
 ('mismatched_command',lambda p:p.update(v=.1),issued+.069,None),
 ('future_source',lambda p:p['tube'].update(source_native_tick=tick+100),issued+.069,None),
 ('future_timestamp',lambda p:None,issued-.001,None),
 ('beyond_200ms',lambda p:None,issued+.201,None),
 ('expired_finite_backup',lambda p:None,issued+.069,dict(proof,body_native_tick=tick-1000,terminal_cycle_qualified=False)),
 ('invalid_backup',lambda p:None,issued+.069,dict(proof,passed=False))]:
 x=make(old=old);p=copy.deepcopy(packet);mutate(p)
 try:x.receive(p,now,tick+7,0.)
 except Exception:checks[label+'_rejected']=True
 else:checks[label+'_rejected']=False
# Sampling receive time for every packet is required in future integration.
checks['production_entry_uses_local_contract']="from native_contract import Startup" in (C/'native_worker.py').read_text()
report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,physical_integration_implemented=True,scope='Integrated ingress candidate with recorded command fields and constructed69ms delay; exact original failing packet/sequence not captured, no claim of exact historical delay reproduction.')
(O/'INGRESS_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['passed']
