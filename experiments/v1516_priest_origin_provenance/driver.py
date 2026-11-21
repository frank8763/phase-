"""Real generation/store/read/fresh-audit path, after a separate narrow admission."""
import fcntl
import importlib.util
import os
from pathlib import Path
import signal
import time
import traceback
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1509_driver_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
contract=c.load('v1509_exact_response_contract',C/'contract.py')

def execute():
 result=dict(passed=False,closed=False,scope=c.limits()['scope'],models_physical=0,physical_native=0,optimizer_calls=0,independent_Allocator_recomputation=0,ownreplay_native=0,generation_analytical_native=0,generation_inflight_unknown=False,audit_analytical_native=0,audit_inflight_unknown=False,first_error=None,secondary_errors=[],generation_executed=False,independent_audit_executed=False,actual_control_admitted=False,whole_route_passed=False)
 store=None;writer=None;arrays=None;generation=None;audit=None;returned_save_attempted=False;task=c.O/'model';started=time.monotonic()
 try:
  with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);authority,source,current,proposal,setup=contract.admit(lock)
   assert task.is_dir()
   budget=c.load('v1509_original_byte_budget',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');boundary_module=c.load('v1509_original_output_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py');codec=c.load('v1509_frozen_branch_stream',c.R/'experiments/v1507_priest_response_evidence/branch_store.py');returned=c.load('v1509_frozen_returned_evidence',c.R/'experiments/v1507_priest_response_evidence/returned_evidence.py')
   writer=budget.WriterBudget(task,role='PLANNER',maximum_bytes=authority['model_writer_bytes'],source_identity=authority['source_manifest_sha256'])
   with boundary_module.OutputBoundary(task,writer.reserve)as boundary:
    try:
     def saved(path,value):codec.write_atomic(path,codec.encoded(value),writer)
     binding=dict(input_sha256=current['input_sha256'],proposal_sha256=proposal['proposal_sha256'],causal_snapshot_sha256=current['causal_snapshot_sha256'],tested_source_manifest_sha256=c.digest(source),geometry_kind='FULL_PERIOD_DISK',origin_native=current['fixed_origin_native'])
     store=codec.BranchStore(task,writer=writer,boundary=boundary,binding=binding)
     generator=c.load('v1509_frozen_PRIEST_generator',C/'generator.py');audit_module=c.load('v1509_frozen_PRIEST_audit',C/'audit.py')
     def stage(mode,maximum,seconds):
      value=dict(authority,mode=mode,maximum_analytical_native=maximum,tested_source_hashes=source);value['hard_stop_monotonic']=min(authority['hard_stop_monotonic'],time.monotonic()+seconds);value['absolute_deadline_unix']=min(authority['absolute_deadline_unix'],time.time()+seconds)
      return value
     phase=stage('PRIEST_RESPONSE_GENERATE',authority['generation_native'],c.limits()['generation_stage_s']);result['generation_executed']=True;result['generation_analytical_native']=None;result['generation_inflight_unknown']=True
     generation,arrays=generator.generate(current,proposal,setup,authority=phase,lock=lock,save_branch=store.save,save_origin=lambda value:saved(task/'GENERATION_ORIGIN.json',value))
     result.update(generation_analytical_native=generation['analytical_native'],generation_inflight_unknown=generation['analytical_inflight_unknown'],generation_explicit_Predictors=generation['explicit_predictor_constructions'],generation_branch_copies=generation['branch_copies'],generation_nominal_native=generation['nominal_native'])
     if not generation['passed']:result['first_error']=generation.get('first_error')or generation.get('stop_reason')or'GENERATION_REFUSED'
     saved(task/'GENERATION.json',generation);returned_save_attempted=True;returned.save_returned(task,generation,arrays,writer=writer,boundary=boundary);store.close(generation_result_sha256=c.sha(task/'GENERATION.json'))
     reader=codec.BranchReader(task,binding=binding,generation_result_sha256=c.sha(task/'GENERATION.json'));evidence=returned.read_returned(task)
     if contract.audit_allowed(generation,saved=True,branch_count=len(reader.rows)):
      phase=stage('PRIEST_RESPONSE_INDEPENDENT_AUDIT',authority['success_only_audit_native'],c.limits()['audit_stage_s']);result['independent_audit_executed']=True;result['audit_analytical_native']=None;result['audit_inflight_unknown']=True
      audit=audit_module.audit(current,proposal,setup,evidence,branch_count=len(reader.rows),read_branch=reader.read,authority=phase,lock=lock,save_origin=lambda value:saved(task/'AUDIT_ORIGIN.json',value));result.update(audit_analytical_native=audit['audit_analytical_native'],audit_inflight_unknown=audit['audit_inflight_unknown'],audit_explicit_Predictors=audit['explicit_predictor_constructions'],audit_branch_copies=audit['branch_copies'])
      if not audit['passed']:result['first_error']=audit.get('first_error')or'INDEPENDENT_AUDIT_REFUSED'
      saved(task/'AUDIT.json',audit)
      result['passed']=generation['passed']and audit['passed'];result['first_error']=audit.get('first_error')if not audit['passed']else None
     else:result['first_error']=generation.get('first_error')or generation.get('stop_reason')or'GENERATION_OR_EVIDENCE_DEPENDENCY_REFUSED'
    except BaseException as error:
     if result['first_error']is None:result['first_error']=repr(error)
     else:result['secondary_errors'].append('evidence_or_audit:'+repr(error))
     result['traceback']=traceback.format_exc();result['passed']=False
     if arrays is not None and not returned_save_attempted:
      returned_save_attempted=True
      try:returned.save_returned(task,generation,arrays,writer=writer,boundary=boundary)
      except BaseException as save_error:result['secondary_errors'].append('returned_save:'+repr(save_error))
     if store and not store.closed:
      try:result['branch_abort']=store.abort(first_error=result['first_error'],generator_counts=generation or dict(analytical_native=result['generation_analytical_native'],inflight_unknown=result['generation_inflight_unknown']))
      except BaseException as save_error:result['secondary_errors'].append('branch_abort:'+repr(save_error))

 except BaseException as error:
  if result['first_error']is None:result['first_error']=repr(error)
  else:result['secondary_errors'].append(repr(error))
  result['traceback']=traceback.format_exc()
 finally:
  result.update(closed=True,wall_s=time.monotonic()-started,source_unchanged=None,internal_allocator_constructions_unknown=True)
  try:c.sources();result['source_unchanged']=True
  except BaseException as error:result['secondary_errors'].append('source_close:'+repr(error));result['passed']=False
  try:
   if writer is not None:
    with boundary_module.OutputBoundary(task,writer.reserve):codec.write_atomic(task/'RESULT.json',codec.encoded(result),writer)
   else:c.put(c.O/'RESULT.json',result)
  except BaseException as error:result['secondary_errors'].append('RESULT_save:'+repr(error));print('RESPONSE_RESULT_SAVE_GAP:'+repr(result),flush=True)
 return result

def main():
 c.bootstrap();c.guard();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('RESPONSE_ROOT_SCOPE_EXPIRED')))
 if(c.O/'RESPONSE_ONLY_ADMISSION.json').exists():signal.alarm(max(1,int(c.read(c.O/'RESPONSE_ONLY_ADMISSION.json')['absolute_deadline_unix']-time.time())))
 value=execute();return 0 if value['passed']else 1
if __name__=='__main__':raise SystemExit(main())
