"""Current bounded modeled RPP namespace/callback/closure, zero models."""
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
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoPhysical(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy','coupled_model','prediction'}:raise AssertionError('BOUNDED_PEER_ZERO_MODELS:'+name)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'PEER_QUALIFICATION.json').exists();os.chdir(R);sys.meta_path.insert(0,NoPhysical())
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py'}:raise AssertionError('BOUNDED_PEER_NO_CONSTRUCTOR_STEP_OR_ALLOCATOR')
 sys.setprofile(forbid);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==5
 io=exact('v1436_atomic_peer_receipts',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');source=exact('v1436_actual_bounded_peer',C/'model_peer.py')
 input_file=R/'runs/v1410_scalar_feedback_witness/model/CURRENT_INPUT.json';current=json.loads(input_file.read_text());assert current['method_spec']['method']=='ORIGINAL_TWO_ARC_CAPTURE_THEN_ORIGINAL_RPP'
 identity=hashlib.sha256((O/'PEER_QUALIFICATION_CLAIM.json').read_bytes()).hexdigest();out=O/'bounded_peer';out.mkdir();folder=out/'bridge_events/event0000';folder.mkdir(parents=True);(folder/'CURRENT_INPUT.json').write_bytes(input_file.read_bytes())
 approval=dict(models_authorized=False,scope='ZERO_MODEL_MODELED_ROS_WRITER_QUALIFICATION',source_identity=identity);io.atomic(out/'APPROVAL.json',approval)
 registry=dict(purpose='ZERO_MODEL_MODELED_ROS_WRITER_QUALIFICATION',source_identity=identity,approval_sha256=hashlib.sha256((out/'APPROVAL.json').read_bytes()).hexdigest(),writers=dict(MODELED_ROS=dict(maximum_bytes=16*1024**2,source_hook_coverage_qualified=False)))
 io.atomic(out/'EXTERNAL_WRITER_RESERVATIONS.json',registry);os.environ['PHASE_BOUNDED_SOURCE_ID']=identity
 start=time.monotonic();peer=None;result=dict(passed=False,closed=False,models=0,analytical_integrations=0,allocator_recomputations=0,physical_native=0,actual_replay_native=0,source_input_saved_fixture_not_actual_wire=True,old_numeric_rounds_not_reexecuted=True,qualification_authority_explicitly_models_false_and_hook_coverage_false=True)
 def check(stage,count):assert count==0 and time.monotonic()-start<60 and time.time()<1795395600 and time.monotonic()<parent['hard_stop_monotonic']
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   peer=source.EventPeer(out,run_id='v1436_BOUND_OUTPUT_MODELED_RPP_FIXTURE',check_budget=check,atomic=io.atomic);peer.begin(0)
   reply=peer.command(native_tick=current['origin']['native_tick'],body=current['origin']['body'],input_sha256=current['input_sha256'])
   assert reply['kind']in {'ORIGINAL_RPP_MODELED_COMMAND','RPP_ACTION_DONE'}and reply['input_sha256']==current['input_sha256']and reply['body']==current['origin']['body']and reply['not_measured_response']is True
   inner=json.loads((folder/'MODELED_PEER_INNER_NAMESPACE.json').read_text());assert inner['network_namespace']!=os.readlink('/proc/self/ns/net')and inner['actual_cpu']==[3]
   assert inner['active_bounded_peer_sha256']==hashlib.sha256((C/'modeled_peer.py').read_bytes()).hexdigest()
   assert (folder/'MODELED_PEER_INNER_NAMESPACE.json').stat().st_size<=8192
   result.update(passed=True,reply=reply,independent_inner_namespace_verified=True,active_bounded_peer_source_verified=True,original_frozen_RPP_policy_sha256=inner['source_peer_sha256'],startup_handshake_bytes_covered_by16KiB_initial_writer_reserve=True)
  except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
  finally:
   if peer is not None:
    try:
     peer.close_event();result['closed_events']=peer.closed_events;closed=peer.closed_events[-1]
     assert closed['returncode']==0 and closed['inner_peer_closure']['closed']and closed['inner_peer_closure']['controller_exited']
     assert closed['inner_peer_closure']['synthetic_scan_messages']==0
     result['inner_controller_peer_and_wrapper_exit_verified']=True
    except BaseException as exc:result.update(passed=False,close_error=repr(exc))
   counter=out/'WRITER_MODELED_ROS_BYTES.json'
   if counter.exists():
    value=json.loads(counter.read_text());result['writer_budget']=value
    if value['charged_bytes']>16*1024**2:result['passed']=False
   else:result.update(passed=False,writer_counter_missing=True)
   result.update(closed=True,wall_s=time.monotonic()-start,physical_admission=False,source_hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.iterdir()if p.is_file()});io.atomic(O/'PEER_QUALIFICATION.json',result)
  print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
