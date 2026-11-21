"""New lazy EventPeer real isolated ROS lifecycle; no analytical model calls."""
import ast
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoPhysical(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('MODEL_PEER_LIFECYCLE_NO_PHYSICAL:'+name)

def main():
 assert sys.argv[1:]==['--entry-check']and os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'MODEL_PEER_QUALIFICATION.json').exists()
 os.chdir(R);sys.meta_path.insert(0,NoPhysical());calls=[]
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'}:calls.append(frame.f_code.co_name);raise AssertionError('MODEL_PEER_LIFECYCLE_ZERO_CONSTRUCTOR_OR_STEP')
 sys.setprofile(forbid);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==5
 io=exact('v1424_peer_atomic_io',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');source=exact('v1424_real_lazy_model_peer',C/'model_peer.py')
 current_file=R/'runs/v1410_scalar_feedback_witness/model/CURRENT_INPUT.json';current=json.loads(current_file.read_text());assert current['method_spec']['method']=='ORIGINAL_TWO_ARC_CAPTURE_THEN_ORIGINAL_RPP'
 out=O/'model_peer';out.mkdir();folder=out/'bridge_events/event0000';folder.mkdir(parents=True);(folder/'CURRENT_INPUT.json').write_bytes(current_file.read_bytes());owner_namespace=os.readlink('/proc/self/ns/net');started=time.monotonic();peer=None;result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,software_saved_input_not_actual_wire=True,old_numeric_rounds_not_reexecuted=True)
 def check(stage,count):
  assert count==0 and time.monotonic()-started<60 and time.time()<1795395600 and time.monotonic()<parent['hard_stop_monotonic']
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   peer=source.EventPeer(out,run_id='v1425_current_event_peer_lifecycle_software',check_budget=check,atomic=io.atomic);peer.begin(0)
   reply=peer.command(native_tick=current['origin']['native_tick'],body=current['origin']['body'],input_sha256=current['input_sha256'])
   assert reply['kind']in {'ORIGINAL_RPP_MODELED_COMMAND','RPP_ACTION_DONE'}and reply['input_sha256']==current['input_sha256']and reply['native_tick']==current['origin']['native_tick']and reply['body']==current['origin']['body']and reply['not_measured_response']is True
   handshake=json.loads((folder/'MODELED_PEER_INNER_NAMESPACE.json').read_text());namespace=handshake['network_namespace'];assert namespace!=owner_namespace and json.loads((folder/'MODELED_PEER_NAMESPACE_VERIFIED.json').read_text())['passed'],'MODELED_PEER_NOT_IN_PRIVATE_NET_NAMESPACE'
   result.update(passed=True,current_input_sha256=current['input_sha256'],input_file_sha256=hashlib.sha256(current_file.read_bytes()).hexdigest(),reply=reply,owner_network_namespace=owner_namespace,modeled_peer_network_namespace=namespace,independent_private_network_namespace=True)
  except BaseException as exc:
   import traceback
   result.update(passed=False,error=repr(exc),traceback=traceback.format_exc())
  finally:
   if peer is not None:
    try:peer.close_event();result['peer_closed_events']=peer.closed_events
    except BaseException as exc:result.update(passed=False,peer_close_error=repr(exc))
   result.update(closed=True,wall_s=time.monotonic()-started,no_model_calls=not calls);io.atomic(O/'MODEL_PEER_QUALIFICATION.json',result)
  print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
