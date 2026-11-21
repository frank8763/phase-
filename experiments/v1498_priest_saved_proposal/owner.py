"""Prepare software input once, then a separately admitted exact numeric owner."""
import argparse
import copy
import fcntl
import hashlib
import importlib.util
import importlib.abc
import ast
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
common=exact('v1493_frozen_worker_common',C/'common.py')
put=common.put;read=common.read;sha=common.sha;digest=common.digest

def prepare():
 with(O/'PREPARE_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0),f)
 assert sorted(os.sched_getaffinity(0))==[4]and os.environ.get('PHASE_REPO')==str(R)
 parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and not parent['models_now_authorized']
 class NoModels(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'jax','jaxlib','torch','mujoco','rclpy','vehicle','factory'}:raise AssertionError('PREPARE_NO_NUMERIC_OR_MODEL_IMPORT:'+name)
 finder=NoModels();sys.meta_path.insert(0,finder)
 def profile(frame,event,arg):
  if event=='call'and frame.f_code.co_filename.startswith(str(R)+'/')and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','coupled_control.py','vehicle_control.py','kernel.py'}:raise AssertionError('PREPARE_NO_MODEL_OR_ALLOCATOR_CALL')
 sys.setprofile(profile);common.guard(O)
 try:
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   qualified=R/'runs/v1497_priest_complete_response'
   freeze=read(qualified/'SOURCE_FREEZE.json');assert freeze['source_only_qualified']and read(qualified/'ENTRY_QUALIFICATION.json')['passed']
   sources=freeze['files'].copy();assert all(sha(R/n)==h for n,h in sources.items())
   reused={}
   for name in ['common.py','sandbox.py']:
    original=R/'experiments/v1492_priest_optimizer_worker'/name
    assert (C/name).read_bytes()==original.read_bytes();reused[name]=sha(original)
   def io_body(path):
    tree=ast.parse(path.read_text());node=next(n for n in ast.walk(tree)if isinstance(n,ast.If)and ast.unparse(n.test)=="mode == 'IO_TARGET'")
    return ast.dump(ast.Module(body=node.body,type_ignores=[]))
   assert io_body(C/'inner.py')==io_body(R/'experiments/v1492_priest_optimizer_worker/inner.py')
   put(O/'OS_QUALIFICATION_REUSE.json',dict(passed=True,unchanged_byte_sources=reused,IO_TARGET_branch_AST_exact=True,original_pass_proof_sha256=sha(R/'runs/v1492_priest_optimizer_worker/ENTRY_QUALIFICATION.json'),old_OS_target_reexecuted=False,models=0))
   fixed=read(qualified/'FIXED_INPUTS.json');saved_file=qualified/'saved_input/CURRENT_INPUT.json';setup_file=qualified/'saved_input/SETUP.json'
   assert sha(saved_file)==fixed['saved_input_file_sha256']and sha(setup_file)==fixed['setup_sha256']
   sources[str(saved_file.relative_to(R))]=sha(saved_file);sources[str(setup_file.relative_to(R))]=sha(setup_file)
   for file in C.iterdir():
    if file.is_file():sources[str(file.relative_to(R))]=sha(file)
   old=R/'experiments/v1485_priest_current_polynomial_seam'
   prepared=exact('v1498_same_prepared_core',old/'core_identity.py').PreparedCore(source_manifest=sources)
   current=read(saved_file);original=copy.deepcopy(current);identity=current.pop('input_sha256');assert digest(current)==identity
   assert current['input_role']=='SAVED_ACTUAL_INPUT_MODEL_ONLY'and current['saved_actual_input_not_fresh_wire']and current['physical_admission']is False
   current['source_manifest_sha256']=prepared.source_manifest_sha256;current['core_identity_sha256']=prepared.hot_identity();current['core_identity']=copy.deepcopy(prepared.value)
   current['input_sha256']=digest(current)
   # Only prepared execution identity changes. Retain exact actual packet,
   # fullstate, causal prediction, segment, mode/gear and source provenance.
   for key in original:
    if key not in {'source_manifest_sha256','core_identity_sha256','core_identity','input_sha256'}:assert current[key]==original[key]
   boundary=exact('v1498_same_declared_boundary',old/'causal_boundary.py');initial=boundary.boundary_state(current)
   port=exact('v1493_frozen_port_source',R/'experiments/v1487_priest_optimizer_contract/cpu_source.py').prepare_cpu_source();port.pop('source')
   request=exact('v1493_actual_request_builder',R/'experiments/v1487_priest_optimizer_contract/optimizer_request.py').build(current,prepared=prepared,boundary_state=initial,port_identity=port)
   assert request['constructor_kwargs']['num_obs_2']==1 and request['initial_state']==initial['state']and request['input_sha256']==current['input_sha256']
   task=O/'numeric';task.mkdir();put(task/'CURRENT_INPUT.json',current);put(task/'OPTIMIZER_REQUEST.json',request);put(task/'SOURCE_MANIFEST.json',sources)
   numerical=sources.copy()
   for p in C.iterdir():
    if p.is_file():numerical[str(p.relative_to(R))]=sha(p)
   put(common.O/'SOURCE_FREEZE.json',dict(files=sources,entry_passed=True,scope='NEW_SAVED_INPUT_WORKER_SOURCE_PREPARATION_ONLY',inherited_OS_proof='runs/v1492_priest_optimizer_worker/ENTRY_QUALIFICATION.json',models=0))
   put(O/'NUMERIC_SOURCE_FREEZE.json',dict(files=numerical,worker_source_freeze_sha256=sha(common.O/'SOURCE_FREEZE.json'),worker_manifest_sha256=digest(sources),models=0,saved_actual_input_not_fresh_wire=True,optimizer_executed=False))
   put(O/'FIXED_INPUTS.json',dict(input_sha256=current['input_sha256'],request_sha256=request['request_sha256'],input_file_sha256=sha(task/'CURRENT_INPUT.json'),request_file_sha256=sha(task/'OPTIMIZER_REQUEST.json'),saved_actual_input_not_fresh_wire=True,models=0,optimizer_calls=0))
   put(O/'PREPARATION_COMPLETION.json',dict(passed=True,closed=True,models=0,optimizer_calls=0,JAX_author_imported=False,real_current_capture=False,source_frozen=True,input_role='SAVED_ACTUAL_INPUT_MODEL_ONLY',original_saved_input_sha256=identity))
 except BaseException as e:put(O/'PREPARATION_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),models=0));raise
 finally:sys.setprofile(None);sys.meta_path.remove(finder)

def usage():
 seen=set();total=0
 for root,dirs,files in os.walk(R/'runs',followlinks=False):
  for p in [Path(root)]+[Path(root)/n for n in files]:
   st=p.lstat();key=(st.st_dev,st.st_ino)
   if key not in seen:seen.add(key);total+=st.st_blocks*512
 return total

def launch():
 assert sorted(os.sched_getaffinity(0))==[4]and os.environ.get('PHASE_REPO')==str(R)
 assert not(O/'NUMERIC_ONCE_CLAIM.json').exists()and read(O/'PREPARATION_COMPLETION.json')['passed']
 source=read(O/'NUMERIC_SOURCE_FREEZE.json');assert all(sha(R/n)==h for n,h in source['files'].items())
 recovery=read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['numeric_source_freeze_sha256']==sha(O/'NUMERIC_SOURCE_FREEZE.json')
 assert read(R/'runs/v1382_weekend_campaign/LEDGER.json')['active_round']is None
 before=usage();peak=before+560*1024**2;assert peak<10*1024**3,'NUMERIC_FULL_EVIDENCE_ARCHIVE_ROOT_PEAK_REFUSED'
 task=O/'numeric';current=read(task/'CURRENT_INPUT.json');request=read(task/'OPTIMIZER_REQUEST.json');start=time.monotonic();end=min(start+600,start+1795395600-time.time())
 authority=dict(scope='PRIEST_OPTIMIZER_ONLY',mode='OPTIMIZER',models_authorized=False,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),source_manifest_sha256=source['worker_manifest_sha256'],input_sha256=current['input_sha256'],request_sha256=request['request_sha256'],kernel_source_sha256=request['port_identity']['ported_sha256'],dependency_index_sha256=sha(R/'runs/v1491_priest_dependency_target/EXTRACTED_INDEX.json'),dependency_remote_proof_sha256=sha(R/'runs/v1490_priest_dependency_recovery/FULL_REMOTE_VERIFIED.json'),qualified_distribution_versions={'jax':'0.4.30','jaxlib':'0.4.30','numpy':'2.2.6','scipy':'1.14.1','matplotlib':'3.10.9'},optimizer_writer_maximum_bytes=2*1024**2,absolute_deadline_unix=min(time.time()+600,1795395600),hard_stop_monotonic=end,saved_actual_input_not_fresh_wire=True,software_current_input_only=False)
 claim=dict(started_unix=time.time(),authority=authority,full_reserved_peak_bytes=peak,models=0)
 with(O/'NUMERIC_ONCE_CLAIM.json').open('x')as f:json.dump(claim,f)
 put(task/'APPROVAL.json',authority);put(O/'OPTIMIZER_ONLY_ADMISSION.json',authority)
 put(task/'CURRENT_SOURCE_REMOTE_RECOVERY.json',dict(passed=True,source_freeze_sha256=source['worker_source_freeze_sha256'],actual_delta_proof=recovery))
 result=dict(passed=False,closed=False,scope='ONCE_SAVED_ACTUAL_INPUT_REAL_CPU_PRIEST_PROPOSAL',models=0,physical_native=0,optimizer_calls=None,optimizer_work_unknown=True)
 try:
  sandbox=exact('v1493_frozen_bounded_sandbox',C/'sandbox.py')
  writer=exact('v1493_exact_parent_budget',R/'experiments/v1436_pathlib_control_rename/writer_budget.py').WriterBudget(task,role='SUPERVISOR_LOG',maximum_bytes=8*1024**2,source_identity=source['worker_manifest_sha256'])
  proof=sandbox.run(task,mode='OPTIMIZER',writer=writer,wall_s=max(1,end-time.monotonic()-2));put(O/'WORKER_RESULT.json',proof)
  terminal=proof['terminal']['result'];result.update(passed=proof['returncode']==0 and terminal['passed'],worker_returncode=proof['returncode'],inner_result=terminal,optimizer_calls=terminal.get('optimizer_calls'),optimizer_work_unknown=not terminal.get('passed',False),first_error=terminal.get('original_error'))
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  result.update(closed=True,wall_s=time.monotonic()-start,source_unchanged=all(sha(R/n)==h for n,h in source['files'].items()),saved_actual_input_not_fresh_wire=True,actual_current_capture=False,actual_control_domain_qualified=False,whole_route_passed=False)
  put(O/'COMPLETION.json',result)
 return 0 if result['passed']else 1

if __name__=='__main__':
 if '--prepare'in sys.argv:prepare()
 elif '--launch'in sys.argv:raise SystemExit(launch())
 else:raise RuntimeError('EXPLICIT_PREPARE_OR_ONCE_LAUNCH_SCOPE_REQUIRED')
