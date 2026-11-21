"""Real bounded I/O and cross-writer pending-index admission; zero models."""
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
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy','coupled_model','prediction'}:raise AssertionError('BYTE_QUOTA_NO_MODELS:'+name)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'QUALIFICATION.json').exists();os.chdir(R);sys.meta_path.insert(0,NoModel());started=time.monotonic()
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py'}:raise AssertionError('BYTE_QUOTA_MODEL_CONSTRUCTOR_STEP_COMPUTE_FORBIDDEN')
 sys.setprofile(forbid);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==5
 import numpy as np
 quota_source=exact('v1431_real_quota',C/'quota.py');store_source=exact('v1431_real_bounded_stream',C/'branch_store.py');sink_source=exact('v1431_real_bounded_receipt_sink',C/'evidence_sink.py');capture_source=exact('v1431_real_capture_hold',C/'capture_budget.py');lifecycle=exact('v1431_actual_latest_lifecycle',C/'lifecycle.py');io=exact('v1431_original_atomic_io',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');limits=json.loads((C/'LIMITS.json').read_text())
 assert Path(lifecycle.owner_module.transaction_module.CuspTransaction.run.__code__.co_filename).resolve()==C/'transaction.py'
 assert Path(lifecycle.owner_module.sink_module.EvidenceSink.reserve_complete.__code__.co_filename).resolve()==C/'evidence_sink.py'
 assert Path(lifecycle.peer_module.EventPeer.command.__code__.co_filename).resolve()==R/'experiments/v1426_peer_graceful_closure/model_peer.py'
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  out=O/'io_boundary';out.mkdir();quota=quota_source.EvidenceQuota(out,limits)
  def atomic(path,value):return quota.atomic(path,value,io.atomic)
  identity='1'*64;states=np.arange(201*8,dtype=np.float64).reshape(201,8)*1e-6;ctrl=np.arange(200*4,dtype=np.float64).reshape(200,4)*1e-7
  proof=dict(before_native=0,complete_native=200,input_sha256=identity,source_packet_sha256='2'*64,passed=False,software_I_O_arrays_not_model=True)
  store=store_source.BranchStore(out/'stream',input_sha256=identity,np=np,atomic=atomic,maximum_branches=2,quota=quota);store.append(proof,states,ctrl);assert store.hold_key in quota.holds
  held_before=quota._held();assert held_before>0
  # Consume capacity using a reservation only; no filler or sparse file is
  # created, no quota is changed and all du measurements remain real.
  room=limits['maximum_task_evidence_bytes']-quota_source.used(out)-quota_source.ERROR_RESERVE-quota._held()-8192
  quota.hold('unrelated-writer-pending',max(0,room//4096*4096))
  negatives=[]
  def reject(label,fn):
   assert time.monotonic()-started<60
   try:fn()
   except (AssertionError,ValueError,KeyError):negatives.append(label);return
   raise AssertionError('BYTE_QUOTA_NEGATIVE_ACCEPTED:'+label)
  reject('ordinary_atomic_cannot_consume_pending_index',lambda:atomic(out/'FORBIDDEN.json',dict(text='x'*65536)))
  assert not(out/'FORBIDDEN.json').exists()and not(out/'FORBIDDEN.json.tmp').exists()
  reject('oversized_append_refuses_before_stream_write',lambda:store.append(dict(proof,before_native=1),states,ctrl))
  assert len(store.rows)==1
  quota.release('unrelated-writer-pending');store.close();assert not quota.holds
  index=json.loads((out/'stream/INDEX.json').read_text());reader=store_source.original.BranchReader(out/'stream',index,np);ss,uu=reader.read(index['branches'][0]);reader.finish();assert np.array_equal(states,ss)and np.array_equal(ctrl,uu)
  reject('external_atomic_path',lambda:atomic(O/'ESCAPE.json',dict(wrong=True)))
  reject('negative_pending_bytes',lambda:quota.admit(-1,'BAD_PENDING'))
  # Exercise the actual CurrentReserve storage callback/sink methods, while
  # explicitly marking these arrays/receipts as software and not certificates.
  sink=sink_source.EvidenceSink(out/'actual',identity=identity,np=np,atomic=atomic,maximum_branches=1,quota=quota)
  reserve=dict(proof,passed=True,software_placeholder_only_not_certificate=True)
  sink.reserve_complete(reserve,states,ctrl)
  row=dict(before_native=0,source_packet_sha256='2'*64,applied=False,software_placeholder_only_not_actual=True)
  sink.before(row,reserve,states,ctrl);sink.after(dict(row,applied=True));sink.reserve_partial(dict(software_partial_only=True),states[:37],ctrl[:36]);sink.close(dict(software_I_O_only=True,actual_native=0))
  closed=json.loads((out/'actual/EVIDENCE_INDEX.json').read_text());assert closed['closed']and closed['complete_reserved_branches']==1 and closed['before_native_rows']==closed['after_native_rows']==1 and closed['incomplete_receipt_native']is None
  with np.load(out/'actual/PARTIAL_RESERVE_000001.npz',allow_pickle=False)as z:assert np.array_equal(z['states'],states[:37])and np.array_equal(z['ctrl'],ctrl[:36])
  quota.save_npz(out/'INITIAL_FULL_STATE_SOFTWARE.npz',dict(qpos=states[:1],ctrl=ctrl[:1]),np)
  # Pure fake vehicle container, never a model or physical factory. Test that
  # CaptureBudget admits and retains exact new arrays/contact/command bytes.
  from types import SimpleNamespace
  vehicle=SimpleNamespace(rows=[dict(time=.01,qpos=np.zeros(11),qvel=np.zeros(10),ctrl=np.zeros(4),mocap_pos=np.zeros((0,3)),mocap_quat=np.zeros((0,4)))],contacts=[[],[]],commands=[[1.,0.,0.,0.,0.,False]],sensor_rows=[dict(native_tick=0,ranges=[3.]*32)])
  capture=capture_source.CaptureBudget(quota);pending=capture.update(vehicle,requested_native=1);assert pending>=262144 and capture.key in quota.holds
  before=dict(raw=capture.raw,encoded=capture.encoded);capture.update(vehicle);assert before==dict(raw=capture.raw,encoded=capture.encoded)
  vehicle.finish=lambda:dict(software_callback_only=True,physical_native=0);assert capture.finish(vehicle)['software_callback_only']and not quota.holds
  quota.error_atomic(out/'EXPECTED_SMALL_FIRST_ERROR.json',dict(first_error='SOFTWARE_QUOTA_REFUSAL',models=0),io.atomic)
  proof=dict(passed=True,models=0,analytical_integrations=0,allocator_recomputations=0,physical_native=0,actual_replay_native=0,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,real_du_inode_measurements=True,no_filler_files_or_quota_changes=True,pending_index_cross_writer_hold_tested=True,bitwise_complete201state200ctrl_stream_roundtrip=True,complete_and_partial_current_reserve_sink_real_I_O=True,root_atomic_npz_and_capture_hold_exercised_with_software=True,negative_cases=negatives,actual_model_or_vehicle_or_lifecycle_unexecuted=True,initializer_and_ROS_child_byte_paths_unqualified=True,complete_route_admission_absent=True,physical_admission=False,wall_s=time.monotonic()-started,all_runs_allocated_bytes=quota_source.used(R/'runs'),task_I_O_allocated_bytes=quota_source.used(out),source_hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.iterdir()if p.is_file()})
  io.atomic(O/'QUALIFICATION.json',proof);print(json.dumps(proof))
if __name__=='__main__':main()
