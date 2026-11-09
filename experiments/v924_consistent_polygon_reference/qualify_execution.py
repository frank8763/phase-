"""Production ingress + native step + independent audit, recording stub only."""
import ast,copy,importlib.abc,json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v924_consistent_polygon_reference'
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','factory','vehicle','physical','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Block());sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from native_contract import Startup,Previous
from handshake import NODES
from ingress_audit import check
s=Startup('fixture');arm=dict(kind='arm',run_id='fixture',native_tick=0,sim_time=0.,states={n:3 for n in NODES},checked_at={n:100. for n in NODES},issued_at=100.)
s.receive(arm,100.,0,0.)
p=dict(passed=True,v=.1,w=0.,body_native_tick=0,source_native_tick=0,body=[0.,0.,0.,.1,0.],body_age_s=.001,issued_at=100.,residual_position_m=.02,residual_angle_rad=.035,terminal_cycle_qualified=True,terminal_cycle_lower_m=.2)
packet=dict(kind='command',run_id='fixture',sequence=1,issued_at=100.,v=.1,w=0.,tube=p);s.receive(packet,100.001,0,0.)
class Recorder:
 def __init__(self):self.count=0;self.records=[];self.commands=[]
 def body(self):return [.1*min(self.count*.01,.2),0.,0.,0.,0.]
 def step(self,v,w,stale):self.commands.append([v,w,stale]);self.count+=1;self.records.append(self.body())
v=Recorder();proofs=[p]
for i in range(300):
 if i in [7,10]:
  q=copy.deepcopy(packet);q['sequence']=2 if i==7 else 3;q['issued_at']=100.002 if i==7 else 100.003;q['tube']['issued_at']=q['issued_at'];proofs.append(q['tube']);s.receive(q,100.+i*.01,i,i*.01)
 s.step(v,100.+i*.01)
data=dict(receipts=s.receipts,execution=s.execution);baseline=check(data,proofs,np.array(v.records),'fixture')
checks=dict(independent_300step_positive=baseline['passed'],two_delayed_commands_discarded=baseline['late_new_discards']==2,old_motion_expires_at_200ms=all(x==[0.,0.,True]for x in v.commands[21:]),old_anchor_never_reset=s.command['sequence']==1 and s.command['issued_at']==100.)
for label,mutate in [('late_admitted',lambda d:d['receipts'][2].update(decision='ACCEPTED',retained_sequence=2)),('expired_motion_replayed',lambda d:d['execution'][30].update(controls=[.1,0.,False])),('old_anchor_replaced',lambda d:d['execution'][8].update(sequence=2)),('missing_native_step',lambda d:d['execution'].pop(50)),('unrecorded_accept',lambda d:d['receipts'][1]['packet']['tube'].update(issued_at=99.)),('future_timestamp',lambda d:d['receipts'][1].update(received_at=99.))]:
 d=copy.deepcopy(data);mutate(d)
 try:failed=not check(d,proofs,np.array(v.records),'fixture')['passed']
 except (AssertionError,KeyError,IndexError):failed=True
 checks[label+'_negative']=failed
r=np.array(v.records);r[150,0]+=.1;checks['actual_position_tamper_negative']=not check(data,proofs,r,'fixture')['passed']
# The old loop timestamps before socket.read. A newly issued queued packet can
# then appear to be from the future. Production now samples per received packet.
src=ast.parse((C/'native_loop.py').read_text());calls=[n for n in ast.walk(src)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='receive']
checks['both_real_receive_sites_sample_after_read']=len(calls)==2 and all(ast.unparse(c.args[1])=='time.monotonic()'for c in calls)
x=Previous('fixture');x.phase='RUNNING';q=copy.deepcopy(packet);q['issued_at']=100.001;q['tube']['issued_at']=100.001
try:x.receive(q,100.,0,0.)
except Exception as e:checks['previous_sample_before_read_failure']='COMMAND_DELIVERY_BUDGET'in str(e)
else:checks['previous_sample_before_read_failure']=False
x=Startup('fixture');x.phase='RUNNING';x.receive(q,100.002,0,0.);checks['sample_after_read_accepts_timely_packet']=x.command==q
report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,recording_stub_only=True,independent_audit_baseline=baseline,historical_failed_packet_unknown=True)
(O/'INGRESS_AUDIT_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['passed']
