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
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;F=R/'experiments/v1474_pre_wire_resource_headroom';FO=R/'runs'/F.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*_):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('RESOURCE_HEADROOM_MODELS_FORBIDDEN:'+name)

def qualify(task):
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'ENTRY_ONCE_CLAIM.json').exists()
 (O/'ENTRY_ONCE_CLAIM.json').write_text(json.dumps(dict(unix=time.time(),models=0,scope='STREAMED_RETIREMENT_AND_BOUNDED_MEMORY'))+'\n')
 finder=NoModels();sys.meta_path.insert(0,finder);previous=sys.getprofile()
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_filename.startswith(str(R)+'/')and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py','vehicle_control.py'}:raise AssertionError('RESOURCE_HEADROOM_CONSTRUCTOR_STEP_COMPUTE_FORBIDDEN')
 sys.setprofile(forbid);result=dict(passed=False,models=0,physical_native=0,allocator_recomputations=0,actual_replay_native=0,software_only=True);first=None;negatives=[]
 io=exact('v1477_original_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');contract=exact('v1477_current_scope',C/'contract.py')
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
    if p.name in {'scope_entry.py','route_command.py','pump.py'}:continue
    restored=p.read_text().replace('v1477_streamed_route_retirement','v1474_pre_wire_resource_headroom').replace('v1477','v1474')
    assert ast.dump(ast.parse(restored))==ast.dump(ast.parse((F/p.name).read_text())),'UNDECLARED_RESOURCE_HEADROOM_CHANGE:'+p.name;unchanged.append(p.name)
   for name in ['TASKS.json','LIMITS.json','WRITER_CAPS.json']:
    assert json.loads((C/name).read_text().replace('v1477_streamed_route_retirement','v1474_pre_wire_resource_headroom').replace('v1477','v1474'))==contract.read(F/name)
   newpump=(C/'pump.py').read_text().replace("Path(__file__).with_name('route_command.py')","R/'experiments/v1411_native_guarded_execution/route_command.py'").replace("commands_module.Commands(owner.native.run_id,retirement_sink=lambda proof:self.append(dict(kind='RETIRED_ACTUAL_ROUTE',retirement=proof)))","commands_module.Commands(owner.native.run_id)")
   assert ast.dump(ast.parse(newpump))==ast.dump(ast.parse((F/'pump.py').read_text())),'UNDECLARED_PUMP_STREAMING_CHANGE'
   current=ast.parse((C/'route_command.py').read_text());original=ast.parse((R/'experiments/v1411_native_guarded_execution/route_command.py').read_text())
   original_class=next(x for x in original.body if isinstance(x,ast.ClassDef));current_class=next(x for x in current.body if isinstance(x,ast.ClassDef))
   orig_accept=next(x for x in original_class.body if x.name=='accept');new_accept=next(x for x in current_class.body if x.name=='accept')
   orig_if=next(x for x in orig_accept.body if isinstance(x,ast.If)and ast.unparse(x.test)=='reason');new_if=next(x for x in new_accept.body if isinstance(x,ast.If)and ast.unparse(x.test)=='reason')
   new_if.body=orig_if.body
   assert ast.dump(new_accept)==ast.dump(orig_accept),'IDENTITY_STATE_SOURCE_OR_ACCEPTANCE_CHANGED'
   life=exact('v1477_exact_scope_lifecycle',C/'lifecycle.py');sup=exact('v1477_once_supervisor',C/'supervisor.py')
   rejected('native_missing_newscope_admission',lambda:life.run(task,{},{}));rejected('once_missing_newscope_admission',lambda:sup.launch('first_event'))
   limits=contract.read(C/'LIMITS.json');sup.budget.limits_check(limits);qmodule=exact('v1477_exact_byte_quota',C/'quota.py');boundary=exact('v1477_original_boundary',C/'bounded_io.py')
   folder=O/'software_retirement';folder.mkdir();quota=qmodule.EvidenceQuota(folder,limits);quota.bind_external_names([]);quota.external_writers=[];quota.write_enforcement_active=True
   caps=contract.read(C/'WRITER_CAPS.json');assert sum(caps.values())==56*1024**2
   for role,cap in caps.items():quota.hold('future_external:'+role,cap)
   original_used=qmodule.base.used;events=[];calls=[];emissions=[]
   def counted(path):calls.append(str(path));events.append('du');return original_used(path)
   def charge(path,n):emissions.append(n);return quota.charge_write(path,n)
   qmodule.base.used=counted;peer=None;pump=None
   try:
    with boundary.OutputBoundary(folder,charge):
     quota.prepare_grant(16*1024**2,phase='STOPPED_EVENT_PREPARATION',valid_for_s=300,external_writers=[])
     run_id='V1477_SOFTWARE_ONLY';n=SimpleNamespace(vehicle=SimpleNamespace(count=5),run_id=run_id,sent={})
     owner=SimpleNamespace(quota=quota,output=folder,native=n,atomic=io.atomic)
     journal_path=folder/'SOFTWARE_RPC_JOURNAL.jsonl'
     def append(value):
      raw=json.dumps(value,separators=(',',':'),allow_nan=False)+'\n';quota.admit(2*len(raw.encode())+16384,'SOFTWARE_REAL_PRODUCTION_RECEIPT')
      with journal_path.open('a')as stream:stream.write(raw);stream.flush()
     pump=life.pump_module.Pump(owner,check_budget=lambda *_:None,append=append,model_peer=None)
     peer=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);peer.bind(pump.peer);peer.settimeout(.2)
     def frame(sequence,tick,acquired):
      return dict(schema=1,run_id=run_id,sequence=sequence,sampled_at=acquired,body=[0.]*5,ranges_m=[3.]*32,native_tick=tick,sim_time=tick*.01,sensor_frame=dict(native_tick=tick,time=tick*.01,xy=[0.,0.],yaw=0.,sampled_at=acquired))
     acquired=time.monotonic();n.sent[0]=frame(0,0,acquired)
     def packet(seq,wire):
      now=time.monotonic();origin=life.pump_module.commands_module.stamped.decode_origin(10**12,10**12,now)
      return dict(kind='command',run_id=run_id,sequence=seq,command_source='CONTROLLER',origin=origin,v=.1,w=0.,observation_sequence=wire['sequence'],observation_native_tick=wire['native_tick'],observation_sampled_at=wire['sampled_at'],issued_at=now)
     before_calls=len(calls);applied=[]
     for sequence in range(300):
      value=packet(sequence,n.sent[0]);peer.sendto(json.dumps(value).encode(),pump.address);received=pump.receive()
      command=pump.command_gate.accept(received,n.sent,current_native=5,now=time.monotonic())
      if command is not None:applied.append(command)
     assert not applied and pump.command_gate.retired_total==300 and len(pump.command_gate.retired)==256
     assert pump.command_gate.retired[0]['packet']['sequence']==44 and pump.command_gate.retired[-1]['packet']['sequence']==299
     assert len(calls)==before_calls,'STREAMING_HOT_RETIREMENT_FULL_DU'
     records=[json.loads(row)for row in journal_path.read_text().splitlines()];retired=[row['retirement']for row in records if row['kind']=='RETIRED_ACTUAL_ROUTE'];chain='0'*64
     import hashlib
     assert len(retired)==300
     for i,receipt in enumerate(retired,1):
      assert receipt['retired_count']==i and receipt['previous_chain_sha256']==chain
      raw=json.dumps(receipt['row'],sort_keys=True,separators=(',',':'),allow_nan=False).encode();chain=hashlib.sha256(bytes.fromhex(chain)+raw).hexdigest();assert receipt['chain_sha256']==chain
     assert chain==pump.command_gate.retirement_chain
     result['streamed_retirement_proof']=dict(authenticated_old_state_packets=300,durable_retirement_rows=300,bounded_memory_rows=256,first_cached_sequence=44,last_cached_sequence=299,final_chain_sha256=chain,hot_du_calls=0,no_stale_returned_or_applied=True,software_only_not_physical=True)
     # Current same-state source remains subject to the exact original gate.
     now=time.monotonic();n.sent[1]=frame(1,5,now);value=packet(300,n.sent[1]);peer.sendto(json.dumps(value).encode(),pump.address);received=pump.receive()
     accepted=pump.command_gate.accept(received,n.sent,current_native=5,now=time.monotonic());assert accepted['v']==.1 and accepted['delivery']['observation_native_tick']==5
     changed=dict(value,sequence=301,observation_native_tick=6);rejected('tampered_binding_still_refused',lambda:pump.command_gate.accept(changed,n.sent,current_native=5,now=time.monotonic()))
     changed=dict(value,sequence=301);changed['origin']=dict(value['origin'],generated_monotonic=value['origin']['generated_monotonic']+.01);rejected('tampered_origin_still_refused',lambda:pump.command_gate.accept(changed,n.sent,current_native=5,now=time.monotonic()))
     # Valid source with201ms observation is retired; acceptance does not relax.
     past=time.monotonic()-.201;n.sent[2]=frame(2,5,past);expired=packet(301,n.sent[2]);assert pump.command_gate.accept(expired,n.sent,current_native=5,now=time.monotonic())is None and pump.command_gate.retired[-1]['reason']=='EXPIRED_SOURCE'
     sink=pump.command_gate.retirement_sink;prior_count=pump.command_gate.retired_total;prior_chain=pump.command_gate.retirement_chain;prior_previous=pump.command_gate.previous
     def fail_sink(value):raise OSError('SOFTWARE_INJECTED_RETIREMENT_SAVE_FIRST_ERROR')
     pump.command_gate.retirement_sink=fail_sink
     try:pump.command_gate.accept(packet(302,n.sent[0]),n.sent,current_native=5,now=time.monotonic())
     except OSError as exc:assert str(exc)=='SOFTWARE_INJECTED_RETIREMENT_SAVE_FIRST_ERROR'
     else:raise AssertionError('DURABLE_RETIREMENT_SAVE_FAILURE_NOT_PROPAGATED')
     assert pump.command_gate.retired_total==prior_count and pump.command_gate.retirement_chain==prior_chain and pump.command_gate.previous==prior_previous
     pump.command_gate.retirement_sink=sink
     result['sink_failure_proof']=dict(original_first_error_preserved=True,retired_total_not_advanced=True,chain_not_advanced=True,accepted_sequence_not_advanced=True,no_action=True)
   finally:
    if peer is not None:peer.close()
    if pump is not None:pump.close()
    qmodule.base.used=original_used
   storage=sup.budget.storage_preflight(limits);inherited=dict(oldfrozen);inherited.update({str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()})
   assert parentpath.read_bytes()==before and not(O/'ROUND_WINDOW.json').exists()and not(O/'first_event').exists()
   result.update(passed=True,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,negatives_rejected=negatives,entry_gates=prior['entry_gates'],external_writer_hook_qualification=prior['external_writer_hook_qualification'],writer_source_proofs=prior['writer_source_proofs'],source_hashes=inherited,storage_preflight=storage,reused_scope_entry_SHA=contract.sha(FO/'SCOPE_QUALIFICATION.json'),normalized_unchanged_production_files=unchanged,actual_Pump_receive_and_command_gate_software_only_real_sockets=True,original_identity_state_and_source_acceptance_AST_exact=True,retirement_memory_bounded_and_streamed=True,all_external_future_caps_held_bytes=sum(caps.values()),live_child_metadata_not_forged=True,source200ms_and_originalscience_unchanged=True,whole_route_admission=False,live_event_runtime_passed=False,source_remote_recovery_still_required=True)
 except BaseException as exc:
  import traceback
  first=dict(error=repr(exc),traceback=traceback.format_exc());result['first_error']=first
 finally:
  sys.setprofile(previous);sys.meta_path.remove(finder);io.atomic(O/'SCOPE_QUALIFICATION.json',result);io.atomic(O/'ENTRY_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,first_error=first))
  files=result.get('source_hashes')or{str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()};io.atomic(O/'SOURCE_FREEZE.json',dict(files=files,entry_passed=result['passed'],models=0,whole_route_admission=False))
 return 0 if result['passed']else 1
