"""Real production receiver/authority and independent audit negatives, no models."""
import ast,copy,hashlib,importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v931_deadband_consistent_mppi'
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in{'mujoco','torch','vehicle','factory','physical'}:raise AssertionError('MODEL_IMPORT')
sys.meta_path.insert(0,Block());sys.path.insert(0,str(C))
from native_contract import Startup
from handshake import ProtocolError,NODES
from ingress_audit import audit
import authority
checks={}
def reject(name,call):
 try:call()
 except (AssertionError,ProtocolError,KeyError,ValueError,TypeError):checks[name]=True;return
 checks[name]=False;raise AssertionError(name)
for p in C.rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks['all_source_ast']=True
s=Startup('x');arm=dict(run_id='x',kind='arm',native_tick=0,sim_time=0.,issued_at=10.,states={n:3 for n in NODES},checked_at={n:10. for n in NODES});s.receive(arm,10.,0,0.)
packet=dict(run_id='x',kind='command',sequence=0,issued_at=10.,v=.1,w=.05);s.receive(packet,10.01,0,0.)
checks['command_accepted']=s.controls(10.1)==(.1,.05,False)
checks['expired_brakes']=s.controls(10.21)==(0.,0.,True)
reject('old_sequence',lambda:s.receive(packet,10.02,0,0.))
for name,change in [('wrongrun',dict(run_id='z')),('unexecutable',dict(v=0.,w=.1)),('deadband_yaw',dict(v=-.000986058847,w=-.000747014245)),('nan',dict(v=float('nan'))),('late',dict(issued_at=9.)),('future',dict(issued_at=11.))]:
 q=dict(packet,sequence=1,**change);reject(name,lambda q=q:s.receive(q,10.02,0,0.))
s.receive(dict(run_id='x',kind='stop'),10.03,0,0.);q=dict(packet,sequence=1,issued_at=10.04);s.receive(q,10.05,0,0.);checks['poststop_cannot_actuate']=s.controls(10.05)==(0.,0.,True)
reject('poststop_wrongrun',lambda:s.receive(dict(q,run_id='z'),10.06,0,0.))
J=dict(receipts=[dict(received_at=10.,packet=arm,decision='ACCEPTED'),dict(received_at=10.01,packet=packet,decision='ACCEPTED')],execution=[dict(native_tick=1,at=10.02,controls=[.1,.05,False],sequence=0)])
B=[[10.02,.1,.05,0.,0.,False]];checks['independent_journal']=audit(J,B,'x')['passed'];bad=copy.deepcopy(B);bad[0][1]=.09;reject('journal_ctrl_tamper',lambda:audit(J,bad,'x'))
bad=copy.deepcopy(J);bad['receipts'][1]['received_at']=10.3;reject('journal_time_tamper',lambda:audit(bad,B,'x'))
start=time.time();auth=dict(scope='V931_DEADBAND_BASELINE',models_authorized=True,started_unix=start-1,deadline_unix=start+500,source_freeze_sha256='f');saved=authority.read
authority.read=lambda p:auth if Path(p).name=='AUTHORIZATION.json'else dict(started_unix=auth['started_unix'],deadline_unix=auth['deadline_unix'])if Path(p).name=='ROUND_WINDOW.json'else dict(passed=True)
checks['root_authority']=authority.root_authorized(start,'f')==auth
reject('wrong_freeze',lambda:authority.root_authorized(start,'bad'));reject('expired_root',lambda:authority.root_authorized(start+500,'f'))
auth['scope']='WRONG';reject('wrong_scope',lambda:authority.root_authorized(start,'f'));authority.read=saved
proof=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,at=time.time());(O/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof));assert proof['passed']
