"""Cold operational bootstrap then real pure backend bindings, no construction."""
import ast
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1511_new_entry_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def main():
 assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
 with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as file:json.dump(dict(started_unix=time.time(),models=0),file)
 class NoModels(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'jax','jaxlib','mujoco','torch','rclpy','vehicle','factory'}:raise AssertionError('BACKEND_SOURCE_TARGET_NO_MODEL_IMPORT:'+name)
 finder=NoModels();sys.meta_path.insert(0,finder)
 def profile(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','coupled_control.py','vehicle_control.py','kernel.py'}:raise AssertionError('BACKEND_SOURCE_TARGET_NO_CONSTRUCT_STEP_OR_COMPUTE')
 sys.setprofile(profile);result=dict(passed=False,closed=False,models=0,response_model_native=0,physical_native=0,Allocator_recomputations=0,replay_native=0,optimizer_calls=0)
 try:
  parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
  with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);bootstrap=c.bootstrap();c.guard()
   previous=c.R/'runs/v1509_priest_response_once';qualified=c.read(previous/'ENTRY_QUALIFICATION.json');assert qualified['passed']and qualified['closed']
   old=c.R/'experiments/v1509_priest_response_once'
   for name in ['contract.py','owner.py','LIMITS.json']:assert(C/name).read_bytes()==(old/name).read_bytes()
   expected=(old/'driver.py').read_text().replace(" c.guard();signal.signal(signal.SIGALRM"," c.bootstrap();c.guard();signal.signal(signal.SIGALRM")
   assert ast.dump(ast.parse(expected))==ast.dump(ast.parse((C/'driver.py').read_text()))
   before=ast.parse((old/'common.py').read_text());after=ast.parse((C/'common.py').read_text());assert ast.dump(before)==ast.dump(ast.Module(body=[v for v in after.body if not isinstance(v,ast.FunctionDef)or v.name!='bootstrap'],type_ignores=after.type_ignores))
   fixed=c.read(previous/'FIXED_INPUTS.json');c.put(c.O/'FIXED_INPUTS.json',fixed)
   files={str(p.relative_to(c.R)):c.sha(p)for p in C.iterdir()if p.is_file()}
   for path in [c.INPUT,c.PROPOSAL,c.SETUP,c.O/'FIXED_INPUTS.json',previous/'ENTRY_QUALIFICATION.json',previous/'PARENT_RESERVATION_PROOF.json',c.R/'runs/v1507_priest_response_evidence/ENTRY_QUALIFICATION.json',c.R/'runs/v1507_priest_response_evidence/STORAGE_TARGET_PROOF.json']:files[str(path.relative_to(c.R))]=c.sha(path)
   c.put(c.O/'SOURCE_FREEZE.json',dict(files=files,base_manifest=str(c.BASE.relative_to(c.R)),base_manifest_sha256=c.sha(c.BASE),entry_passed=False))
   generation=c.load('v1511_exact_generation_binding',c.R/'experiments/v1497_priest_complete_response/generator.py');audit=c.load('v1511_exact_audit_binding',c.R/'experiments/v1497_priest_complete_response/audit.py')
   first=generation.bridge.binding();second=audit.bridge.binding();assert first[:4]==second[:4]
   for left,right,names in [(first[4],second[4],['select']),(first[5],second[5],['select','observe_applied'])]:
    for name in names:
     a=getattr(left,name);b=getattr(right,name);assert Path(a.__code__.co_filename).resolve()==Path(b.__code__.co_filename).resolve()and a.__qualname__==b.__qualname__ and a.__code__.co_code==b.__code__.co_code and a.__code__.co_consts==b.__code__.co_consts
   Predictor,initial,kernel,Adapter=first[:4]
   for fn,name in [(Predictor.step,'coupled_model.py'),(initial,'coupled_model.py'),(Adapter.compute,'coupled_control.py')]:assert Path(fn.__code__.co_filename).resolve()==c.R/'experiments/v1114_coupled_steering_mode'/name
   c.put(c.O/'BACKEND_BINDING_PROOF.json',dict(passed=True,bootstrap=bootstrap,real_numerical_binding_objects_equal=True,fresh_Gear_Policy_source_code_identity_equal=True,original_Predictor_step=str(Path(Predictor.step.__code__.co_filename).relative_to(c.R)),original_Adapter_compute=str(Path(Adapter.compute.__code__.co_filename).relative_to(c.R)),class_definitions_only=True,profile_forbade_all_constructor_step_compute=True,old_context_audit_parent_reservation_proof_sha256=c.sha(previous/'ENTRY_QUALIFICATION.json'),models=0))
  driver=c.load('v1511_real_driver_unadmitted',C/'driver.py');value=driver.execute();assert not value['passed']and value['closed']and 'PRIEST_RESPONSE_ONLY_NOT_ADMITTED'in value['first_error']and not value['generation_executed']and value['generation_analytical_native']==value['audit_analytical_native']==0 and not value['secondary_errors']
  (c.O/'RESULT.json').replace(c.O/'ENTRY_REFUSAL_RESULT.json');result.update(passed=True,source_frozen=True,actual_cold_bootstrap_before_guard=True,actual_generator_and_audit_binding_positive=True,unadmitted_driver_closed=True,old_targets_reused_by_AST_SHA_not_rerun=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  result['closed']=True;c.put(c.O/'ENTRY_QUALIFICATION.json',result);sys.setprofile(None);sys.meta_path.remove(finder)
 if result['passed']:
  freeze=c.read(c.O/'SOURCE_FREEZE.json');freeze['entry_passed']=True;freeze['files'][str((c.O/'ENTRY_QUALIFICATION.json').relative_to(c.R))]=c.sha(c.O/'ENTRY_QUALIFICATION.json');freeze['files'][str((c.O/'BACKEND_BINDING_PROOF.json').relative_to(c.R))]=c.sha(c.O/'BACKEND_BINDING_PROOF.json');c.put(c.O/'SOURCE_FREEZE.json',freeze)
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
