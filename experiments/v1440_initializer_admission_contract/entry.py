"""Initializer CLI: entry qualification has no models; numerical mode is scoped."""
import argparse
import ast
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import subprocess
import time
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy','coupled_model','prediction'}:raise AssertionError('INITIALIZER_ENTRY_NO_MODEL:'+name)

def install_guard(output):
 guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=output);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])

def qualify():
 assert not(O/'ENTRY_QUALIFICATION.json').exists();sys.meta_path.insert(0,NoModel())
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py'}:raise AssertionError('INITIALIZER_ENTRY_PROFILE_MODELS_FORBIDDEN')
 sys.setprofile(forbid);install_guard(O)
 init=exact('v1440_actual_initializer_under_entry_guard',C/'initializer.py');owner=exact('v1440_once_actual_owner_under_entry_guard',C/'owner.py');contract=init.contract
 parent_path=R/'runs/v1382_weekend_campaign/LEDGER.json';parent_before=parent_path.read_bytes();parent=json.loads(parent_before);assert parent['active_round']is None and not parent['models_now_authorized']
 scope=O/'entry';scope.mkdir();negatives=[]
 def reject(name,fn,expected=None):
  try:fn()
  except (AssertionError,RuntimeError,OSError)as exc:
   if expected is not None:assert expected in str(exc),(name,repr(exc))
   negatives.append(dict(case=name,error=repr(exc)));return
  raise AssertionError('INITIALIZER_ENTRY_NEGATIVE_ACCEPTED:'+name)
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  reject('real_initializer_refuses_before_physical_binding',lambda:init.run({}, {}, {}),'INITIALIZER_ENTRY_PREREQUISITES_MISSING_MODELS_FORBIDDEN')
  life=exact('v1440_exact_existing_physical_binding',R/'experiments/v1439_actual_ros_startup_close/lifecycle.py');old,Adapter,factory,replay=life.physical_binding(scope)
  assert Path(Adapter.compute.__code__.co_filename)==R/'experiments/v1114_coupled_steering_mode/coupled_control.py'
  assert Path(factory.create_vehicle.__code__.co_filename)==R/'experiments/v1067_causal_replan_brake_reserve/scene_binding.py'
  assert Path(replay.__code__.co_filename)==R/'experiments/v882_runtime_evidence_repair/physical.py'
  # Only call/save/error control is exercised; no software object substitutes
  # for a physical vehicle or produces a t0/fullstate certificate.
  result=dict(canonical_factory_call_attempts=0,canonical_vehicle_initializations=0,initializer_inflight_unknown=False,first_error=None,secondary_errors=[])
  def save(name,value):init.io.atomic(scope/name,dict(software_fault_only=True,value=value))
  def factory_failure():raise ValueError('SOFTWARE_PRIMARY_FACTORY_CALL_FAILURE')
  try:init.call_factory_once(factory_failure,save=save,result=result)
  except ValueError as exc:init.save_error(result,exc,save,stage='SOFTWARE_FACTORY_FAULT')
  assert result['canonical_factory_call_attempts']==1 and result['canonical_vehicle_initializations']is None and result['initializer_inflight_unknown']
  primary=result['first_error'].copy()
  def save_failure(*_):raise OSError('SOFTWARE_SECONDARY_SAVE_FAILURE')
  init.save_error(result,OSError('SOFTWARE_LATER_CLOSE'),save_failure,stage='SOFTWARE_LATER_CLOSE')
  assert result['first_error']==primary and len(result['secondary_errors'])==2
  reject('factory_cannot_retry',lambda:init.call_factory_once(factory_failure,save=save,result=result),'INITIALIZER_FACTORY_ALREADY_ATTEMPTED')
  untouched=dict(canonical_factory_call_attempts=0,canonical_vehicle_initializations=0,initializer_inflight_unknown=False)
  reject('failed_before_call_save_does_not_call_factory',lambda:init.call_factory_once(factory_failure,save=save_failure,result=untouched),'SOFTWARE_SECONDARY_SAVE_FAILURE')
  assert untouched['canonical_factory_call_attempts']==0 and untouched['canonical_vehicle_initializations']==0 and not untouched['initializer_inflight_unknown']
  init.io.atomic(scope/'SOFTWARE_ERROR_ACCOUNTING.json',dict(software_only=True,after_factory_exception=result,before_factory_save_exception=untouched,no_real_factory_called=True))
  zeros=exact('v1440_production_zero_step_guard',C/'zero_steps.py');calls=[]
  def original_step(*_):calls.append('UNEXPECTED')
  api=SimpleNamespace(mj_step=original_step,mj_step1=original_step,mj_step2=original_step)
  with zeros.forbid_steps(api)as attempted:
   sys.setprofile(None);assert getattr(sys.getprofile(),'_initializer_zero_step_guard',False)
   for name in ['mj_step','mj_step1','mj_step2']:reject('forbidden_'+name,lambda name=name:getattr(api,name)(None),'INITIALIZER_NATIVE_STEPS_FORBIDDEN')
  assert len(attempted)==3 and not calls and api.mj_step is original_step
  quota_module=exact('v1440_narrow32MiB_initializer_quota',C/'quota.py');limits=contract.read(C/'LIMITS.json');quota=quota_module.EvidenceQuota(scope,limits)
  reject('32MiB_cap_cannot_be_replaced_by224',lambda:quota_module.EvidenceQuota(scope,dict(limits,maximum_task_evidence_bytes=224*1024**2)))
  boundary=exact('v1440_qualified_native_C_save_boundary',R/'experiments/v1439_actual_ros_startup_close/bounded_io.py')
  # Explicit software save API verifies write ordering/size rejection only.
  # No MuJoCo module, native model or actual C save is called here.
  emissions=[]
  def fake_save(model,path,buffer=None):emissions.append(path);Path(path).write_bytes(b's'*37)
  fake=SimpleNamespace(mj_sizeModel=lambda _:37,mj_saveModel=fake_save)
  quota.bind_external_names([]);quota.write_enforcement_active=True
  try:
   with boundary.OutputBoundary(scope,quota.charge_write),boundary.native_model_saves(fake,quota.charge_write):fake.mj_saveModel(None,str(scope/'software_api.bin'))
   assert len(emissions)==1 and(scope/'software_api.bin').stat().st_size==37
   def prewrite_refusal(*_):raise RuntimeError('SOFTWARE_PREWRITE_REFUSAL')
   with boundary.native_model_saves(fake,prewrite_refusal):reject('native_save_rejected_before_software_API_call',lambda:fake.mj_saveModel(None,str(scope/'unwritten_api.bin')),'SOFTWARE_PREWRITE_REFUSAL')
   assert len(emissions)==1 and not(scope/'unwritten_api.bin').exists()
  finally:quota.write_enforcement_active=False
  with(scope/'software_console.bin').open('xb')as stream:
   console=owner.BoundedConsole(stream,7)
   child=subprocess.Popen(['taskset','-c','5',sys.executable,'-B','-c',"import sys;sys.stdout.buffer.write(b'first')"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   data,_=child.communicate(timeout=5);assert child.returncode==0 and data==b'first';console.feed(data)
   reject('console_rejects_before_byte_write',lambda:console.feed(b'next'),'INITIALIZER_CONSOLE_BYTE_CAP_EXHAUSTED')
   assert console.charged==5
  assert(scope/'software_console.bin').read_bytes()==b'first'
  owner.claim_once(scope/'software_once.json');reject('once_claim_rejects_second_attempt',lambda:owner.claim_once(scope/'software_once.json'))
  now=time.time();mono=time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+180,hard_stop_monotonic=mono+180,boot_id=parent['boot_id']);contract.check_window(window,parent)
  reject('wrong_boot',lambda:contract.check_window(dict(window,boot_id='wrong'),parent))
  reject('dual_clock_duration_changed',lambda:contract.check_window(dict(window,hard_stop_monotonic=mono+179),parent))
  reject('close_time_reserve_missing',lambda:contract.check_window(dict(window,absolute_deadline_unix=now+20,hard_stop_monotonic=mono+20),parent))
  prerequisites=contract.prerequisites();storage=contract.storage_preflight()
  assert parent_path.read_bytes()==parent_before and not(O/'INITIALIZER_ONLY_ADMISSION.json').exists()and not(O/'INITIALIZER_ONCE_CLAIM.json').exists()
  gates={name:True for name in ['actual_no_model_entry_refusal','exact_factory_and_adapter_binding','first_error_and_unknown_count_saves','forbidden_native_step_guard','native_save_size_source_and_byte_path','whole_storage_peak','bounded_dual_clock_and_once_owner','supervisor_console_bounded_pipe']}
  proof=dict(passed=True,models=0,physical_native=0,analytical_integrations=0,allocator_recomputations=0,actual_replay_native=0,actual_cpu=[2],original_writeguard=True,model_constructor_profile_guard=True,entry_gates=gates,negative_cases=negatives,software_faults_and_software_save_API_explicit=True,actual_native_C_save_executed=False,actual_canonical_initializer_called=False,initializer_runtime_qualified=False,physical_route_admission=False,prerequisite_qualification_SHA=prerequisites,all_runs_peak=storage,source_hashes={str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()})
  init.io.atomic(O/'ENTRY_QUALIFICATION.json',proof);print(json.dumps(proof))

def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--qualify-entry',action='store_true');g.add_argument('--prepare-admission',action='store_true');g.add_argument('--launch',action='store_true');g.add_argument('--run',action='store_true');a=p.parse_args()
 if a.prepare_admission or a.launch:
  os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));owner=exact('v1440_zero_model_schedule_owner',C/'owner.py')
  return owner.prepare_admission()if a.prepare_admission else owner.launch()
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 os.chdir(R);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply()
 if a.qualify_entry:return qualify()
 install_guard(O/'initializer_only');init=exact('v1440_numerical_initializer_runtime',C/'initializer.py');result=init.run(init.contract.read(O/'TASK.json'),init.contract.read(O/'APPROVAL.json'),init.contract.read(O/'INITIALIZER_WINDOW.json'));return 0 if result['passed']else 1

if __name__=='__main__':raise SystemExit(main())
