"""Real file/log interception and no-du hot grants; no models or sensors."""
import ast
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy','coupled_model','prediction'}:raise AssertionError('GRANT_I_O_NO_MODEL:'+name)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'QUALIFICATION.json').exists();os.chdir(R);sys.meta_path.insert(0,NoModel());started=time.monotonic()
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py'}:raise AssertionError('GRANT_I_O_MODEL_CONSTRUCTOR_STEP_COMPUTE')
 sys.setprofile(forbid);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==5
 boundary=exact('v1432_real_output_boundary',C/'bounded_io.py');writers=exact('v1432_real_child_counter',C/'writer_budget.py');source=exact('v1432_real_pre_wire_quota',C/'quota.py');lifecycle=exact('v1432_real_native_lifecycle',C/'lifecycle.py');io=exact('v1432_original_atomic_json',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');limits=json.loads((C/'LIMITS.json').read_text())
 assert Path(lifecycle.owner_module.transaction_module.CuspTransaction.run.__code__.co_filename).resolve()==C/'transaction.py'
 assert Path(lifecycle.pump_module.Pump.publish.__code__.co_filename).resolve()==C/'pump.py'
 negatives=[]
 def reject(label,fn):
  assert time.monotonic()-started<60
  try:fn()
  except (AssertionError,ValueError,KeyError,OSError):negatives.append(label);return
  raise AssertionError('GRANT_BOUNDARY_NEGATIVE_ACCEPTED:'+label)
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  out=O/'real_I_O';out.mkdir();writer=writers.WriterBudget(out,role='ACTUAL_ROS',maximum_bytes=1024**2,source_identity='a'*64)
  with boundary.OutputBoundary(out,writer.reserve):
   (out/'child_native_text.json').write_text(json.dumps(dict(software_only=True,models=0)))
   with(out/'child.console').open('x')as log:
    job=subprocess.Popen([sys.executable,'-B','-c',"print('software subprocess log, zero models')"],stdout=log,stderr=subprocess.STDOUT);assert job.wait(timeout=10)==0
   reject('write_escape_before_open',lambda:(O/'FORBIDDEN_ESCAPE').write_text('no'))
   with(out/'raw_descriptor_forbidden.txt').open('x')as stream:reject('unknown_native_descriptor',stream.fileno)
   reject('child_byte_cap_exhaustion',lambda:writer.reserve(out/'NO_OVERSIZE',2*1024**2))
  assert 'software subprocess log'in(out/'child.console').read_text()
  reject('foreign_child_counter_identity',lambda:writers.WriterBudget(out,role='ACTUAL_ROS',maximum_bytes=1024**2,source_identity='b'*64))
  native=O/'native_grant';native.mkdir();quota=source.EvidenceQuota(native,limits);quota.bind_external_names([]);quota.write_enforcement_active=True
  hot=[False];walks=[]
  def no_hot_du(event,args):
   if event=='subprocess.Popen':
    command=args[1]
    if any(str(x)=='du'for x in command):
     walks.append(dict(hot=hot[0],monotonic=time.monotonic()));assert not hot[0],'FULL_TREE_WALK_ON_FRESH_COMMAND_PATH'
  sys.addaudithook(no_hot_du)
  with boundary.OutputBoundary(native,quota.charge_write):
   grant=quota.prepare_grant(8*1024**2,phase='BEFORE_ACTUAL5_NATIVE_WIRE',valid_for_s=2,external_writers=[])
   software_wire_generated=time.monotonic();assert software_wire_generated>=grant['prepared_monotonic'];hot[0]=True
   start=time.monotonic()
   quota.atomic(native/'complete_record.json',dict(software_current_source_only=True),io.atomic);first=quota.grant['remaining_bytes']
   quota.atomic(native/'complete_record.json',dict(software_current_source_only=True),io.atomic);assert quota.grant['remaining_bytes']<first
   quota.hold('future-complete-index',65536);remaining=quota.grant['remaining_bytes']
   with quota.spend('future-complete-index'):quota.atomic(native/'complete_index.json',dict(closed=True,software_only=True),io.atomic)
   quota.release('future-complete-index');assert quota.grant['remaining_bytes']<=remaining
   hot_wall=time.monotonic()-start
   reject('grant_exhausted_before_write',lambda:quota.admit(16*1024**2,'EXCESS_GRANT'))
   saved=quota.grant['expires_monotonic'];quota.grant['expires_monotonic']=time.monotonic()-1;reject('grant_expired',lambda:quota.admit(1,'EXPIRED'));quota.grant['expires_monotonic']=saved
   saved=quota.grant['boot_id'];quota.grant['boot_id']='wrong';reject('grant_foreign_boot',lambda:quota.admit(1,'BAD_BOOT'));quota.grant['boot_id']=saved
   hot[0]=False;quota.retire_grant();quota.bind_external_names(['ACTUAL_ROS']);reject('missing_external_writer_reservation',lambda:quota.prepare_grant(1024,phase='BEFORE_ACTUAL5_NATIVE_WIRE',valid_for_s=2,external_writers=[]))
  assert walks and not any(x['hot']for x in walks)
  proof=dict(passed=True,models=0,physical_native=0,analytical_integrations=0,allocator_recomputations=0,actual_replay_native=0,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,real_text_and_subprocess_pipe_writes_budgeted=True,full_tree_scan_prepared_before_software_wire=True,actual_sensor_messages=0,hot_path_full_tree_walks=0,hot_two_atomic_and_index_hold_sample_wall_s=hot_wall,not_realtime_or_actual_certificate_claim=True,negative_cases=negatives,production_actual_native_ROS_model_peer_lifecycle_unexecuted=True,native_MuJoCo_initializer_boundary_unexecuted=True,all_external_writer_hook_coverage_not_yet_qualified=True,complete_route_admission_absent=True,physical_admission=False,wall_s=time.monotonic()-started,source_hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.iterdir()if p.is_file()})
  io.atomic(O/'QUALIFICATION.json',proof);print(json.dumps(proof))
if __name__=='__main__':main()
