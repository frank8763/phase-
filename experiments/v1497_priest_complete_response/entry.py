"""Once saved-current provenance/source seams only; forbid model execution."""
import copy
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def put(p,v):
 raw=json.dumps(v,indent=2,allow_nan=False)+'\n';t=p.with_suffix(p.suffix+'.tmp');t.write_text(raw);t.replace(p)
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'jax','jaxlib','torch','mujoco','rclpy','vehicle','factory'}:raise AssertionError('SOURCE_ONLY_ENTRY_FORBIDDEN_IMPORT:'+name)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[4]
 with(O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0),f)
 start=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('SAVED_INPUT_SOURCE_90S')));signal.alarm(90)
 sys.meta_path.insert(0,NoModels())
 assert time.time()<1795395600
 exact('v1497_existing_immutable_guard',R/'experiments/v1492_priest_optimizer_worker/common.py').guard(O)
 def profile(frame,event,arg):
  if event=='call'and frame.f_code.co_filename.startswith(str(R)+'/')and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','coupled_control.py','vehicle_control.py','kernel.py'}:raise AssertionError('NO_SOURCE_ENTRY_MODEL_OR_ALLOCATOR_CALL')
 sys.setprofile(profile);sources={};negatives=[];completed=[]
 result=dict(passed=False,closed=False,models=0,physical_native=0,optimizer_calls=0,Allocator_recomputations=0,ownreplay_native=0,scope='SAVED_ACTUAL_INPUT_NEW_METHOD_SOURCE_ONLY',actual_current_capture=False,proposal_fixture_not_optimizer=True)
 def reject(name,fn):
  try:fn()
  except (AssertionError,KeyError,RuntimeError,ValueError,FileNotFoundError):negatives.append(name);return
  raise AssertionError('SAVED_RESPONSE_SOURCE_NEGATIVE_ACCEPTED:'+name)
 try:
  parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==7
  before_parent=(R/'runs/v1382_weekend_campaign/LEDGER.json').read_bytes()
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   sources=read(R/'runs/v1493_priest_numeric_once/NUMERIC_SOURCE_FREEZE.json')['files'].copy()
   for p in C.iterdir():
    if p.is_file():sources[str(p.relative_to(R))]=sha(p)
   root=R/'runs/v1479_retirement_scope_binding';event=root/'first_event/bridge_events/event0000'
   paths=dict(original_event_input=event/'CURRENT_INPUT.json',original_setup=event/'SETUP.json',full_states=root/'first_event/FULL_STATE_NPLUS1.npz',journal=root/'first_event/ACTUAL_OWNER_JOURNAL.jsonl',remote_index=root/'actual_runtime_delivery/ARCHIVE_INDEX.json',remote_proof=root/'actual_runtime_delivery/FULL_REMOTE_VERIFIED.json')
   for p in paths.values():sources[str(p.relative_to(R))]=sha(p)
   prepared=exact('v1497_entry_prepared_original_core',R/'experiments/v1485_priest_current_polynomial_seam/core_identity.py').PreparedCore(source_manifest=sources)
   saved=exact('v1497_new_saved_input_adapter',C/'saved_input.py');current,setup=saved.capture(prepared=prepared,**paths)
   assert current['input_role']=='SAVED_ACTUAL_INPUT_MODEL_ONLY'and current['saved_actual_input_not_fresh_wire']and not current['physical_admission']
   model=O/'saved_input';model.mkdir();put(model/'CURRENT_INPUT.json',current);put(model/'SETUP.json',setup);completed.append('saved_fullstate_body_encoder_control_modegear_snapshot_provenance')
   hint=current['author_initial_boundary_hint'];position=current['rear_pose_world'];velocity=current['rear_velocity_world'];acc=hint['acceleration_hint_world']
   coefficients=[]
   for a,v,g in zip(position[:2],velocity,acc):
    arr=[a+v*i for i in range(11)];arr[0]=a;arr[1]=a+v;arr[2]=2*arr[1]-arr[0]+g*100/90;coefficients.append(arr)
   reply=dict(kind='PRIEST_AUTHOR_POLYNOMIAL_PROPOSAL',schema=1,run_id=current['run_id'],input_sha256=current['input_sha256'],core_identity_sha256=current['core_identity_sha256'],origin_native=current['fixed_origin_native'],origin_sim_time=current['fixed_origin_sim_time'],horizon_s=10.,coordinate_frame='REAR_AXLE_WORLD_XY',gear=current['next_segment']['gear'],coefficients_x=coefficients[0],coefficients_y=coefficients[1],optimizer_accounting=dict(optimizer_calls=None,iterations_completed=None,mathematical_candidate_evaluations=None,inflight_unknown=False,author_core_source_sha256=current['core_identity']['author_members'][0]['sha256']))
   output=exact('v1497_entry_frozen_proposal_math',R/'experiments/v1485_priest_current_polynomial_seam/candidate_output.py');proposal=output.bind(current,reply)
   bridge=exact('v1497_entry_new_model_binding',C/'model_bridge.py');binding=bridge.bind_input(current,proposal);assert not binding['actual_admission']
   gen=exact('v1497_new_producer_source',C/'generator.py');audit=exact('v1497_new_fresh_auditor_source',C/'audit.py');completed.append('producer_and_independent_audit_exact_source_import_no_modelbinding')
   reject('unregistered_response_model',lambda:bridge.authorize(current,proposal,dict(models_authorized=False),lock))
   wrong=copy.deepcopy(proposal);wrong['input_sha256']='0'*64;reject('changed_proposal_identity',lambda:bridge.bind_input(current,wrong))
   wrong=copy.deepcopy(current);wrong['fixed_origin_native']+=1;reject('changed_current_identity',lambda:bridge.bind_input(wrong,proposal))
   wrong=copy.deepcopy(current);wrong['causal_snapshot']['periodic']=None;wrong['causal_snapshot_sha256']=digest(wrong['causal_snapshot']);wrong.pop('input_sha256');wrong['input_sha256']=digest(wrong);fake=copy.deepcopy(proposal);fake['input_sha256']=wrong['input_sha256'];fake['reply']['input_sha256']=wrong['input_sha256'];fake['reply']['origin_native']=wrong['fixed_origin_native'];fake=output.bind(wrong,fake['reply']);reject('absent_forecast_no_static_safety_substitution',lambda:bridge.bind_input(wrong,fake))
   bad=copy.copy(prepared);bad.sources=dict(prepared.sources);bad.sources.pop(str(paths['original_setup'].relative_to(R)));reject('undeclared_original_source',lambda:saved.capture(prepared=bad,**paths))
   assert (R/'runs/v1382_weekend_campaign/LEDGER.json').read_bytes()==before_parent
   put(O/'FIXED_INPUTS.json',dict(input_sha256=current['input_sha256'],saved_input_file_sha256=sha(model/'CURRENT_INPUT.json'),setup_sha256=sha(model/'SETUP.json'),software_proposal_fixture_was_not_executed=True,source_rows_covered=current['fixed_origin_native'],independent_actual_Allocator_recomputation_unexecuted=True,provenance=current['saved_provenance'],models=0))
   prepared.verify_closure_sources();result.update(passed=True,completed=completed,negative_cases=negatives,source_rows_covered=current['fixed_origin_native'],source_unchanged=True,no_model_or_optimizer_rerun=True,complete_current_response_not_yet_qualified=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc(),completed=completed,negative_cases=negatives)
 finally:
  sys.setprofile(None);signal.alarm(0);result.update(closed=True,wall_s=time.monotonic()-start);put(O/'ENTRY_QUALIFICATION.json',result)
  if not sources:sources={str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()}
  put(O/'SOURCE_FREEZE.json',dict(files=sources,source_only_qualified=result['passed'],numerical_response_qualified=False,actual_capture_qualified=False,models=0))
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
