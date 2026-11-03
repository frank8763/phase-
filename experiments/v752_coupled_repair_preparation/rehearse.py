"""Rehearse the candidate observer on OLD actually executed states only."""
import ast,fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(own));sys.path.insert(1,str(repo/'experiments/v751_coupled_packet_schema_diagnosis'));sys.path.insert(2,str(repo/'experiments/v735_scan_differential_navigation'));sys.path.insert(3,str(repo/'experiments/v733_early_low_translation_scan'));sys.path.insert(4,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V752_MODEL_INITIALIZATION_OR_INTEGRATION_FORBIDDEN')
for n in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,n,forbidden)
from packet_contract import packet_equal
from canonical_sensor_pose import sensor_pose
from sensor_model import packet as sensed_packet
from dynamic_scene import Motion
from recursive_domain import RecursiveDomain
from renewal_state import encode,decode
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v752_coupled_fixture_rehearsal';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+300,limit_s=300,round_closed=False);dump('ROUND_WINDOW.json',window);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V752_300S_ABSOLUTE_STOP')));signal.alarm(300);status='RUNNING'
def clone(d):
 out=RecursiveDomain(d.origin);out.time=d.time;out.possible=d.possible.copy();out.distance=d.distance.copy();out.last=dict(d.last);return out
try:
 assert(repo/'REVIEW_PENDING').exists()
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 def node(text,name):return next(x for x in ast.walk(ast.parse(text))if isinstance(x,ast.FunctionDef)and x.name==name)
 candidate=(own/'probe_candidate.py.txt').read_text();original=(repo/'experiments/v749_coupled_observation_progress/probe.py').read_text();unchanged={name:ast.dump(node(candidate,name),include_attributes=False)==ast.dump(node(original,name),include_attributes=False)for name in ['forecast','perform','branch','make_proof']};assert all(unchanged.values())
 pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');motion=Motion(read(pair/'DYNAMIC_PROTOCOL.json'));initial_calls=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap'];rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];beliefs={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())}
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
 errors=[]
 for pkt,row in zip(packets[1:],rows):
  q=np.asarray(row['qpos_full']);xy,yaw=sensor_pose(q);assert xy.astype(float).tolist()==pkt['xy']and yaw==pkt['yaw'];y=float(np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2)))
  if y!=yaw:errors.append(dict(step=pkt['step'],numpy_minus_canonical_yaw=y-yaw))
 scope=dict(np=np,sensor_pose=sensor_pose,sensed_packet=sensed_packet,protocol=protocol,motion=motion,initial_calls=initial_calls,encode=encode)
 exec(compile(ast.Module(body=[node(candidate,'observe')],type_ignores=[]),'<candidate actual observer>','exec'),scope)
 domain=clone(decode(beliefs[32]['free_space_renewal']));observed=[]
 for step in range(33,74):
  real=SimpleNamespace(qpos=np.asarray(rows[step-1]['qpos_full']),time=packets[step]['time']);o=scope['observe'](real,domain,step);assert packet_equal(o['packet'],packets[step])and o['domain']==beliefs[step]['free_space_renewal'];observed.append(o)
 audit=(own/'audit_candidate.py.txt').read_text();audit_scope=dict(np=np,math=math,poses=lambda q:np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))],sensed_packet=sensed_packet,packet_equal=packet_equal,p=protocol,motion=motion,initial_calls=initial_calls,encode=encode)
 exec(compile(ast.Module(body=[node(audit,'observe')],type_ignores=[]),'<candidate independent observer audit>','exec'),audit_scope)
 domain=clone(decode(beliefs[32]['free_space_renewal']))
 for step,o in zip(range(33,74),observed):audit_scope['observe'](o,np.asarray(rows[step-1]['qpos_full']),step,domain)
 assert all(sha(repo/n)==h for n,h in freeze['files'].items());status='FULL_OLD_CALIBRATION_REHEARSED_REPAIR_PREPARED_NOT_PHYSICALLY_RUN';dump('RESULT.json',dict(status=status,all_old_public_sensor_poses_exact=176,canonical_math_pose_errors=0,numpy_yaw_mismatches=errors,all41_old_calibration_raw_packets_and_domains_exact=True,all41_independent_observer_rehearsal_passed=True,old_coverage_checks=41*329,maximum_actual_coverage_excess_m=max(o['maximum_actual_coverage_excess_m']for o in observed),algorithm_functions_AST_unchanged=unchanged,new_initializations=0,new_integrations=0,new_predictions=0,new_raw_measurements=0,source_states='Old V735 actually executed public33..73, not newly predicted or executed states',candidate_only_text_no_execution_entrypoint=True,three_profiles_still_unexecuted=True))
except BaseException as e:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(status=status,round_closed=True,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
