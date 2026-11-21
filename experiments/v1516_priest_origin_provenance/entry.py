"""Once origin-value/provenance diagnostic target; no model or optimizer work."""
import ast
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
s=importlib.util.spec_from_file_location('v1516_origin_entry_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)

def main():
 assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
 with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as file:json.dump(dict(started_unix=time.time(),models=0),file)
 class NoModels(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'jax','jaxlib','mujoco','torch','rclpy','vehicle','factory'}:raise AssertionError('ORIGIN_TARGET_NO_NUMERIC_IMPORT:'+name)
 finder=NoModels();sys.meta_path.insert(0,finder)
 def profile(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'prediction.py','coupled_model.py','coupled_control.py','vehicle_control.py','kernel.py'}:raise AssertionError('ORIGIN_TARGET_NO_MODEL_OR_ALLOCATOR_CALL')
 sys.setprofile(profile);c.guard();result=dict(passed=False,closed=False,models=0,response_model_native=0,physical_native=0,Allocator_recomputations=0,replay_native=0,optimizer_calls=0)
 try:
  with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
   old=c.R/'experiments/v1513_priest_binding_token_repair';prior=c.R/'runs/v1513_priest_binding_token_repair';assert c.read(prior/'ENTRY_QUALIFICATION.json')['passed']and c.read(prior/'COMPLETION.json')['closed']and not c.read(prior/'COMPLETION.json')['passed'];assert c.read(prior/'actual_runtime_delivery/FULL_REMOTE_VERIFIED.json')['passed']
   for name in ['common.py','contract.py','owner.py','LIMITS.json']:assert(C/name).read_bytes()==(old/name).read_bytes()
   original=c.R/'experiments/v1497_priest_complete_response';expected=(original/'generator.py').read_text().replace('authority,lock,save_branch):','authority,lock,save_branch,save_origin):')
   needle="  for key in ['body','body_lateral','steering','controller_memory','coupled_episode','parked_target','steering_motion_active']:assert measured[key]==origin[key],'PRIEST_RESPONSE_CURRENT_ORIGIN_CHANGED'"
   assert expected.count(needle)==1;expected=expected.replace(needle,"  bridge.validate_origin(measured,current,p.state,save_origin=save_origin)");assert ast.dump(ast.parse(expected))==ast.dump(ast.parse((C/'generator.py').read_text()))
   expected=(original/'audit.py').read_text().replace('read_branch,authority,lock):','read_branch,authority,lock,save_origin):');needle="  for key in ['body','body_lateral','steering','controller_memory','coupled_episode','parked_target','steering_motion_active']:assert first[key]==origin[key]"
   assert expected.count(needle)==1;expected=expected.replace(needle,"  bridge.validate_origin(first,current,p.state,save_origin=save_origin)");assert ast.dump(ast.parse(expected))==ast.dump(ast.parse((C/'audit.py').read_text()))
   tree=ast.parse((C/'model_bridge.py').read_text());tree.body=[v for v in tree.body if not isinstance(v,ast.FunctionDef)or v.name not in {'origin_comparison','validate_origin'}];assert ast.dump(tree)==ast.dump(ast.parse((original/'model_bridge.py').read_text()))
   expected=(old/'driver.py').read_text().replace("c.R/'experiments/v1497_priest_complete_response/generator.py'","C/'generator.py'").replace("c.R/'experiments/v1497_priest_complete_response/audit.py'","C/'audit.py'")
   expected=expected.replace('save_branch=store.save)',"save_branch=store.save,save_origin=lambda value:saved(task/'GENERATION_ORIGIN.json',value))").replace('read_branch=reader.read,authority=phase,lock=lock)',"read_branch=reader.read,authority=phase,lock=lock,save_origin=lambda value:saved(task/'AUDIT_ORIGIN.json',value))");assert ast.dump(ast.parse(expected))==ast.dump(ast.parse((C/'driver.py').read_text()))
   priorfixed=c.read(prior/'FIXED_INPUTS.json');c.put(c.O/'FIXED_INPUTS.json',priorfixed)
   files={str(p.relative_to(c.R)):c.sha(p)for p in C.iterdir()if p.is_file()}
   for path in [c.INPUT,c.PROPOSAL,c.SETUP,c.O/'FIXED_INPUTS.json',prior/'ENTRY_QUALIFICATION.json',prior/'BACKEND_BINDING_PROOF.json',c.R/'runs/v1509_priest_response_once/PARENT_RESERVATION_PROOF.json',c.R/'runs/v1507_priest_response_evidence/STORAGE_TARGET_PROOF.json']:files[str(path.relative_to(c.R))]=c.sha(path)
   c.put(c.O/'SOURCE_FREEZE.json',dict(files=files,base_manifest=str(c.BASE.relative_to(c.R)),base_manifest_sha256=c.sha(c.BASE),entry_passed=False))
   current,proposal,setup=c.inputs();bridge=c.load('v1516_new_exact_origin_seam',C/'model_bridge.py');bridge.bind_input(current,proposal)
   origin=current['origin'];projection={name:copy.deepcopy(origin[name])for name in ['body','body_lateral','controller_memory','coupled_episode','parked_target','steering_motion_active']};projection.update(native_tick=origin['native_tick'],sim_time=origin['sim_time'],steering={k:copy.deepcopy(origin['steering'][k])for k in ['position','velocity']})
   assert projection['steering']!=origin['steering']
   # Eight numbers are a storage/provenance fixture, never reconstructed model state.
   software_state=[*origin['body'][:4],origin['body_lateral'],origin['body'][4],0.,0.]
   boundary_module=c.load('v1516_original_bounded_io',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py');budgets=c.load('v1516_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');codec=c.load('v1516_qualified_origin_codec',c.R/'experiments/v1507_priest_response_evidence/branch_store.py');task=c.O/'origin_target';task.mkdir();writer=budgets.WriterBudget(task,role='PLANNER',maximum_bytes=1024**2,source_identity=c.digest(c.sources()));records=[]
   with boundary_module.OutputBoundary(task,writer.reserve):
    def run_case(label,packet,input_value,state,expected):
     path=task/(label+'.json');seen=[]
     def save(value):codec.write_atomic(path,codec.encoded(value),writer);seen.append(value)
     first=None
     try:answer=bridge.validate_origin(packet,input_value,state,save_origin=save)
     except AssertionError as error:first=repr(error);answer=seen[0]if seen else None
     assert len(seen)==1 and path.is_file()and c.read(path)==seen[0]and answer['passed']is expected
     assert (first is None)==expected;records.append(dict(name=label,passed=expected,first_error=first,file=str(path.relative_to(c.R)),sha256=c.sha(path),checks=answer['checks'],diagnostic_saved_before_refusal=True))
    run_case('positive_exact_numeric_original_provenance',copy.deepcopy(projection),copy.deepcopy(current),software_state,True)
    changed=copy.deepcopy(projection);changed['steering']['position'][0]+=1e-10;run_case('wrong_position_no_tolerance',changed,current,software_state,False)
    changed=copy.deepcopy(projection);changed['controller_memory']['integral']+=1e-10;run_case('wrong_memory_no_reset',changed,current,software_state,False)
    changed=copy.deepcopy(current);changed['origin']['steering']['native_tick']+=1;run_case('wrong_source_native',projection,changed,software_state,False)
    changed=copy.deepcopy(current);changed['origin']['steering']['measured_at']+=.001;run_case('wrong_measurement_source',projection,changed,software_state,False)
    changed=copy.deepcopy(current);del changed['origin']['steering']['measured_at'];run_case('missing_provenance_schema',projection,changed,software_state,False)
    changed=copy.deepcopy(projection);changed['steering']['measured_at']=origin['steering']['measured_at'];run_case('fabricated_model_sensor_timestamp',changed,current,software_state,False)
    changed=copy.deepcopy(projection);changed['sim_time']+=.01;run_case('changed_fixed_clock',changed,current,software_state,False)
    run_case('nonfinite_initial_state',projection,current,[float('nan'),*software_state[1:]],False)
   changed=copy.deepcopy(current);changed['origin']['steering']['native_tick']+=1
   try:bridge.bind_input(changed,proposal)
   except AssertionError:identity_refused=True
   else:raise AssertionError('CURRENT_INPUT_SHA_MUTATION_ACCEPTED')
   c.put(c.O/'ORIGIN_INTERFACE_QUALIFICATION.json',dict(passed=True,scope='EXACT_SAVED_ENVELOPE_NUMERIC_PROJECTION_SOFTWARE_ONLY',cases=records,changed_whole_current_identity_rejected=identity_refused,software_initial8state_not_modelmeasurement=True,source_packet_and_proposal_files_unchanged=c.sha(c.INPUT)==priorfixed['input_file_sha256']and c.sha(c.PROPOSAL)==priorfixed['proposal_file_sha256'],all_original_numerical_bodies_AST_equal_except_origin_interface=True,real_original_boundary_writer_counter=writer._read(),models=0,physical_native=0,optimizer_calls=0))
  driver=c.load('v1516_exact_unadmitted_driver',C/'driver.py');value=driver.execute();assert not value['passed']and value['closed']and 'PRIEST_RESPONSE_ONLY_NOT_ADMITTED'in value['first_error']and not value['generation_executed']and value['generation_analytical_native']==value['audit_analytical_native']==0 and not value['secondary_errors'];(c.O/'RESULT.json').replace(c.O/'ENTRY_REFUSAL_RESULT.json')
  result.update(passed=True,source_frozen=True,exact_origin_positive=True,new_negative_cases=9,malformed_provenance_and_numeric_diagnostics_saved_before_refusal=True,unadmitted_driver_closed_before_model=True,original_science_tolerances_unchanged=True,old_bootstrap_byte_partialproof_reused_not_reexecuted=True,scope='NEW_ORIGIN_INTERFACE_SOURCE_ONLY')
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  result['closed']=True;c.put(c.O/'ENTRY_QUALIFICATION.json',result);sys.setprofile(None);sys.meta_path.remove(finder)
 if result['passed']:
  freeze=c.read(c.O/'SOURCE_FREEZE.json');freeze['entry_passed']=True
  for path in [c.O/'ENTRY_QUALIFICATION.json',c.O/'ORIGIN_INTERFACE_QUALIFICATION.json']:freeze['files'][str(path.relative_to(c.R))]=c.sha(path)
  c.put(c.O/'SOURCE_FREEZE.json',freeze)
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
