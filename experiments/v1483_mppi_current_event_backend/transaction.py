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

owner=exact('v1483_current_MPPI_event_owner',C/'event_owner.py')
generator=exact('v1419_complete_generator',C/'generator.py')
auditor=exact('v1420_corrected_auditor',C/'audit.py')
store_module=exact('v1419_complete_branches',R/'experiments/v1449_route_initializer_binding/branch_store.py')

class CuspTransaction:
 def __init__(self,*,native,output,setup,authority,lock,budget,limits,atomic,np,peer_command,peer_replies,quota):
  self.native=native;self.output=Path(output).resolve();self.setup=copy.deepcopy(setup);self.authority=copy.deepcopy(authority)
  self.quota=quota;self.lock=lock;self.budget=budget;self.limits=copy.deepcopy(limits);self.atomic=atomic;self.np=np;self.peer=peer_command;self.peer_replies=peer_replies
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
  genleft=min(genleft,self.limits['maximum_generation_per_event']);audleft=min(audleft,self.limits['maximum_audit_per_event'])
  assert 200<=genleft<=1005000 and 200<=audleft<=1005000
  a.update(scope='CURRENT_EVENT_COMPLETE_MODEL_WITNESS',current_input_sha256=request.current['input_sha256'],maximum_analytical_native=genleft,maximum_nominal_native=self.limits['maximum_nominal_native'])
  return a,audleft

 def bind_request(self,notice):
  packet=json.loads((R/notice['path']).read_text())
  if packet['request']['event']['kind']=='ORDERED_ROUTE_FIRST_SEGMENT_CHECK':
   assert self.native.bridge_started and self.last_event>=0,'ORDERED_EVENT_REQUIRES_ACTUAL_PRIOR_BRIDGE'
   assert packet['request']['completed_bridge_events']==self.last_event+1,'ORDERED_EVENT_PRIOR_BRIDGE_COUNT_CHANGED'
  return owner.OwnerRequest(notice,output=self.output,vehicle=self.native.vehicle,mode_memory=self.native.mode_memory,gear=self.native.gear,run_id=self.native.run_id,last_event_index=self.last_event,now=time.monotonic())

 def run(self,notice):
  assert not getattr(self,'stop_phase_entered',False),'NEW_EVENT_FORBIDDEN_DURING_STOP_PHASE'
  assert not self.closed and not self.active and self.last_event+1<self.limits['maximum_events']
  assert notice['event_index']==self.last_event+1
  self.active=True;request=None;folder=None;store=None;generation=None;audit=None;first_error=None;save_errors=[];stage='BIND_CURRENT_EVENT'
  before_account=copy.deepcopy(self.budget);initial_native=None;initial_state_sha=None
  try:
   initial_native=self.native.vehicle.count;initial_state_sha=owner.measured_identity(self.native.vehicle)
   request=self.bind_request(notice)
   self.quota.retire_grant();self.quota.prepare_grant(64*1024**2,phase='STOPPED_EVENT_PREPARATION',valid_for_s=1800,external_writers=self.quota.external_writers)
   folder=self.output/'bridge_events'/('event%04d'%notice['event_index']);folder.mkdir(parents=True,exist_ok=False)
   self.atomic(folder/'CURRENT_INPUT.json',request.current);self.atomic(folder/'SETUP.json',self.setup)
   a,audleft=self.authority_for(request)
   self.atomic(folder/'GENERATION_AUTHORITY.json',a)
   store=store_module.BranchStore(folder/'branches',input_sha256=request.current['input_sha256'],np=self.np,atomic=self.atomic,maximum_branches=self.limits['maximum_nominal_native'],quota=self.quota)
   stage='GENERATE';self.budget['generation_inflight_unknown']=True
   generation,data=generator.generate(request.current,self.setup,authority=a,lock=self.lock,peer_command=self.peer,save_branch=store.append)
   # The generator persists each complete refused branch before testing gates.
   self.budget['generation_native']+=generation['analytical_native'];self.budget['generation_inflight_unknown']=generation['analytical_inflight_unknown']
   self.atomic(folder/'GENERATION.json',generation)
   self.quota.save_npz(folder/'NOMINAL.npz',dict(states=self.np.asarray(data['states']),ctrl=self.np.asarray(data['ctrl'])),self.np)
   for key in ['journal','memory','modes']:self.atomic(folder/(key.upper()+'.json'),data[key])
   partial=data.get('partial_branch')
   if partial is not None:
    self.quota.save_npz(folder/'PARTIAL_BRANCH.npz',dict(states=partial['states'],ctrl=partial['ctrl']),self.np)
    self.atomic(folder/'PARTIAL_BRANCH.json',{k:v for k,v in partial.items()if k not in {'states','ctrl'}})
   store.close();store=None
   assert generation['passed']is True and generation['closed']and not generation['analytical_inflight_unknown'],'CURRENT_EVENT_GENERATION_REFUSED'
   assert digest(request.current)==digest(json.loads((folder/'CURRENT_INPUT.json').read_text()))
   assert self.native.vehicle.count==request.start_native and owner.measured_identity(self.native.vehicle)==request.start_full_state_sha256
   stage='AUDIT'
   aa=dict(mode='CURRENT_WITNESS_INDEPENDENT_AUDIT',round_id=a['round_id'],input_sha256=request.current['input_sha256'],maximum_steps=audleft,boot_id=a['boot_id'],absolute_deadline_unix=a['absolute_deadline_unix'],hard_stop_monotonic=a['hard_stop_monotonic'],source_hashes=a['tested_source_hashes'])
   self.atomic(folder/'AUDIT_AUTHORITY.json',aa)
   # MPPI replies are supplied by the separate modeled-peer recorder, never the
   # live route command stream. Its snapshot must be immutable after generate.
   data['modeled_mppi_replies']=copy.deepcopy(self.peer_replies())
   self.atomic(folder/'MODELED_ACCEPTED.json',data['modeled_mppi_replies'])
   self.budget['audit_inflight_unknown']=True
   audit=auditor.audit(request.current,self.setup,data,folder/'branches',authority=aa,lock=self.lock)
   self.budget['audit_native']+=audit['audit_analytical_native'];self.budget['audit_inflight_unknown']=audit['audit_inflight_unknown']
   self.atomic(folder/'INDEPENDENT_AUDIT.json',audit)
   assert audit['passed']is True and audit['closed']and not audit['audit_inflight_unknown'],'CURRENT_EVENT_INDEPENDENT_AUDIT_REFUSED'
   stage='COMMIT'
   files=sorted(p for p in folder.rglob('*')if p.is_file())
   self.quota.admit(8*sum(len(str(p))+128 for p in files)+262144,'COMMIT_EVENT_CERTIFICATE_FILES')
   ready=request.commit(vehicle=self.native.vehicle,mode_memory=self.native.mode_memory,gear=self.native.gear,generation=generation,audit=audit,evidence_files=files,manifest_path=folder/'CERTIFICATE.json')
   self.last_event=notice['event_index'];stage='READY'
   return request,ready,data['states']
  except BaseException as exc:
   first_error=dict(error=repr(exc),traceback=traceback.format_exc(),stage=stage)
   self.closed=True
   try:
    if request is not None:failure=request.reject(repr(exc))
    else:failure=dict(kind='BRIDGE_FAILED',run_id=self.native.run_id,event_index=notice.get('event_index'),reason=repr(exc),physical_admission=False)
   except BaseException as saving:
    save_errors.append(dict(stage='REJECT_NOTICE',error=repr(saving)));failure=None
   error_record=dict(first_error=first_error,notice=copy.deepcopy(notice),failure=failure,accounting=copy.deepcopy(self.budget),generation_primary_error=None if generation is None else generation.get('error'),save_errors=save_errors)
   try:self.atomic((folder if folder is not None else self.output)/('TRANSACTION_ERROR.json'if folder is not None else 'CUSP_BIND_ERROR.json'),error_record)
   except BaseException as saving:
    save_errors.append(dict(stage='SAVE_FIRST_ERROR',error=repr(saving)))
    os.write(2,(json.dumps(dict(error_record,evidence_save_failed=True),default=str,allow_nan=False)+'\n').encode())
   raise
  finally:
   self.active=False
   closing_errors=[]
   if store is not None:
    try:store.close()
    except BaseException as exc:closing_errors.append(dict(stage='CLOSE_BRANCH_STREAM',error=repr(exc)))
   actual_delta=None;actual_unchanged=None
   try:
    actual_delta=None if initial_native is None else self.native.vehicle.count-initial_native
    actual_unchanged=None if initial_state_sha is None else owner.measured_identity(self.native.vehicle)==initial_state_sha
    if actual_delta!=0 or actual_unchanged is not True:closing_errors.append(dict(stage='ACTUAL_OWNER_CHANGED_OR_UNKNOWN',actual_native_delta=actual_delta,full_state_unchanged=actual_unchanged))
   except BaseException as saving:closing_errors.append(dict(stage='READ_ACTUAL_OWNER_AT_CLOSE',error=repr(saving)))
   if folder is not None:
    closure=dict(closed=True,passed=stage=='READY'and not closing_errors and not save_errors,stage=stage,first_error=first_error,closing_errors=closing_errors,save_errors=save_errors,before_accounting=before_account,accounting=copy.deepcopy(self.budget),independent_audit_unexecuted=audit is None,actual_native_delta_during_certificate=actual_delta,actual_full_state_unchanged=actual_unchanged,physical_admission=False)
    try:self.atomic(folder/'TRANSACTION_CLOSED.json',closure)
    except BaseException as saving:
     save_errors.append(dict(stage='SAVE_CLOSURE',error=repr(saving)));os.write(2,(json.dumps(dict(closure,evidence_save_failed=True),default=str,allow_nan=False)+'\n').encode())
   if (closing_errors or save_errors) and first_error is None:
    self.closed=True
    raise RuntimeError('CURRENT_CUSP_TRANSACTION_CLOSURE_FAILED:'+repr(closing_errors+save_errors))
