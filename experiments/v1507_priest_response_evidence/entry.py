"""Once new response serializer/reader target, software arrays only, no model work."""
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

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def put(path,value):
 temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temporary.replace(path)

def main():
 assert sorted(os.sched_getaffinity(0))==[4]and os.environ.get('PHASE_REPO')==str(R)and time.time()+60<1795395600
 with(O/'ENTRY_ONCE_CLAIM.json').open('x')as stream:json.dump(dict(started_unix=time.time(),models=0),stream)
 class NoModels(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'jax','jaxlib','mujoco','torch','rclpy','vehicle','factory'}:raise AssertionError('EVIDENCE_TARGET_NO_MODEL_OR_OPTIMIZER:'+name)
 finder=NoModels();sys.meta_path.insert(0,finder)
 def profile(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'prediction.py','coupled_model.py','coupled_control.py','vehicle_control.py','kernel.py'}:raise AssertionError('EVIDENCE_TARGET_NO_MODEL_OR_ALLOCATOR_CALL')
 sys.setprofile(profile)
 common=load('v1507_original_immutable_guard',R/'experiments/v1504_priest_namespace_worker/common.py');common.guard(O)
 result=dict(passed=False,closed=False,scope='NEW_COMPLETE_BRANCH_AND_PARTIAL_STORAGE_SOFTWARE_ONLY',models=0,optimizer_calls=0,response_model_native=0,physical_native=0,Allocator_recomputations=0,replay_native=0)
 try:
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);parent=common.read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
   import numpy as np
   codec=load('v1507_new_stream_store',C/'branch_store.py');returned=load('v1507_new_returned_arrays',C/'returned_evidence.py');boundary_module=load('v1507_original_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');budget_module=load('v1507_original_writer',R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
   source=common.read(R/'runs/v1504_priest_namespace_worker/NUMERIC_SOURCE_FREEZE.json')['files'].copy();assert all(common.sha(R/n)==h for n,h in source.items())
   for file in C.iterdir():
    if file.is_file():source[str(file.relative_to(R))]=common.sha(file)
   identity=common.digest(source);binding=dict(input_sha256='a'*64,proposal_sha256='b'*64,causal_snapshot_sha256='c'*64,tested_source_manifest_sha256=identity,geometry_kind='FULL_PERIOD_DISK',origin_native=0,software_fixture=True)
   states=np.arange(1608,dtype=np.float64).reshape(201,8)/1609.;ctrl=np.arange(800,dtype=np.float64).reshape(200,4)/801.;states[0,:4]=[0.,-0.,np.nextafter(0.,1.),-np.nextafter(0.,1.)]
   def proof(index,unsafe=False):return dict(before_native=index,complete_native=200,causal_tube_lower_m=.21 if unsafe else .3,rest=np.bool_(not unsafe),body_caps=True,current_input_sha256='a'*64,proposal_sha256='b'*64,geometry_kind='FULL_PERIOD_DISK',causal_snapshot_sha256='c'*64)
   def bits(a,b):assert a.shape==b.shape and a.dtype==b.dtype and np.array_equal(a.view(np.uint64),b.view(np.uint64))
   failures=[]
   def rejects(name,fn):
    try:fn()
    except (AssertionError,FileNotFoundError,ValueError,KeyError)as error:failures.append(dict(name=name,error=repr(error)))
    else:raise AssertionError('EVIDENCE_NEGATIVE_ACCEPTED:'+name)
   task=O/'software';task.mkdir();writer=budget_module.WriterBudget(task,role='PLANNER',maximum_bytes=2*1024**2,source_identity=identity)
   with boundary_module.OutputBoundary(task,writer.reserve)as boundary:
    store=codec.BranchStore(task,writer=writer,boundary=boundary,binding=binding);initial_debit=writer._read()['charged_bytes'];first=store.save(proof(0),states,ctrl);after_first=writer._read()['charged_bytes'];assert after_first-initial_debit==first['stream_bytes'],'SINGLE_PREWRITE_DEBIT_NOT_EXACT'
    rejects('OUT_OF_ORDER_BRANCH',lambda:store.save(proof(2),states,ctrl));assert store.count==1
    rejects('INCOMPLETE_199_CONTROL',lambda:store.save(proof(1),states,ctrl[:-1]));assert store.count==1
    store.save(proof(1,True),states,ctrl);seal=store.close(generation_result_sha256='d'*64);assert seal['records']==2
    reader=codec.BranchReader(task,binding=binding,generation_result_sha256='d'*64)
    for index in range(2):
     value,ss,uu=reader.read(index);bits(ss,states);bits(uu,ctrl);assert value==codec.normalized(proof(index,index==1))
    original=(task/'BRANCHES.bin').read_bytes()
    def replace_blob(value):codec.write_atomic(task/'BRANCHES.bin',value,writer)
    replace_blob(original[:-1]);rejects('TRUNCATED_STREAM',lambda:codec.BranchReader(task,binding=binding,generation_result_sha256='d'*64));replace_blob(original)
    damaged=bytearray(original);damaged[-1]^=1;replace_blob(bytes(damaged));rejects('CORRUPTED_PAYLOAD',lambda:codec.BranchReader(task,binding=binding,generation_result_sha256='d'*64));replace_blob(original)
    replace_blob(original+b'x');rejects('UNDECLARED_TRAILING_BYTES',lambda:codec.BranchReader(task,binding=binding,generation_result_sha256='d'*64));replace_blob(original)
    foreign=dict(binding,input_sha256='e'*64);rejects('CHANGED_CURRENT_SOURCE',lambda:codec.BranchReader(task,binding=foreign,generation_result_sha256='d'*64));rejects('CHANGED_GENERATION_ID',lambda:codec.BranchReader(task,binding=binding,generation_result_sha256='e'*64))
    example_counts=dict(analytical_native=236,analytical_inflight_unknown=True,nominal_native=0,complete_stop_branches=1,software_counter_example_not_measurement=True)
    generation=dict(passed=False,closed=True,first_error='SOFTWARE_PRODUCER_FIRST_ERROR',**example_counts)
    arrays=dict(states=states[:1],ctrl=np.empty((0,4),dtype=np.float64),memory=np.empty((0,5),dtype=np.float64),journal=[],modes=[],partial_branch=dict(before_native=1,states=states[:37],ctrl=ctrl[:36],complete=False,inflight_unknown=True,first_error=generation['first_error']))
    returned.save_returned(task,generation,arrays,writer=writer,boundary=boundary);restored=returned.read_returned(task);bits(restored['partial_branch']['states'],states[:37]);bits(restored['partial_branch']['ctrl'],ctrl[:36]);assert restored['generation']==generation and restored['partial_branch']['inflight_unknown']is True
   abort_task=O/'abort';abort_task.mkdir();abort_writer=budget_module.WriterBudget(abort_task,role='PLANNER',maximum_bytes=512*1024,source_identity=identity)
   with boundary_module.OutputBoundary(abort_task,abort_writer.reserve)as boundary:
    store=codec.BranchStore(abort_task,writer=abort_writer,boundary=boundary,binding=binding);store.save(proof(0),states,ctrl)
    original_atomic=codec.write_atomic
    def fail_abort(path,*args):
     if path.name=='BRANCH_ABORT.json':raise OSError('SOFTWARE_SECONDARY_SAVE_ERROR')
     return original_atomic(path,*args)
    codec.write_atomic=fail_abort
    try:aborted=store.abort(first_error='SOFTWARE_PRODUCER_FIRST_ERROR',generator_counts=example_counts)
    finally:codec.write_atomic=original_atomic
    assert aborted['first_error']=='SOFTWARE_PRODUCER_FIRST_ERROR'and 'SOFTWARE_SECONDARY_SAVE_ERROR'in aborted['abort_receipt_save_error']and aborted['actual_saved_bytes']==aborted['acknowledged_record_bytes']and not aborted['unacknowledged_tail_unknown']
    rejects('ABORT_WITHOUT_COMPLETE_SEAL',lambda:codec.BranchReader(abort_task,binding=binding,generation_result_sha256='d'*64))
   cap_task=O/'cap';cap_task.mkdir();cap_writer=budget_module.WriterBudget(cap_task,role='PLANNER',maximum_bytes=16384,source_identity=identity)
   with boundary_module.OutputBoundary(cap_task,cap_writer.reserve)as boundary:rejects('BYTE_CAP_BEFORE_OPEN',lambda:codec.BranchStore(cap_task,writer=cap_writer,boundary=boundary,binding=binding))
   assert not(cap_task/'BRANCHES.bin').exists()
   put(O/'STORAGE_TARGET_PROOF.json',dict(passed=True,software_inputs_only=True,new_integrations=0,complete_branches_read=2,refused_unsafe_proof_saved=True,bitwise_float64_including_signed_zero_and_subnormal=True,single_prewrite_debit=True,full201states200ctrl_each=True,partial_saved_states=37,partial_saved_ctrl=36,original_first_error_and_secondary_save_error_retained=True,abort_proof=aborted,negative_cases=failures,writer_actual_debit=writer._read(),read_only_fsync_actual_path_passed=True,models=0))
   assert all(common.sha(R/n)==h for n,h in source.items());put(O/'SOURCE_FREEZE.json',dict(files=source,source_and_storage_only_qualified=True,models=0,numerical_response_qualified=False));result.update(passed=True,negative_cases=len(failures),source_frozen=True,complete_response_or_actual_admission=False)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  result['closed']=True;put(O/'ENTRY_QUALIFICATION.json',result);sys.setprofile(None);sys.meta_path.remove(finder)
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
