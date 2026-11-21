"""Premodel qualification and a separately admitted one-shot numerical entry."""
import argparse
import ast
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def guard(output):
 source=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(source.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=output);exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),scope);sys.addaudithook(scope['write_guard'])

class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*_):
  if name.split('.')[0]in {'mujoco','vehicle','factory','rclpy'}:raise AssertionError('ZERO200_ENTRY_NO_MODELS:'+name)

def qualify():
 assert not(O/'ENTRY_ONCE_CLAIM.json').exists();(O/'ENTRY_ONCE_CLAIM.json').write_text(json.dumps(dict(unix=time.time(),models=0))+'\n')
 guard(O);finder=NoModel();sys.meta_path.insert(0,finder);previous=sys.getprofile()
 def no_models(frame,event,arg):
  if event=='call'and frame.f_code.co_filename.startswith(str(R)+'/'):
   leaf=frame.f_code.co_filename.rsplit('/',1)[-1];name=frame.f_code.co_name
   if(name in {'__init__','step'}and leaf in {'coupled_model.py','vehicle.py','prediction.py'})or(name=='compute'and leaf in {'coupled_control.py','vehicle_control.py'}):raise AssertionError('V1454_ENTRY_MODEL_OR_COMPUTE_FORBIDDEN')
 sys.setprofile(no_models);result=dict(passed=False,models=0,physical_native=0,allocator_recomputations=0,actual_replay_native=0,software_only=True);first=None
 contract=exact('v1454_current_contract',C/'contract.py');io=exact('v1454_original_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
 try:
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   import gzip
   boundary=exact('v1454_frozen_boundary',R/'experiments/v1439_actual_ros_startup_close/bounded_io.py');capture=exact('v1454_exact_new_capture',C/'capture_budget.py')
   folder=O/'software_io';folder.mkdir();charges=[];negative=[]
   def charge(path,n):
    assert Path(path).is_relative_to(folder)and type(n)is int and n>=0
    charges.append(dict(path=str(Path(path).relative_to(folder)),bytes=n))
   with boundary.OutputBoundary(folder,charge):
    try:
     with gzip.open(folder/'ORIGINAL_RED.json.gz','xt')as stream:json.dump(dict(software_only=True),stream)
    except OSError as exc:assert 'WRITABLE_RAW_DESCRIPTOR'in str(exc);negative.append('original_TextIOWrapper_descriptor_refused')
    else:raise AssertionError('ORIGINAL_GZIP_REFUSAL_NOT_REPRODUCED')
    values={'CONTACTS.json.gz':[[[1,2,'software_only',0.0]],[]],'SENSORS.json.gz':[dict(software_only=True,text='中文',native=0)]}
    with capture.original_finish_compressed_paths(folder)as opened:
     for name,value in values.items():
      with gzip.open(folder/name,'xt')as stream:
       json.dump(value,stream,ensure_ascii=False)
       try:stream.fileno()
       except OSError:negative.append('raw_descriptor_'+name)
       else:raise AssertionError('COMPRESSED_RAW_FD_ACCEPTED')
     for name,mode in [('OTHER.json.gz','xt'),('CONTACTS.json.gz','xt'),('SENSORS.json.gz','wt')]:
      try:
       with gzip.open(folder/name,mode):pass
      except AssertionError:negative.append('compressed_target_or_mode_'+name+mode)
      else:raise AssertionError('WRONG_COMPRESSED_PATH_OR_MODE_ACCEPTED')
    assert opened=={folder/'CONTACTS.json.gz',folder/'SENSORS.json.gz'}
   for name,value in values.items():
    with gzip.open(folder/name,'rt')as stream:assert json.load(stream)==value
    emitted=sum(row['bytes']for row in charges if row['path']==name);assert emitted==8192+(folder/name).stat().st_size
   # Only the new capture adapter and save ordering changed. Exact normalized
   # previous production files/gates are reused; no old entry is rerun.
   old=R/'experiments/v1451_native_closure_qualification'
   reused=[]
   for name in ['native_budget.py','quota.py','closure_owner.py','contract.py','owner.py']:
    actual=(C/name).read_text().replace('v1454_bounded_gzip_closure','v1451_native_closure_qualification').replace('v1454','v1451');assert ast.dump(ast.parse(actual))==ast.dump(ast.parse((old/name).read_text())),'V1454_UNDECLARED_CHANGE:'+name;reused.append(name)
   driver=(C/'driver.py').read_text().replace('v1454','v1451')
   driver=driver.replace("C/'capture_budget.py'","R/'experiments/v1439_actual_ros_startup_close/capture_budget.py'")
   driver=driver.replace("journal.close();journal=None","journal.close();journal=None;result['physical']=capture.finish(v)")
   driver=driver.replace("result.update(complete200_applied_zero_tail=True,full_Nplus1_roundtrip=True)\n     result['physical']=capture.finish(v)","result.update(complete200_applied_zero_tail=True,full_Nplus1_roundtrip=True)")
   driver=driver.replace("capture is not None and not capture.finish_attempted and 'physical'not in result","capture is not None and 'physical'not in result")
   assert ast.dump(ast.parse(driver))==ast.dump(ast.parse((old/'driver.py').read_text())),'V1454_DRIVER_UNDECLARED_CHANGE'
   previous_q=contract.read(R/'runs/v1451_native_closure_qualification/ENTRY_QUALIFICATION.json');assert previous_q['passed']and previous_q['models']==previous_q['physical_native']==0
   source=dict(previous_q['source_hashes']);source.update({str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()})
   assert all(contract.sha(R/p)==h for p,h in source.items())
   storage=contract.storage_preflight();result.update(passed=True,entry_gates=previous_q['entry_gates'],negatives_rejected=negative,compressed_bytes_charged_exact=True,lossless_unicode_and_contact_shape_roundtrip=True,original_red_reproduced=True,source_hashes=source,reused_zero200_entry_SHA=contract.sha(R/'runs/v1451_native_closure_qualification/ENTRY_QUALIFICATION.json'),unchanged_AST_files=reused,driver_only_capture_and_save_order_changes=True,storage=storage,actual_cpu=sorted(os.sched_getaffinity(0)),original_writeguard=True,physical_route_admission=False,actual_zero_tail_allocator_replay_not_executed=True)
 except BaseException as exc:
  import traceback
  first=dict(error=repr(exc),traceback=traceback.format_exc());result['first_error']=first
 finally:
  sys.setprofile(previous);sys.meta_path.remove(finder);io.atomic(O/'ENTRY_QUALIFICATION.json',result);io.atomic(O/'ENTRY_CLOSED.json',dict(closed=True,passed=result['passed'],first_error=first,models=0))
  if result['passed']:io.atomic(O/'SOURCE_FREEZE.json',dict(files=result['source_hashes'],models=0,physical_route_admission=False))
 return 0 if result['passed']else 1

def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--qualify-entry',action='store_true');g.add_argument('--run',action='store_true');g.add_argument('--prepare-admission',action='store_true');g.add_argument('--launch',action='store_true');a=p.parse_args()
 if a.prepare_admission or a.launch:
  os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));owner=exact('v1454_once_owner',C/'owner.py')
  if a.prepare_admission:owner.prepare_admission();return 0
  value=owner.launch();return 0 if value['passed']else 1
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 os.chdir(R);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply()
 if a.qualify_entry:return qualify()
 guard(O/'zero200');driver=exact('v1454_once_actual_driver',C/'driver.py');v=driver.run(driver.contract.read(O/'TASK.json'),driver.contract.read(O/'APPROVAL.json'),driver.contract.read(O/'ROUND_WINDOW.json'));return 0 if v['passed']else 1
if __name__=='__main__':raise SystemExit(main())
