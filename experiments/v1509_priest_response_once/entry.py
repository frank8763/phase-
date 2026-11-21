"""New owner/CLI/source/clock/audit dependency target, no model construction."""
import copy
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
s=importlib.util.spec_from_file_location('v1509_entry_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def main():
 assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
 with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as file:json.dump(dict(started_unix=time.time(),models=0),file)
 class NoModels(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'jax','jaxlib','mujoco','torch','rclpy','vehicle','factory'}:raise AssertionError('RESPONSE_OWNER_ENTRY_NO_MODEL:'+name)
 finder=NoModels();sys.meta_path.insert(0,finder)
 def profile(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','coupled_control.py','vehicle_control.py','kernel.py'}:raise AssertionError('RESPONSE_OWNER_ENTRY_NO_MODEL_CALL')
 sys.setprofile(profile);c.guard();result=dict(passed=False,closed=False,models=0,optimizer_calls=0,physical_native=0,response_model_native=0,Allocator_recomputations=0,replay_native=0)
 try:
  with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
   source_pass=c.read(c.R/'runs/v1507_priest_response_evidence/ENTRY_QUALIFICATION.json');assert source_pass['passed'];base=c.read(c.BASE);assert all(c.sha(c.R/n)==h for n,h in base['files'].items())
   old=c.R/'runs/v1504_priest_namespace_worker';assert c.read(old/'COMPLETION.json')['passed']and c.read(old/'actual_runtime_delivery/FULL_REMOTE_VERIFIED.json')['passed'];index=c.read(old/'actual_runtime_delivery/ARCHIVE_INDEX.json');members={v['path']:v for v in index['files']}
   for path in [c.INPUT,c.PROPOSAL]:assert c.sha(path)==members[str(path.relative_to(c.R))]['sha256']
   current=c.read(c.INPUT);proposal=c.read(c.PROPOSAL)['candidate'];assert current['input_role']=='SAVED_ACTUAL_INPUT_MODEL_ONLY'and current['saved_actual_input_not_fresh_wire']and not current['physical_admission']and proposal['input_sha256']==current['input_sha256']
   fixed=dict(input_file_sha256=c.sha(c.INPUT),proposal_file_sha256=c.sha(c.PROPOSAL),setup_file_sha256=c.sha(c.SETUP),input_sha256=current['input_sha256'],proposal_sha256=proposal['proposal_sha256'],input_immutable_identity_not_rebound=True);c.put(c.O/'FIXED_INPUTS.json',fixed)
   files={str(p.relative_to(c.R)):c.sha(p)for p in C.iterdir()if p.is_file()}
   for path in [c.INPUT,c.PROPOSAL,c.SETUP,c.O/'FIXED_INPUTS.json',c.R/'runs/v1507_priest_response_evidence/ENTRY_QUALIFICATION.json',c.R/'runs/v1507_priest_response_evidence/STORAGE_TARGET_PROOF.json']:files[str(path.relative_to(c.R))]=c.sha(path)
   freeze=dict(files=files,base_manifest=str(c.BASE.relative_to(c.R)),base_manifest_sha256=c.sha(c.BASE),entry_passed=False);c.put(c.O/'SOURCE_FREEZE.json',freeze)
   contract=c.load('v1509_actual_contract_target',C/'contract.py');driver=c.load('v1509_actual_driver_target',C/'driver.py');source=c.sources();identity=c.digest(source);limits=c.limits();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();now=time.time();mono=time.monotonic()
   owner=c.load('v1509_real_once_parent_source',C/'owner.py');budgets=c.load('v1509_original_parent_budget',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');target=c.O/'parent_reservation_target';target.mkdir();budget=budgets.WriterBudget(target,role='SUPERVISOR_LOG',maximum_bytes=limits['parent_writer_bytes'],source_identity=identity);prepaid=owner.reserve_parent_budget(budget,(c.R/'runs/v1417_complete_timed_witness/REVIEW_PENDING.before').read_bytes(),limits);assert budget._read()['charged_bytes']<=limits['parent_writer_bytes']and prepaid['COMPLETION.json']==32768
   c.put(c.O/'PARENT_RESERVATION_PROOF.json',dict(passed=True,actual_counter=budget._read(),real_parent_paths_reserved_only_not_written=True,all_close_capacity_prepaid_before_child=True,models=0))
   authority=dict(scope=limits['scope'],round_id=C.name,models_authorized=True,physical_authorized=False,optimizer_authorized=False,boot_id=boot,source_manifest_sha256=identity,current_input_sha256=current['input_sha256'],proposal_sha256=proposal['proposal_sha256'],absolute_deadline_unix=now+60,hard_stop_monotonic=mono+60)
   for key in ['maximum_nominal_native','generation_native','success_only_audit_native','model_writer_bytes','parent_writer_bytes']:authority[key]=limits[key]
   software_parent=dict(active_round=C.name,models_now_authorized=True,active_math_round=None,hard_stop_monotonic=mono+100)
   def validate(value,p=software_parent):return contract.validate(value,parent=p,limits=limits,boot=boot,now_unix=now,now_mono=mono,source_identity=identity,input_sha=current['input_sha256'],proposal_sha=proposal['proposal_sha256'])
   assert validate(authority);negative=[]
   for name,key,value in [('PHYSICAL_PERMISSION','physical_authorized',True),('OPTIMIZER_PERMISSION','optimizer_authorized',True),('FOREIGN_BOOT','boot_id','foreign'),('CHANGED_INPUT','current_input_sha256','0'*64),('EXPIRED_WALL','absolute_deadline_unix',now-1),('EXPIRED_MONOTONIC','hard_stop_monotonic',mono-1),('CHANGED_NATIVE_CAP','generation_native',limits['generation_native']+1)]:
    changed=dict(authority);changed[key]=value
    try:validate(changed)
    except AssertionError:negative.append(name)
    else:raise AssertionError('OWNER_NEGATIVE_ACCEPTED:'+name)
   generation=dict(passed=True,closed=True,analytical_inflight_unknown=False,nominal_native=200,complete_stop_branches=200,analytical_native=40200);assert contract.audit_allowed(generation,saved=True,branch_count=200)
   for key,value in [('passed',False),('closed',False),('analytical_inflight_unknown',True),('nominal_native',199),('complete_stop_branches',199),('analytical_native',40199)]:assert not contract.audit_allowed(dict(generation,**{key:value}),saved=True,branch_count=200)
   assert not contract.audit_allowed(generation,saved=False,branch_count=200)
  # Actual production execute must refuse before loading generator/model bindings.
  value=driver.execute();assert not value['passed']and value['closed']and 'PRIEST_RESPONSE_ONLY_NOT_ADMITTED'in value['first_error']and value['generation_executed']is False and value['independent_audit_executed']is False and value['generation_analytical_native']==value['audit_analytical_native']==0 and value['source_unchanged']is True and not value['secondary_errors']
  (c.O/'RESULT.json').replace(c.O/'ENTRY_REFUSAL_RESULT.json');assert 'v1509_frozen_PRIEST_generator'not in sys.modules
  result.update(passed=True,source_frozen=True,source_only=True,production_CLI_unadmitted_before_binding=True,source_clock_budget_negative_cases=negative,audit_dependency_negative_cases=7,real_partial_storage_proof_reused_not_reexecuted=True,partial_storage_proof_sha256=c.sha(c.R/'runs/v1507_priest_response_evidence/STORAGE_TARGET_PROOF.json'),old_optimizer_not_reexecuted=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  result['closed']=True;c.put(c.O/'ENTRY_QUALIFICATION.json',result);sys.setprofile(None);sys.meta_path.remove(finder)
 if result['passed']:
  freeze=c.read(c.O/'SOURCE_FREEZE.json');freeze['entry_passed']=True;freeze['files'][str((c.O/'ENTRY_QUALIFICATION.json').relative_to(c.R))]=c.sha(c.O/'ENTRY_QUALIFICATION.json');c.put(c.O/'SOURCE_FREEZE.json',freeze)
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
