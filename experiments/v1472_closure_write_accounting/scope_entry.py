"""One new no-model qualification of pre-wire reuse and bounded closure I/O."""
import ast
import fcntl
import gzip
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import time
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;F=R/'experiments/v1467_initializer_byte_grant';FO=R/'runs'/F.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*_):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('WIRE_GRANT_ENTRY_MODELS_FORBIDDEN:'+name)

def qualify(task):
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'ENTRY_ONCE_CLAIM.json').exists()
 (O/'ENTRY_ONCE_CLAIM.json').write_text(json.dumps(dict(unix=time.time(),models=0,scope='WIRE_REUSE_AND_COMPLETE_PREFIX_BYTE_GRANT'))+'\n')
 finder=NoModels();sys.meta_path.insert(0,finder);previous=sys.getprofile()
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_filename.startswith(str(R)+'/')and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py','vehicle_control.py'}:raise AssertionError('WIRE_GRANT_CONSTRUCTOR_STEP_COMPUTE_FORBIDDEN')
 sys.setprofile(forbid);result=dict(passed=False,models=0,physical_native=0,allocator_recomputations=0,actual_replay_native=0,software_only=True);first=None;negatives=[]
 io=exact('v1472_original_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');contract=exact('v1472_current_scope',C/'contract.py')
 def rejected(label,fn):
  try:fn()
  except (AssertionError,RuntimeError,FileExistsError,FileNotFoundError):negatives.append(label);return
  raise AssertionError('WIRE_GRANT_NEGATIVE_ACCEPTED:'+label)
 try:
  import numpy as np
  parentpath=R/'runs/v1382_weekend_campaign/LEDGER.json';before=parentpath.read_bytes();parent=json.loads(before);assert parent['active_round']is None and not parent['models_now_authorized']
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   prior=contract.read(FO/'SCOPE_QUALIFICATION.json');assert prior['passed']and prior['models']==prior['physical_native']==0
   oldfrozen=contract.read(FO/'SOURCE_FREEZE.json')['files'];assert all(contract.sha(R/p)==h for p,h in oldfrozen.items())
   unchanged=[]
   for p in sorted(C.glob('*.py')):
    if p.name in {'scope_entry.py','lifecycle.py','pump.py','wire_grant.py'}:continue
    restored=p.read_text().replace('v1472_closure_write_accounting','v1467_initializer_byte_grant').replace('v1472','v1467')
    assert ast.dump(ast.parse(restored))==ast.dump(ast.parse((F/p.name).read_text())),'UNDECLARED_WIRE_CHANGE:'+p.name;unchanged.append(p.name)
   for name in ['TASKS.json','LIMITS.json','WRITER_CAPS.json']:
    assert json.loads((C/name).read_text().replace('v1472_closure_write_accounting','v1467_initializer_byte_grant').replace('v1472','v1467'))==contract.read(F/name)
   pump_source=(C/'pump.py').read_text();pump_original=(R/'experiments/v1449_route_initializer_binding/pump.py').read_text()
   pump_source=pump_source.replace("wire_grants=exact('v1472_before_wire_grant',Path(__file__).with_name('wire_grant.py'))\n",'').replace("quota=self.owner.quota;wire_grants.before_wire(quota,native_tick=self.owner.native.vehicle.count)","quota=self.owner.quota;quota.retire_grant();quota.prepare_grant(8*1024**2,phase='BEFORE_ACTUAL5_NATIVE_WIRE',valid_for_s=2,external_writers=quota.external_writers)")
   assert ast.dump(ast.parse(pump_source))==ast.dump(ast.parse(pump_original)),'PUMP_CHANGED_BEYOND_BEFORE_WIRE_GRANT'
   life_source=(C/'lifecycle.py').read_text().replace('v1472_closure_write_accounting','v1467_initializer_byte_grant').replace('v1472','v1467')
   life_source=life_source.replace("pump_module=exact('v1467_actual_pump_pre_wire_grant',N/'pump.py')","pump_module=exact('v1421_actual_pump',C/'pump.py')")
   close_line="   attempt('PREPARE_BOUNDED_PREFIX_CLOSE_GRANT',lambda:evidence_quota.prepare_grant(32*1024**2,phase='COMPLETE_ZERO_TAIL_OR_CLOSURE',valid_for_s=300,external_writers=evidence_quota.external_writers))\n"
   assert close_line in life_source;life_source=life_source.replace(close_line,'')
   assert ast.dump(ast.parse(life_source))==ast.dump(ast.parse((F/'lifecycle.py').read_text())),'LIFECYCLE_CHANGED_BEYOND_DECLARED_PUMP_AND_CLOSURE_GRANT'
   life=exact('v1472_exact_scope_lifecycle',C/'lifecycle.py');sup=exact('v1472_once_supervisor',C/'supervisor.py')
   rejected('native_missing_newscope_admission',lambda:life.run(task,{},{}));rejected('once_missing_newscope_admission',lambda:sup.launch('first_event'))
   limits=contract.read(C/'LIMITS.json');sup.budget.limits_check(limits);qmodule=exact('v1472_exact_byte_quota',C/'quota.py');boundary=exact('v1472_original_boundary',C/'bounded_io.py');capture=exact('v1472_qualified_bounded_gzip',R/'experiments/v1454_bounded_gzip_closure/capture_budget.py')
   folder=O/'software_wire';folder.mkdir();quota=qmodule.EvidenceQuota(folder,limits);quota.bind_external_names([]);quota.external_writers=[];quota.write_enforcement_active=True
   caps=contract.read(C/'WRITER_CAPS.json');assert sum(caps.values())==56*1024**2
   for role,cap in caps.items():quota.hold('future_external:'+role,cap)
   original_used=qmodule.base.used;calls=[];events=[];emissions=[]
   def counted(path):calls.append(str(path));events.append('du');return original_used(path)
   def charge(path,n):emissions.append(dict(path=str(path.relative_to(folder)),bytes=n));return quota.charge_write(path,n)
   qmodule.base.used=counted;peer=None;pump=None
   try:
    with boundary.OutputBoundary(folder,charge):
     quota.prepare_grant(16*1024**2,phase='CANONICAL_INITIALIZER_PREPARATION',valid_for_s=180,external_writers=[])
     assert len(calls)==2
     vehicle=SimpleNamespace(count=0);owner=SimpleNamespace(quota=quota,output=folder,native=SimpleNamespace(vehicle=vehicle,run_id='V1469_SOFTWARE_ONLY'))
     def envelope():events.append('sample_software_envelope');return dict(software_only=True,native_tick=vehicle.count,sequence=len(events))
     owner.envelope=envelope;owner.atomic=io.atomic
     def append(value):
      with(folder/'SOFTWARE_DISPATCH.jsonl').open('a')as stream:stream.write(json.dumps(value,allow_nan=False)+'\n')
     pump=life.pump_module.Pump(owner,check_budget=lambda *_:None,append=append,model_peer=None)
     peer=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);peer.bind(pump.peer);peer.settimeout(1)
     seq=quota.grant['sequence'];credit=quota.grant['remaining_bytes'];expires=quota.grant['expires_monotonic'];events.clear();before_calls=len(calls)
     pump.publish();wire=json.loads(peer.recv(65536));assert wire['software_only']and wire['native_tick']==0
     assert events==['sample_software_envelope']and len(calls)==before_calls and quota.grant['sequence']==seq and quota.grant['expires_monotonic']==expires
     assert quota.grant['remaining_bytes']<credit
     reuse_at_t0=dict(full_du_calls=0,sampled_after_grant_check=True,original_expiration_not_renewed=True)
     # Existing valid credits cannot be silently replenished to rescue a wire.
     saved=dict(quota.grant);quota.grant['remaining_bytes']=65535;events.clear();before_calls=len(calls)
     rejected('insufficient_existing_grant_no_refresh',pump.publish);assert not events and len(calls)==before_calls and quota.grant['sequence']==seq
     quota.grant=dict(saved);quota.grant['owner_pid']=-1;rejected('foreign_grant_owner',pump.publish)
     quota.grant=dict(saved);quota.grant['boot_id']='SOFTWARE_FOREIGN_BOOT';rejected('foreign_grant_boot',pump.publish)
     quota.grant=dict(saved);quota.grant['expires_monotonic']=time.monotonic()-1;events.clear();before_calls=len(calls)
     pump.publish();peer.recv(65536);assert events==['du','du','sample_software_envelope']and len(calls)==before_calls+2
     assert quota.grant['phase']=='BEFORE_ACTUAL5_NATIVE_WIRE'and quota.grant['sequence']==seq+1
     assert abs(quota.grant['expires_monotonic']-quota.grant['prepared_monotonic']-2)<1e-9
     events.clear();before_calls=len(calls);pump.publish();peer.recv(65536);assert events==['sample_software_envelope']and len(calls)==before_calls
     quota.retire_grant();quota.prepare_grant(16*1024**2,phase='CANONICAL_INITIALIZER_PREPARATION',valid_for_s=180,external_writers=[])
     vehicle.count=1;events.clear();before_calls=len(calls);pump.publish();peer.recv(65536)
     assert events==['du','du','sample_software_envelope']and len(calls)==before_calls+2 and quota.grant['phase']=='BEFORE_ACTUAL5_NATIVE_WIRE'
     rejected('negative_native_tick',lambda:life.pump_module.wire_grants.before_wire(quota,native_tick=-1))
     rejected('noninteger_native_tick',lambda:life.pump_module.wire_grants.before_wire(quota,native_tick=0.0))
     quota.retire_grant();quota.prepare_grant(4096,phase='STOPPED_EVENT_PREPARATION',valid_for_s=2,external_writers=[])
     events.clear();pump.publish();peer.recv(65536);assert events==['du','du','sample_software_envelope']and quota.grant['phase']=='BEFORE_ACTUAL5_NATIVE_WIRE'
     quota.retire_grant();closure=quota.prepare_grant(32*1024**2,phase='COMPLETE_ZERO_TAIL_OR_CLOSURE',valid_for_s=300,external_writers=[])
     before_calls=len(calls);before_emissions=len(emissions);remaining=quota.grant['remaining_bytes']
     # Fresh software values, not old physics arrays or replayed controls.
     arrays=dict(software_only=np.asarray(True),counter=np.arange(17,dtype=np.int64),unicode_utf8=np.frombuffer('关闭来源资格'.encode(),dtype=np.uint8).copy())
     quota.save_npz(folder/'SOFTWARE_PREFIX.npz',arrays,np)
     with np.load(folder/'SOFTWARE_PREFIX.npz',allow_pickle=False)as stored:
      assert set(stored.files)==set(arrays)and all(np.array_equal(stored[k],v)for k,v in arrays.items())
     payloads={'CONTACTS.json.gz':[{'software_only':True,'tag':'原受限压缩'}], 'SENSORS.json.gz':[{'software_only':True,'sensor':'非测量'}]}
     with capture.original_finish_compressed_paths(folder):
      for name,value in payloads.items():
       with gzip.open(folder/name,'xt')as stream:json.dump(value,stream,ensure_ascii=False)
     for name,value in payloads.items():
      with gzip.open(folder/name,'rt')as stream:assert json.load(stream)==value
     emitted=sum(row['bytes']for row in emissions[before_emissions:]);expected=sum(8192+(folder/name).stat().st_size for name in ['SOFTWARE_PREFIX.npz',*payloads])
     by_name={name:sum(row['bytes']for row in emissions[before_emissions:]if row['path']==name)for name in ['SOFTWARE_PREFIX.npz',*payloads]}
     result['closure_write_proof']=dict(charged_bytes=emitted,final_file_bytes_plus_open=expected,quota_debit=remaining-quota.grant['remaining_bytes'],hot_du_calls=len(calls)-before_calls,bytes_by_name=by_name,write_emissions=emissions[before_emissions:])
     assert by_name['SOFTWARE_PREFIX.npz']>=8192+(folder/'SOFTWARE_PREFIX.npz').stat().st_size,'NPZ_REWRITES_MUST_NOT_RETURN_CREDIT'
     assert all(by_name[name]==8192+(folder/name).stat().st_size for name in payloads),'GZIP_EXACT_EMITTED_BYTES'
     assert quota.grant['remaining_bytes']==remaining-emitted and len(calls)==before_calls,'CLOSURE_HOT_WRITE_ACCOUNTING_OR_DU'
     assert closure['maximum_held_bytes']==sum(caps.values())and abs(closure['expires_monotonic']-closure['prepared_monotonic']-300)<1e-9
     quota.grant['expires_monotonic']=time.monotonic()-1;rejected('expired_closure_before_emission',lambda:(folder/'EXPIRED.txt').write_text('x'));assert not(folder/'EXPIRED.txt').exists()
     quota.retire_grant();rejected('wire_ttl_not_expanded',lambda:quota.prepare_grant(4096,phase='BEFORE_ACTUAL5_NATIVE_WIRE',valid_for_s=2.001,external_writers=[]))
     rejected('closure_ttl_not_expanded',lambda:quota.prepare_grant(4096,phase='COMPLETE_ZERO_TAIL_OR_CLOSURE',valid_for_s=301,external_writers=[]))
   finally:
    if peer is not None:peer.close()
    if pump is not None:pump.close()
    qmodule.base.used=original_used
   storage=sup.budget.storage_preflight(limits)
   inherited=dict(oldfrozen);inherited.update({str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()})
   assert parentpath.read_bytes()==before and not(O/'ROUND_WINDOW.json').exists()and not(O/'first_event').exists()
   result.update(passed=True,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,negatives_rejected=negatives,entry_gates=prior['entry_gates'],external_writer_hook_qualification=prior['external_writer_hook_qualification'],writer_source_proofs=prior['writer_source_proofs'],source_hashes=inherited,storage_preflight=storage,reused_scope_entry_SHA=contract.sha(FO/'SCOPE_QUALIFICATION.json'),normalized_unchanged_production_files=unchanged,exact_original_pump_only_prewire_change=True,exact_lifecycle_only_new_pump_and_close_grant=True,all_external_future_caps_held_bytes=sum(caps.values()),live_child_metadata_not_forged=True,production_pump_real_Unix_datagram_software_dispatch=True,reuse_at_t0=reuse_at_t0,expiry_and_nonzero_native_prepare_before_sampling=True,closure_full_du_calls_during_writes=0,closure_exact_charged_bytes=emitted,closure_NPZ_and_qualified_gzip_lossless=True,source200ms_and_originalscience_unchanged=True,old_runtime_failure_retained=True,whole_route_admission=False,live_event_runtime_passed=False,source_remote_recovery_still_required=True)
 except BaseException as exc:
  import traceback
  first=dict(error=repr(exc),traceback=traceback.format_exc());result['first_error']=first
 finally:
  sys.setprofile(previous);sys.meta_path.remove(finder);io.atomic(O/'SCOPE_QUALIFICATION.json',result);io.atomic(O/'ENTRY_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,first_error=first))
  files=result.get('source_hashes')or{str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()};io.atomic(O/'SOURCE_FREEZE.json',dict(files=files,entry_passed=result['passed'],models=0,whole_route_admission=False))
 return 0 if result['passed']else 1
