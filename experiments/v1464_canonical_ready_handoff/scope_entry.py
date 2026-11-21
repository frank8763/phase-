"""New canonical-ready, failfast and cooperative source qualification only."""
import ast
import copy
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;F=R/'experiments/v1462_explicit_ros_phase';FO=R/'runs'/F.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*_):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('READY_ENTRY_MODELS_FORBIDDEN:'+name)

def qualify(task):
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'ENTRY_ONCE_CLAIM.json').exists()
 (O/'ENTRY_ONCE_CLAIM.json').write_text(json.dumps(dict(unix=time.time(),models=0,scope='NEW_CANONICAL_READY_FAILFAST_AND_COOPERATIVE_STOP_ONLY'))+'\n')
 finder=NoModels();sys.meta_path.insert(0,finder);previous=sys.getprofile()
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_filename.startswith(str(R)+'/')and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py','vehicle_control.py'}:raise AssertionError('READY_ENTRY_MODEL_STEP_COMPUTE_FORBIDDEN')
 sys.setprofile(forbid);result=dict(passed=False,models=0,physical_native=0,allocator_recomputations=0,actual_replay_native=0,software_only=True);first=None;negatives=[]
 io=exact('v1464_original_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');contract=exact('v1464_ready_scope',C/'contract.py')
 def rejected(label,fn):
  try:fn()
  except (AssertionError,RuntimeError,FileExistsError,FileNotFoundError):negatives.append(label);return
  raise AssertionError('CANONICAL_READY_NEGATIVE_ACCEPTED:'+label)
 try:
  import numpy as np
  parentpath=R/'runs/v1382_weekend_campaign/LEDGER.json';before=parentpath.read_bytes();parent=json.loads(before);assert parent['active_round']is None and not parent['models_now_authorized']
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   prior=contract.read(FO/'SCOPE_QUALIFICATION.json');assert prior['passed']and prior['models']==prior['physical_native']==0
   oldfrozen=contract.read(FO/'SOURCE_FREEZE.json')['files'];assert all(contract.sha(R/p)==h for p,h in oldfrozen.items())
   unchanged=[]
   for p in sorted(C.glob('*.py')):
    if p.name in {'scope_entry.py','startup.py','lifecycle.py','supervisor.py','budget.py'}:continue
    restored=p.read_text().replace('v1464_canonical_ready_handoff','v1462_explicit_ros_phase').replace('v1464','v1462')
    assert ast.dump(ast.parse(restored))==ast.dump(ast.parse((F/p.name).read_text())),'UNDECLARED_READY_SOURCE_CHANGE:'+p.name;unchanged.append(p.name)
   startup=exact('v1464_exact_ready_helpers',C/'startup.py');life=exact('v1464_exact_native_lifecycle',C/'lifecycle.py');sup=exact('v1464_exact_scope_supervisor',C/'supervisor.py')
   rejected('native_missing_ready_scope_admission',lambda:life.run(task,{},{}));rejected('once_missing_ready_scope_admission',lambda:sup.launch('first_event'))
   assert life.O==sup.O==O
   # This folder is explicitly synthetic software I/O, never model/scan input.
   folder=O/'software_ready';folder.mkdir();(folder/'physics').mkdir()
   limits=contract.read(C/'LIMITS.json');sup.budget.limits_check(limits)
   quota_module=exact('v1464_original_pre_wire_quota',life.C/'quota.py');quota=quota_module.EvidenceQuota(folder,limits);quota.bind_external_names([]);quota.external_writers=[];quota.write_enforcement_active=True
   boundary=exact('v1464_frozen_output_boundary',C/'bounded_io.py')
   def put(p,v):return quota.atomic(p,v,io.atomic)
   identity='a'*64;run='SOFTWARE_READY_ONLY'
   initial=dict(time=np.asarray(0.),qpos=np.zeros(20),qvel=np.zeros(19),ctrl=np.zeros(11),mocap_pos=np.zeros((1,3)),mocap_quat=np.asarray([[1.,0.,0.,0.]]))
   packet=dict(native_tick=0,sim_time=0.,body=[-4.,-2.,0.,0.,0.],controller_memory=dict(last_ctrl=[0.,0.,0.,0.],integral=0.))
   sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);sock.bind(str((folder/'native.sock').relative_to(R)))
   try:
    with boundary.OutputBoundary(folder,quota.charge_write):
     quota.prepare_grant(2*1024**2,phase='COMPLETE_ZERO_TAIL_OR_CLOSURE',valid_for_s=60,external_writers=[])
     put(folder/'INITIAL_PACKET.json',packet);quota.save_npz(folder/'INITIAL_FULL_STATE.npz',initial,np)
     (folder/'physics/scene_model.mjb').write_bytes(b'SOFTWARE_NOT_MUJOCO_MODEL')
     put(folder/'physics/SETUP.json',dict(model_sha256=startup.sha(folder/'physics/scene_model.mjb')))
     receipt=dict(run_id=run,source_identity=identity,native_tick=0,sim_time=0.,canonical_factory_returned=True,initial_packet_sha256=startup.sha(folder/'INITIAL_PACKET.json'),initial_fullstate_sha256=startup.sha(folder/'INITIAL_FULL_STATE.npz'),model_sha256=startup.sha(folder/'physics/scene_model.mjb'),source_counts=dict(actual_native=0,private_native=0),software_fixture=True)
     put(folder/'CANONICAL_T0_READY.json',receipt)
     rejected('software_receipt_cannot_start_actual_ROS',lambda:startup.verify_ready(folder,run_id=run,source_identity=identity))
     assert startup.verify_ready(folder,run_id=run,source_identity=identity,allow_software=True)==receipt
     for key,value,label in [('run_id','foreign','wrong_ready_run'),('source_identity','b'*64,'wrong_ready_source'),('native_tick',1,'ready_native_nonzero'),('sim_time',.01,'ready_sim_time_nonzero'),('model_sha256','c'*64,'ready_model_changed'),('initial_packet_sha256','d'*64,'ready_packet_changed'),('initial_fullstate_sha256','e'*64,'ready_state_changed')]:
      bad=dict(receipt,**{key:value});put(folder/'CANONICAL_T0_READY.json',bad);rejected(label,lambda:startup.verify_ready(folder,run_id=run,source_identity=identity,allow_software=True))
     put(folder/'CANONICAL_T0_READY.json',receipt)
     # Native emit source is exercised with clearly software state; emitted
     # object stays in software_ready and is immediately relabeled true before
     # any independent verify; no task admission reads this folder.
     vehicle=SimpleNamespace(count=0,d=SimpleNamespace(time=0.),rows=[],commands=[],audit=SimpleNamespace(native_count=0),adapter=SimpleNamespace(last=np.zeros(4),integral=0.),body=lambda:tuple(packet['body']))
     canonical=SimpleNamespace(native=SimpleNamespace(applied=0))
     emitted=startup.emit_ready(vehicle,canonical,folder,run_id=run,source_identity=identity,atomic=put)
     emitted['software_fixture']=True;put(folder/'CANONICAL_T0_READY.json',emitted);assert emitted['canonical_factory_returned']
     vehicle.count=1;rejected('emit_ready_actual_native_nonzero',lambda:startup.emit_ready(vehicle,canonical,folder,run_id=run,source_identity=identity,atomic=put));vehicle.count=0
     # ROS classification uses actual saved JSON schema but no ROS nodes.
     put(folder/'ROS_RESULT.json',dict(closed=True,passed=False,error='SOFTWARE_T0_TIMEOUT',controller_server_exited=True,evidence_write_errors=[]))
     assert startup.unexpected_ROS_failure(folder,run)['first_saved_ROS_error']=='SOFTWARE_T0_TIMEOUT'
     put(folder/'PEER_STOP_REQUEST.json',dict(run_id=run));put(folder/'ROS_RESULT.json',dict(closed=True,passed=False,functional_stop='COOPERATIVE_PEER_CLOSED',controller_server_exited=True,evidence_write_errors=[]));assert startup.unexpected_ROS_failure(folder,run)is None
     put(folder/'PEER_STOP_REQUEST.json',dict(run_id='foreign'));assert startup.unexpected_ROS_failure(folder,run)is not None
     put(folder/'ROS_RESULT.json',dict(closed=True,passed=True,error='SOFTWARE_CORRUPT_SUCCESS',controller_server_exited=True,evidence_write_errors=[]));assert startup.unexpected_ROS_failure(folder,run)is not None
     put(folder/'ROS_RESULT.json',dict(closed=True,passed=True,controller_server_exited=True,evidence_write_errors=[]));assert startup.unexpected_ROS_failure(folder,run)is None
     stop=startup.request_native_stop(folder,run_id=run,source_identity=identity,error='SOFTWARE_PRIMARY',atomic=put)
     rejected('valid_stop_refuses_new_action',lambda:startup.check_native_stop(folder,run_id=run,source_identity=identity))
     rejected('foreign_native_stop_run',lambda:startup.check_native_stop(folder,run_id='foreign',source_identity=identity))
     rejected('foreign_native_stop_source',lambda:startup.check_native_stop(folder,run_id=run,source_identity='z'*64))
     assert startup.read(folder/'NATIVE_STOP_REQUEST.json')==stop
     sock.close();(folder/'native.sock').unlink();(folder/'native.sock').write_text('not socket')
     rejected('native_socket_must_be_socket',lambda:startup.verify_ready(folder,run_id=run,source_identity=identity,allow_software=True))
    quota.retire_grant();quota.write_enforcement_active=False
   finally:sock.close()
   # Shared clocks are measured without sleeping for long or constructing a
   # model; fake clock is confined to helper globals and restored immediately.
   now=time.time();mono=time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+5400,hard_stop_monotonic=mono+5400,boot_id=parent['boot_id'])
   end=startup.initializer_deadlines(window,dict(absolute_deadline_unix=now+4140,hard_stop_monotonic=mono+4140),cap_s=180)
   assert 179<end['absolute_deadline_unix']-now<=181 and 179<end['hard_stop_monotonic']-mono<=181
   rejected('init_cap_cannot_expand',lambda:startup.initializer_deadlines(window,end,cap_s=181))
   near=startup.initializer_deadlines(dict(window,absolute_deadline_unix=now+50,hard_stop_monotonic=mono+50),dict(absolute_deadline_unix=now+4140,hard_stop_monotonic=mono+4140),cap_s=180);assert near['absolute_deadline_unix']<=now+45
   actual_time=startup.time
   fake=SimpleNamespace(time=lambda:1000.,monotonic=lambda:1000.,sleep=lambda _:None)
   startup.time=fake
   try:
    fakejob=SimpleNamespace(poll=lambda:None)
    # wait start and next check receive different software clocks, proving both
    # subcap refusal and no mutation of original root window.
    calls=[1000.,1201.]
    fake.monotonic=lambda:calls.pop(0)if calls else 1201.
    rejected('cooperative_close200_no_root_reset',lambda:startup.wait_native_close(fakejob,window,maximum_s=200,check=lambda:None))
    calls[:]=[1000.,1181.];fake.monotonic=lambda:calls.pop(0)if calls else 1181.
    rejected('ready180_no_root_reset',lambda:startup.wait_ready(folder,task,identity,fakejob,window,maximum_s=180,check=lambda:None))
    rejected('cooperative_close_cap_cannot_expand',lambda:startup.wait_native_close(fakejob,window,maximum_s=201,check=lambda:None))
   finally:startup.time=actual_time
   # Exact actual bounded child cooperative request, no MjModel or physics.
   child_out=O/'cooperative_child';child_out.mkdir();stopfile=child_out/'NATIVE_STOP_REQUEST.json';resultfile=child_out/'SOFTWARE_CLOSED.json'
   program="import json,time;from pathlib import Path;p=Path(__import__('sys').argv[1]);q=Path(__import__('sys').argv[2]);end=time.monotonic()+5\nwhile not p.exists() and time.monotonic()<end:time.sleep(.01)\nv=json.loads(p.read_text());q.write_text(json.dumps(dict(closed=True,software_only=True,actual_native=0,first_error=v['reason'])))"
   job=subprocess.Popen(['taskset','-c','5','/usr/bin/python3.12','-B','-c',program,str(stopfile),str(resultfile)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
   try:
    startup.request_native_stop(child_out,run_id=run,source_identity=identity,error='SOFTWARE_FIRST_ERROR',atomic=io.atomic)
    startup.wait_native_close(job,window,maximum_s=200,check=lambda:contract.clocks(window,parent,reserve_s=5));job.communicate(timeout=2)
    assert job.returncode==0 and json.loads(resultfile.read_text())==dict(closed=True,software_only=True,actual_native=0,first_error='SOFTWARE_FIRST_ERROR')
   finally:
    if job.poll()is None:sup.terminate(job)
    if job.stdout is not None:job.stdout.close()
   # Production attachment identity and step-before-stop ordering is explicit.
   assert 'startup.emit_ready' in(C/'lifecycle.py').read_text()and 'startup.wait_ready' in(C/'supervisor.py').read_text()
   life_tree=ast.parse((C/'lifecycle.py').read_text());assert "creating=False;result['canonical_vehicle_initializations']=1"in(C/'lifecycle.py').read_text()
   assert 'startup.unexpected_ROS_failure'in(C/'supervisor.py').read_text()
   storage=sup.budget.storage_preflight(limits)
   inherited=dict(oldfrozen);inherited.update({str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()})
   assert parentpath.read_bytes()==before and not(O/'ROUND_WINDOW.json').exists()and not(O/'first_event').exists()
   result.update(passed=True,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,negatives_rejected=negatives,entry_gates=prior['entry_gates'],external_writer_hook_qualification=prior['external_writer_hook_qualification'],writer_source_proofs=prior['writer_source_proofs'],source_hashes=inherited,storage_preflight=storage,reused_scope_entry_SHA=contract.sha(FO/'SCOPE_QUALIFICATION.json'),normalized_unchanged_production_files=unchanged,ready_receipts_explicitly_software_not_factory=True,real_unix_socket_readiness_checked=True,init180_same_root5400=True,original_ROS45s_wait_unchanged=True,saved_ROS_failure_and_expected_close_classified=True,real_software_child_cooperative_stop_saved_without_physics=True,old_native_RESULT_gap_preserved=True,whole_route_admission=False,live_event_runtime_passed=False,source_remote_recovery_still_required=True)
 except BaseException as exc:
  import traceback
  first=dict(error=repr(exc),traceback=traceback.format_exc());result['first_error']=first
 finally:
  sys.setprofile(previous);sys.meta_path.remove(finder);io.atomic(O/'SCOPE_QUALIFICATION.json',result);io.atomic(O/'ENTRY_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,first_error=first))
  files=result.get('source_hashes')or{str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()};io.atomic(O/'SOURCE_FREEZE.json',dict(files=files,entry_passed=result['passed'],models=0,whole_route_admission=False))
 return 0 if result['passed']else 1
