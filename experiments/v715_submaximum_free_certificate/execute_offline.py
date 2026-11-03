"""Saved data only: finite certificate feasibility and meaningful geometry checks."""
import fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from free_certificate import Certificate,reliable_rays,free_samples,body_points,combined_lower,old_lower,GRID,AXIS,CELL_RHO,ACTOR_RADIUS,SLACK,SPEED
REPO=Path(__file__).resolve().parents[2];OWN=Path(__file__).parent
sys.path.insert(1,str(REPO/'experiments/v712_joint_field_continuation'))
from ray_packet_contract import saved_rays_equal
from exact_footprint import pose_values
root=REPO/'runs/v715_submaximum_free_certificate';root.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
with (REPO/'runs/v648_static_unknown/execution.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});begun=time.time()
 window=dict(started_unix=begun,absolute_deadline_unix=begun+600,limit_s=600,round_closed=False,pid=os.getpid());write(root/'ROUND_WINDOW.json',window)
 def alarm(*_):raise TimeoutError('V715_600S_HARD_STOP')
 signal.signal(signal.SIGALRM,alarm);signal.alarm(600);status='RUNNING'
 try:
  freeze=read(OWN/'SOURCE_FREEZE.json');assert all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items())
  pair=REPO/'runs/v712_joint_field_continuation/main01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json')
  with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
  origin=np.array(protocol['start_qpos'][:2]);certificates=[];records=[];all_prefixes=True;truth_cover=True
  field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.empty((0,4)),circles=np.empty((0,3)),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-100.,upper=100.))
  for packet in packets:
   certificate=Certificate(packet,origin);certificates.append(certificate);all_prefixes &= saved_rays_equal(certificate.rays[(certificate.rays[:,4]<3.-certificate.rays[:,5]-1e-5)],packet['rays'])
   # Strict causal history, with actor truth only for finite evaluation.
   poses=np.repeat([[*packet['xy'],packet['yaw']]],329,axis=0);times=float(packet['time'])+np.arange(329)*.01
   value=certificate.body_lower(poses,times);actual=[]
   for pose,t in zip(poses,times):
    xy=np.array(config['anchor_xy'])+np.array(config['axis_xy'])*config['amplitude_m']*math.sin(config['omega_rad_s']*t+config['phase_rad']);field.circles=np.array([[*xy,.10]]);actual.append(float(pose_values(field,[pose])[0]))
   excess=float(np.max(value-np.asarray(actual)));truth_cover &= excess<=1e-8
   records.append(dict(step=packet['step'],time=packet['time'],reliable_rays=len(certificate.rays),certified_free_samples=len(certificate.samples),excluded_cells=int(certificate.excluded.sum()),current_pose_328_end_lower=float(value[-1]),old_328_end_lower=float(old_lower(poses[-1:],times[-1:],origin)[0]),maximum_evaluator_coverage_excess_m=excess))
   if packet['step']%25==0:write(root/'ACTIVE.json',dict(step=packet['step'],completed_packets=len(records),total_packets=len(packets)))
  checkpoints=[]
  for step in [64,104,145]:
   packet=next(p for p in packets if p['step']==step);tau=np.arange(329)*.01;fraction=np.minimum(tau/1.60,1.);poses=np.repeat([[*packet['xy'],packet['yaw']]],329,axis=0);poses[:,:2]+=fraction[:,None]*.30*np.array([math.cos(packet['yaw']),math.sin(packet['yaw'])]);times=float(packet['time'])+tau
   history=[c for c in certificates if c.time<=packet['time']+1e-10];new=combined_lower(history,poses,times,origin);old=old_lower(poses,times,origin)
   static=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
   static_minimum=float(np.min(pose_values(static,poses)))
   checkpoints.append(dict(step=step,minimum_new_actor_clearance_m=float(new.min()),minimum_old_actor_clearance_m=float(old.min()),new_terminal_clearance_m=float(new[-1]),minimum_clearance_gain_m=float(new.min()-old.min()),minimum_known_geometry_clearance_m=static_minimum,actor_certificate_passed=bool(new.min()>=.155 and static_minimum>=.155),history_certificates=len(history),kinematic_interpolation_not_physics=True))
  # Max-range/dropout ambiguity and noncausal future certificates must be rejected.
  negative_packet={'xy':[-4.,-2.],'yaw':0.,'time':0.,'lidar':[1.]*32,'depth':[1.]*15,'lidar_max_range':3.,'depth_max_range':3.}
  no_prefix=len(reliable_rays(negative_packet))==0 and len(free_samples(reliable_rays(negative_packet)))==0
  cert=certificates[-1]
  try:cert.body_lower([[*packets[-1]['xy'],packets[-1]['yaw']]],[0.]);future_rejected=False
  except AssertionError:future_rejected=True
  # Independent brute-force EDT checks at deterministic grid indices.
  zero=np.argwhere(~cert.excluded);rng=np.random.default_rng(714);selected=rng.integers(0,len(AXIS),size=(128,2));errors=[]
  for i,j in selected:
   exact=math.sqrt(float(np.min(np.sum((zero-[i,j])**2,axis=1))))*GRID
   errors.append(float(cert.distance[i,j])-exact)
  # Independent synthetic first-hit disks, clipped errors, and dropped rays.
  rng=np.random.default_rng(71401);synthetic_count=500;false_exclusions=0;synthetic_samples=0
  for trial in range(synthetic_count):
   angle=float(rng.uniform(-np.pi,np.pi));along=float(rng.uniform(.25,2.8));side=float(rng.uniform(-.11,.11));direction=np.asarray([math.cos(angle),math.sin(angle)],np.float32);normal=np.array([-direction[1],direction[0]])
   centre=(direction*along+normal*side).astype(np.float32);origin0=np.asarray([0.,0.],np.float32);raw=3.;sample_distance=0.
   while sample_distance<=3.:
    point=origin0+sample_distance*direction
    if float(np.sum((point-centre).astype(float)**2))<=float(np.float32(.10))**2:raw=sample_distance;break
    sample_distance+=.08
   error=float(rng.choice([-.06,.06])) if trial%2==0 else float(rng.uniform(-.06,.06));observed=float(np.clip(raw+error,0.,3.))
   if trial%20==0:observed=3.
   rays0=np.array([[0.,0.,math.cos(angle),math.sin(angle),observed,.06,.02]]) if .05<observed<3. else np.empty((0,7))
   points0=free_samples(rays0);synthetic_samples+=len(points0)
   false_exclusions+=int(bool(len(points0)) and float(np.min(np.linalg.norm(points0-centre,axis=1)))<.10-SLACK)
  checks=dict(saved_rays_exact=bool(all_prefixes),all146x329_finite_truth_cover=bool(truth_cover),synthetic500_no_false_free_prefix=false_exclusions==0,dropout_maxrange_not_free=no_prefix,noncausal_future_packet_rejected=future_rejected,edt_error_below_slack=max(errors)<=SLACK,old_evidence_unchanged=all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items()),zero_simulator_import='mujoco'not in sys.modules)
  feasible=checkpoints[-1]['actor_certificate_passed'];status='OFFLINE_CERTIFICATE_FEASIBILITY_PASS'if all(checks.values())and feasible else 'OFFLINE_CERTIFICATE_INSUFFICIENT'if all(checks.values())else'CERTIFICATE_AUDIT_FAILED'
  result=dict(status=status,checks=checks,records=records,checkpoints=checkpoints,synthetic_compatible_disk_cases=synthetic_count,synthetic_prefix_samples=synthetic_samples,synthetic_false_exclusions=false_exclusions,maximum_edt_overestimate_m=max(errors),minimum_edt_error_m=min(errors),physical_candidate_admissible=bool(all(checks.values())and feasible),new_initializations=0,new_integrations=0,training_updates=0,scope='Saved sensor data and conservative kinematic witness, not an executable control or dynamic acceptance.')
  write(root/'RESULT.json',result)
 except BaseException as error:
  status='STOPPED_EXCEPTION';write(root/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
 finally:
  signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-begun);write(root/'ROUND_WINDOW.json',window);write(root/'COMPLETION.json',dict(status=status,round_closed=True,new_initializations=0,new_integrations=0,training_updates=0));write(root/'ACTIVE.json',dict(completed=True,status=status));print(json.dumps(dict(status=status,elapsed_s=window['elapsed_s'])))
