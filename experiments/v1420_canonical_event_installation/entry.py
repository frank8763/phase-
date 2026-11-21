"""CPU2/run_phase zero-model fault probes of the new production transaction.

Saved numerical arrays are storage inputs only. Injected callbacks never invoke
old generators/audits or create a model. No physical permission is produced.
"""
import ast
import copy
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoPhysical(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('CUSP_INSTALLATION_ENTRY_PHYSICAL_IMPORT_FORBIDDEN:'+name)

def main():
 assert sys.argv[1:]==['--entry-check']and os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 assert not(O/'ENTRY_QUALIFICATION.json').exists();os.chdir(R);sys.meta_path.insert(0,NoPhysical());calls=[]
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'}:
   calls.append(frame.f_code.co_name);raise AssertionError('CUSP_INSTALLATION_ZERO_MODEL_CONSTRUCTOR_OR_STEP')
 sys.setprofile(forbid)
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply()
 guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  module=exact('v1420_production_canonical_owner',C/'canonical_owner.py');tx=module.transaction_module
  assert Path(tx.CuspTransaction.run.__code__.co_filename).resolve()==C/'transaction.py'
  assert Path(module.guard_module.PhysicalGuard.at_event.__func__.__code__.co_filename).resolve()==R/'experiments/v1415_unified_causal_witness/physical_guard.py'
  assert Path(module.bridge_module.BridgeExecution.advance.__code__.co_filename).resolve()==R/'experiments/v1415_unified_causal_witness/bridge_execution.py'
  io=exact('v1420_original_atomic_io',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');import numpy as np
  old=R/'runs/v1417_complete_timed_witness/model';index=json.loads((old/'branches/INDEX.json').read_text());reader=tx.store_module.BranchReader(old/'branches',index,np);states,ctrl=reader.read(index['branches'][0]);reader.finish()
  current=json.loads((old/'CURRENT_INPUT.json').read_text());results=[]
  def never(*args,**kwargs):raise AssertionError('ZERO_MODEL_AUDIT_OR_PEER_MUST_NOT_RUN')
  realgen=tx.generator
  try:
   for case in ['bind_error','complete_refusal','partial_unknown','first_error_plus_save_close_error']:
    out=O/case;out.mkdir();synthetic_native=SimpleNamespace(vehicle=SimpleNamespace(count=0,d=SimpleNamespace(qpos=np.zeros(7),qvel=np.zeros(6),ctrl=np.zeros(4),mocap_pos=np.zeros((1,3)),mocap_quat=np.zeros((1,4)),time=0.)),run_id='SOFTWARE_FAULT_PROBE_NO_PLANT')
    t=tx.CuspTransaction.__new__(tx.CuspTransaction);t.native=synthetic_native;t.output=out;t.setup={};t.lock=lock;t.budget=dict(generation_native=0,audit_native=0,generation_inflight_unknown=False,audit_inflight_unknown=False);t.limits=dict(maximum_events=1,maximum_nominal_native=1);t.np=np;t.peer=never;t.peer_replies=never;t.last_event=-1;t.closed=False;t.active=False
    attempts=[]
    def atomic(path,value):
     attempts.append(path.name)
     if case=='first_error_plus_save_close_error'and path.name in {'TRANSACTION_ERROR.json','TRANSACTION_CLOSED.json'}:raise OSError('INJECTED_SAVE_OR_CLOSE_FAILURE')
     io.atomic(path,value)
    t.atomic=atomic
    class Request:
     def __init__(self):self.current=copy.deepcopy(current)
     def reject(self,reason):return dict(kind='BRIDGE_FAILED',reason=reason,software_probe=True,physical_admission=False)
    def bind(notice):
     if case=='bind_error':raise RuntimeError('INJECTED_FIRST_BIND_FAILURE')
     return Request()
    t.bind_request=bind;t.authority_for=lambda request:({},200)
    def generated(cur,setup,*,authority,lock,peer_command,save_branch):
     result=dict(passed=False,closed=True,analytical_native=0,analytical_inflight_unknown=case=='partial_unknown',error='INJECTED_ZERO_MODEL_GENERATION_REFUSAL',qualification_copied_arrays_not_integrations=True)
     data=dict(states=[states[0]],ctrl=[],journal=[],memory=[],modes=[],partial_branch=None)
     if case=='partial_unknown':data['partial_branch']=dict(before_native=0,states=states[:37],ctrl=ctrl[:36],analytical_inflight_unknown=True,qualification_copied_prefix_not_integrations=True)
     else:save_branch(dict(index['branches'][0]['proof'],qualification_copied_arrays_not_integrations=True),states,ctrl)
     return result,data
    tx.generator=SimpleNamespace(generate=generated)
    error=None
    try:t.run(dict(event_index=0,qualification_only=True))
    except BaseException as exc:error=exc
    assert t.closed and not t.active and synthetic_native.vehicle.count==0
    if case=='bind_error':
     assert isinstance(error,RuntimeError)and str(error)=='INJECTED_FIRST_BIND_FAILURE';assert json.loads((out/'CUSP_BIND_ERROR.json').read_text())['first_error']['error']==repr(error)
    else:
     assert isinstance(error,AssertionError)and str(error)=='CURRENT_EVENT_GENERATION_REFUSED'
     branch=json.loads((out/'bridge_events/event0000/branches/INDEX.json').read_text())
     if case=='partial_unknown':
      assert not branch['branches'];folder=out/'bridge_events/event0000'
      with np.load(folder/'PARTIAL_BRANCH.npz',allow_pickle=False)as partial:assert partial['states'].shape==(37,8)and partial['ctrl'].shape==(36,4)
      assert json.loads((folder/'TRANSACTION_CLOSED.json').read_text())['accounting']['generation_inflight_unknown']is True
     else:assert len(branch['branches'])==1 and branch['branches'][0]['raw_sha256']==index['branches'][0]['raw_sha256']
     if case=='first_error_plus_save_close_error':assert 'TRANSACTION_ERROR.json'in attempts and 'TRANSACTION_CLOSED.json'in attempts
    assert t.budget['generation_native']==t.budget['audit_native']==0
    results.append(dict(case=case,passed=True,primary_exception_preserved=repr(error),models=0,analytical_native=0,physical_native=0,copied_arrays_not_integrations=True))
  finally:tx.generator=realgen
  assert not calls
  io.atomic(O/'ENTRY_QUALIFICATION.json',dict(passed=True,models=0,analytical_native=0,physical_native=0,actual_installation_unexecuted=True,canonical_owner_import_pass=True,transaction_fault_paths_pass=True,actual_cpu=[2],original_writeguard=True,constructor_step_profile_guard=True,cases=results,source_hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.glob('*')if p.is_file()},physical_admission=False))
  print(json.dumps(dict(passed=True,models=0,analytical_native=0,cases=results)))
if __name__=='__main__':main()
