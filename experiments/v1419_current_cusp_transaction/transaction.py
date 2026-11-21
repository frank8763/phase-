"""One current CUSP witness transaction in the canonical native owner process.

No plant construction, launch, socket, or step occurs here. The outer registered
route must supply actual native owner, current notice, authority, and model peer.
"""
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

owner=exact('v1419_current_event_owner',R/'experiments/v1415_unified_causal_witness/event_owner.py')
generator=exact('v1419_complete_generator',R/'experiments/v1415_unified_causal_witness/generator.py')
auditor=exact('v1419_corrected_auditor',C/'audit.py')
store_module=exact('v1419_complete_branches',R/'experiments/v1407_lossless_branch_stream/stream.py')

class CuspTransaction:
 def __init__(self,*,native,output,setup,authority,lock,budget,limits,atomic,np,peer_command,peer_replies):
  self.native=native;self.output=Path(output).resolve();self.setup=copy.deepcopy(setup);self.authority=copy.deepcopy(authority)
  self.lock=lock;self.budget=budget;self.limits=copy.deepcopy(limits);self.atomic=atomic;self.np=np;self.peer=peer_command;self.peer_replies=peer_replies
  assert callable(peer_command)and callable(peer_replies)
  assert self.output.is_relative_to(R/'runs')and self.output.is_dir()
  assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(R)
  assert authority['scope']=='ACTUAL_ROUTE_EVENT_WITNESS'and authority['models_authorized']is True
  assert Path('/proc/self/fd/'+str(lock.fileno())).resolve()==R/'runs/v648_static_unknown/execution.lock'
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert native.applied==native.vehicle.count and native.gear.last_tick==native.applied-1
  native.mode_memory.snapshot(native.applied)
  self.last_event=-1;self.closed=False;self.active=False

 def authority_for(self,request):
  parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());a=copy.deepcopy(self.authority)
  assert parent['models_now_authorized']and parent['active_round']==a['round_id']
  assert a['boot_id']==parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
  assert a['absolute_deadline_unix']<=1795395600 and a['hard_stop_monotonic']<=parent['hard_stop_monotonic']
  assert time.time()<a['absolute_deadline_unix']-60 and time.monotonic()<a['hard_stop_monotonic']-60
  assert not self.budget.get('generation_inflight_unknown',False)and not self.budget.get('audit_inflight_unknown',False)
  genleft=self.limits['maximum_generation_native']-self.budget['generation_native'];audleft=self.limits['maximum_audit_native']-self.budget['audit_native']
  assert 200<=genleft<=1005000 and 200<=audleft<=1005000
  a.update(scope='CURRENT_EVENT_COMPLETE_MODEL_WITNESS',current_input_sha256=request.current['input_sha256'],maximum_analytical_native=genleft,maximum_nominal_native=self.limits['maximum_nominal_native'])
  return a,audleft

 def run(self,notice):
  assert not self.closed and not self.active and self.last_event+1<self.limits['maximum_events']
  assert notice['event_index']==self.last_event+1
  self.active=True;request=None;folder=None;store=None;generation=None;audit=None;first_error=None;stage='BIND_CURRENT_EVENT'
  before_account=copy.deepcopy(self.budget);initial_native=self.native.vehicle.count;initial_state_sha=owner.base.base.measured_identity(self.native.vehicle)
  try:
   request=owner.OwnerRequest(notice,output=self.output,vehicle=self.native.vehicle,mode_memory=self.native.mode_memory,gear=self.native.gear,run_id=self.native.run_id,last_event_index=self.last_event,now=time.monotonic())
   folder=self.output/'bridge_events'/('event%04d'%notice['event_index']);folder.mkdir(parents=True,exist_ok=False)
   self.atomic(folder/'CURRENT_INPUT.json',request.current);self.atomic(folder/'SETUP.json',self.setup)
   a,audleft=self.authority_for(request)
   self.atomic(folder/'GENERATION_AUTHORITY.json',a)
   store=store_module.BranchStore(folder/'branches',input_sha256=request.current['input_sha256'],np=self.np,atomic=self.atomic,maximum_branches=self.limits['maximum_nominal_native'])
   stage='GENERATE';self.budget['generation_inflight_unknown']=True
   generation,data=generator.generate(request.current,self.setup,authority=a,lock=self.lock,peer_command=self.peer,save_branch=store.append)
   # The generator persists each complete refused branch before testing gates.
   self.budget['generation_native']+=generation['analytical_native'];self.budget['generation_inflight_unknown']=generation['analytical_inflight_unknown']
   self.atomic(folder/'GENERATION.json',generation)
   with (folder/'NOMINAL.npz').open('xb')as stream:self.np.savez_compressed(stream,states=self.np.asarray(data['states']),ctrl=self.np.asarray(data['ctrl']))
   for key in ['journal','memory','modes']:self.atomic(folder/(key.upper()+'.json'),data[key])
   partial=data.get('partial_branch')
   if partial is not None:
    with(folder/'PARTIAL_BRANCH.npz').open('xb')as stream:self.np.savez_compressed(stream,states=partial['states'],ctrl=partial['ctrl'])
    self.atomic(folder/'PARTIAL_BRANCH.json',{k:v for k,v in partial.items()if k not in {'states','ctrl'}})
   store.close();store=None
   assert generation['passed']is True and generation['closed']and not generation['analytical_inflight_unknown'],'CURRENT_EVENT_GENERATION_REFUSED'
   assert digest(request.current)==digest(json.loads((folder/'CURRENT_INPUT.json').read_text()))
   assert self.native.vehicle.count==request.start_native and owner.base.base.measured_identity(self.native.vehicle)==request.start_full_state_sha256
   stage='AUDIT'
   aa=dict(mode='CURRENT_WITNESS_INDEPENDENT_AUDIT',round_id=a['round_id'],input_sha256=request.current['input_sha256'],maximum_steps=audleft,boot_id=a['boot_id'],absolute_deadline_unix=a['absolute_deadline_unix'],hard_stop_monotonic=a['hard_stop_monotonic'],source_hashes=a['tested_source_hashes'])
   self.atomic(folder/'AUDIT_AUTHORITY.json',aa)
   # RPP replies are supplied by the separate modeled-peer recorder, never the
   # live route command stream. Its snapshot must be immutable after generate.
   data['original_rpp_replies']=copy.deepcopy(self.peer_replies())
   self.atomic(folder/'MODELED_ACCEPTED.json',data['original_rpp_replies'])
   self.budget['audit_inflight_unknown']=True
   audit=auditor.audit(request.current,self.setup,data,folder/'branches',authority=aa,lock=self.lock)
   self.budget['audit_native']+=audit['audit_analytical_native'];self.budget['audit_inflight_unknown']=audit['audit_inflight_unknown']
   self.atomic(folder/'INDEPENDENT_AUDIT.json',audit)
   assert audit['passed']is True and audit['closed']and not audit['audit_inflight_unknown'],'CURRENT_EVENT_INDEPENDENT_AUDIT_REFUSED'
   stage='COMMIT'
   files=sorted(p for p in folder.rglob('*')if p.is_file())
   ready=request.commit(vehicle=self.native.vehicle,mode_memory=self.native.mode_memory,gear=self.native.gear,generation=generation,audit=audit,evidence_files=files,manifest_path=folder/'CERTIFICATE.json')
   self.last_event=notice['event_index'];stage='READY'
   return request,ready,data['states']
  except BaseException as exc:
   first_error=dict(error=repr(exc),traceback=traceback.format_exc(),stage=stage)
   self.closed=True
   if request is not None:failure=request.reject(repr(exc))
   else:failure=dict(kind='BRIDGE_FAILED',run_id=self.native.run_id,event_index=notice.get('event_index'),reason=repr(exc),physical_admission=False)
   self.atomic((folder if folder is not None else self.output)/('TRANSACTION_ERROR.json'if folder is not None else 'CUSP_BIND_ERROR.json'),dict(first_error=first_error,notice=copy.deepcopy(notice),failure=failure,accounting=copy.deepcopy(self.budget)))
   raise
  finally:
   self.active=False
   closing_errors=[]
   if store is not None:
    try:store.close()
    except BaseException as exc:closing_errors.append(dict(stage='CLOSE_BRANCH_STREAM',error=repr(exc)))
   actual_delta=self.native.vehicle.count-initial_native;actual_unchanged=owner.base.base.measured_identity(self.native.vehicle)==initial_state_sha
   if actual_delta!=0 or not actual_unchanged:closing_errors.append(dict(stage='ACTUAL_OWNER_CHANGED',actual_native_delta=actual_delta,full_state_unchanged=actual_unchanged))
   if folder is not None:
    self.atomic(folder/'TRANSACTION_CLOSED.json',dict(closed=True,passed=stage=='READY'and not closing_errors,stage=stage,first_error=first_error,closing_errors=closing_errors,before_accounting=before_account,accounting=copy.deepcopy(self.budget),independent_audit_unexecuted=audit is None,actual_native_delta_during_certificate=actual_delta,actual_full_state_unchanged=actual_unchanged,physical_admission=False))
   if closing_errors and first_error is None:
    self.closed=True
    raise RuntimeError('CURRENT_CUSP_TRANSACTION_CLOSURE_FAILED:'+repr(closing_errors))
