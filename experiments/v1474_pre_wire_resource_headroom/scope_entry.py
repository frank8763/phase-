"""Near-expiry resource grant handoff before fresh source acquisition only."""
import ast
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import time
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;F=R/'experiments/v1472_closure_write_accounting';FO=R/'runs'/F.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*_):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('RESOURCE_HEADROOM_MODELS_FORBIDDEN:'+name)

def qualify(task):
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'ENTRY_ONCE_CLAIM.json').exists()
 (O/'ENTRY_ONCE_CLAIM.json').write_text(json.dumps(dict(unix=time.time(),models=0,scope='NEAR_EXPIRY_RESOURCE_PREPARATION_BEFORE_SOURCE'))+'\n')
 finder=NoModels();sys.meta_path.insert(0,finder);previous=sys.getprofile()
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_filename.startswith(str(R)+'/')and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py','vehicle_control.py'}:raise AssertionError('RESOURCE_HEADROOM_CONSTRUCTOR_STEP_COMPUTE_FORBIDDEN')
 sys.setprofile(forbid);result=dict(passed=False,models=0,physical_native=0,allocator_recomputations=0,actual_replay_native=0,software_only=True);first=None;negatives=[]
 io=exact('v1474_original_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');contract=exact('v1474_current_scope',C/'contract.py')
 def rejected(label,fn):
  try:fn()
  except (AssertionError,RuntimeError,FileExistsError,FileNotFoundError):negatives.append(label);return
  raise AssertionError('RESOURCE_HEADROOM_NEGATIVE_ACCEPTED:'+label)
 try:
  parentpath=R/'runs/v1382_weekend_campaign/LEDGER.json';before=parentpath.read_bytes();parent=json.loads(before);assert parent['active_round']is None and not parent['models_now_authorized']
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   prior=contract.read(FO/'SCOPE_QUALIFICATION.json');assert prior['passed']and prior['models']==prior['physical_native']==0
   oldfrozen=contract.read(FO/'SOURCE_FREEZE.json')['files'];assert all(contract.sha(R/p)==h for p,h in oldfrozen.items())
   unchanged=[]
   for p in sorted(C.glob('*.py')):
    if p.name in {'scope_entry.py','wire_grant.py'}:continue
    restored=p.read_text().replace('v1474_pre_wire_resource_headroom','v1472_closure_write_accounting').replace('v1474','v1472')
    assert ast.dump(ast.parse(restored))==ast.dump(ast.parse((F/p.name).read_text())),'UNDECLARED_RESOURCE_HEADROOM_CHANGE:'+p.name;unchanged.append(p.name)
   for name in ['TASKS.json','LIMITS.json','WRITER_CAPS.json']:
    assert json.loads((C/name).read_text().replace('v1474_pre_wire_resource_headroom','v1472_closure_write_accounting').replace('v1474','v1472'))==contract.read(F/name)
   source=ast.parse((C/'wire_grant.py').read_text());old=ast.parse((F/'wire_grant.py').read_text())
   # Only wrap the original reuse return with the explicit resource margin;
   # preserve the capacity admission *before* considering early retirement.
   function=next(n for n in source.body if isinstance(n,ast.FunctionDef))
   parent_if=function.body[2].body[2]
   assert isinstance(parent_if,ast.If)and ast.unparse(parent_if.test)=="permitted and time.monotonic() < grant['expires_monotonic']"
   margin=parent_if.body[-1];assert isinstance(margin,ast.If)and ast.unparse(margin.test)=="grant['expires_monotonic'] - time.monotonic() >= 0.5"
   ret=margin.body[0];ret.value.keywords=[k for k in ret.value.keywords if k.arg!='minimum_resource_headroom_s'];parent_if.body[-1]=ret
   assert ast.dump(source)==ast.dump(old),'UNDECLARED_WIRE_RESOURCE_POLICY_CHANGE'
   life=exact('v1474_exact_scope_lifecycle',C/'lifecycle.py');sup=exact('v1474_once_supervisor',C/'supervisor.py')
   rejected('native_missing_newscope_admission',lambda:life.run(task,{},{}));rejected('once_missing_newscope_admission',lambda:sup.launch('first_event'))
   limits=contract.read(C/'LIMITS.json');sup.budget.limits_check(limits);qmodule=exact('v1474_exact_byte_quota',C/'quota.py');boundary=exact('v1474_original_boundary',C/'bounded_io.py')
   folder=O/'software_headroom';folder.mkdir();quota=qmodule.EvidenceQuota(folder,limits);quota.bind_external_names([]);quota.external_writers=[];quota.write_enforcement_active=True
   caps=contract.read(C/'WRITER_CAPS.json');assert sum(caps.values())==56*1024**2
   for role,cap in caps.items():quota.hold('future_external:'+role,cap)
   original_used=qmodule.base.used;events=[];calls=[];emissions=[]
   def counted(path):calls.append(str(path));events.append('du');return original_used(path)
   def charge(path,n):emissions.append(n);return quota.charge_write(path,n)
   qmodule.base.used=counted;peer=None;pump=None
   try:
    with boundary.OutputBoundary(folder,charge):
     quota.prepare_grant(8*1024**2,phase='BEFORE_ACTUAL5_NATIVE_WIRE',valid_for_s=2,external_writers=[])
     original_expires=quota.grant['expires_monotonic'];sequence=quota.grant['sequence']
     owner=SimpleNamespace(quota=quota,output=folder,native=SimpleNamespace(vehicle=SimpleNamespace(count=5),run_id='V1474_SOFTWARE_ONLY'),atomic=io.atomic)
     def envelope():
      events.append('fresh_software_sample');return dict(software_only=True,sampled_at=time.monotonic(),resource_sequence=quota.grant['sequence'])
     owner.envelope=envelope
     def append(value):
      with(folder/'SOFTWARE_RECEIPT.jsonl').open('a')as stream:stream.write(json.dumps(value,allow_nan=False)+'\n')
     pump=life.pump_module.Pump(owner,check_budget=lambda *_:None,append=append,model_peer=None)
     peer=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);peer.bind(pump.peer);peer.settimeout(.2)
     # Real clock elapsed against the exact original2s TTL; no fake time or
     # sleeps in production. This software scope performs no native action.
     delay=max(0.,original_expires-time.monotonic()-.35);time.sleep(delay)
     pre_sample_remaining=original_expires-time.monotonic();assert 0<pre_sample_remaining<.5,'SOFTWARE_SCHEDULING_MISSED_NEAR_EXPIRY_CASE'
     events.clear();count_before=len(calls);pump.publish();wire=json.loads(peer.recv(65536))
     assert events==['du','du','fresh_software_sample']and len(calls)==count_before+2 and wire['resource_sequence']==sequence+1
     assert wire['sampled_at']>=quota.grant['prepared_monotonic']and quota.grant['expires_monotonic']>original_expires
     assert abs(quota.grant['expires_monotonic']-quota.grant['prepared_monotonic']-2)<1e-9
     result['near_expiry_proof']=dict(prior_resource_remaining_s=pre_sample_remaining,du_before_new_sample=2,source_sampled_after_new_grant=True,TTL_s=2,minimum_resource_headroom_s=.5)
     # Actual original receive appends through quota after receiving a software
     # packet; no source certificate or physical observation is fabricated.
     packet=dict(run_id=owner.native.run_id,kind='SOFTWARE_ONLY_RECEIPT');peer.sendto(json.dumps(packet).encode(),pump.address)
     assert pump.receive()==packet
     events.clear();count_before=len(calls);expires=quota.grant['expires_monotonic'];sequence=quota.grant['sequence'];pump.publish();peer.recv(65536)
     assert events==['fresh_software_sample']and len(calls)==count_before and quota.grant['expires_monotonic']==expires and quota.grant['sequence']==sequence
     remaining=quota.grant['remaining_bytes'];quota.grant['remaining_bytes']=65535
     # Explicit software boundary input checks an insufficient *valid* grant
     # near expiry. It must fail rather than use early retirement to refill.
     quota.grant['expires_monotonic']=time.monotonic()+.3;events.clear();count_before=len(calls)
     rejected('insufficient_near_expiry_cannot_refill',pump.publish);assert not events and len(calls)==count_before and quota.grant['sequence']==sequence
     quota.grant['remaining_bytes']=remaining;quota.grant['expires_monotonic']=expires
     rejected('original_wire_TTL_not_extended',lambda:quota.prepare_grant(4096,phase='BEFORE_ACTUAL5_NATIVE_WIRE',valid_for_s=2.001,external_writers=[]))
     # The rejected prepare checks TTL before changing the grant.
     assert quota.grant['expires_monotonic']==expires
   finally:
    if peer is not None:peer.close()
    if pump is not None:pump.close()
    qmodule.base.used=original_used
   storage=sup.budget.storage_preflight(limits);inherited=dict(oldfrozen);inherited.update({str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()})
   assert parentpath.read_bytes()==before and not(O/'ROUND_WINDOW.json').exists()and not(O/'first_event').exists()
   result.update(passed=True,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,negatives_rejected=negatives,entry_gates=prior['entry_gates'],external_writer_hook_qualification=prior['external_writer_hook_qualification'],writer_source_proofs=prior['writer_source_proofs'],source_hashes=inherited,storage_preflight=storage,reused_scope_entry_SHA=contract.sha(FO/'SCOPE_QUALIFICATION.json'),normalized_unchanged_production_files=unchanged,actual_Pump_publish_receive_software_only_real_sockets=True,resource_headroom_check_only_change=True,valid_reuse_no_du_no_TTL_reset=True,insufficient_near_expiry_refused_before_refill=True,all_external_future_caps_held_bytes=sum(caps.values()),live_child_metadata_not_forged=True,source200ms_and_originalscience_unchanged=True,whole_route_admission=False,live_event_runtime_passed=False,source_remote_recovery_still_required=True)
 except BaseException as exc:
  import traceback
  first=dict(error=repr(exc),traceback=traceback.format_exc());result['first_error']=first
 finally:
  sys.setprofile(previous);sys.meta_path.remove(finder);io.atomic(O/'SCOPE_QUALIFICATION.json',result);io.atomic(O/'ENTRY_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,first_error=first))
  files=result.get('source_hashes')or{str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()};io.atomic(O/'SOURCE_FREEZE.json',dict(files=files,entry_passed=result['passed'],models=0,whole_route_admission=False))
 return 0 if result['passed']else 1
