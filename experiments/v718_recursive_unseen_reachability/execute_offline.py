"""One finite recursive-domain trial on original saved sensor data."""
import fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import cv2
import numpy as np
from recursive_domain import RecursiveDomain,propagate,GRID,AXIS,LOWER,HALF_DIAGONAL,SPEED,RADIUS
REPO=Path(__file__).resolve().parents[2];OWN=Path(__file__).parent
sys.path.insert(2,str(REPO/'experiments/v712_joint_field_continuation'))
from exact_footprint import pose_values
root=REPO/'runs/v718_recursive_unseen_reachability';root.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
with (REPO/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});begun=time.time();window=dict(started_unix=begun,absolute_deadline_unix=begun+600,limit_s=600,round_closed=False);write(root/'ROUND_WINDOW.json',window)
 def stop(*_):raise TimeoutError('V718_600S_HARD_STOP')
 signal.signal(signal.SIGALRM,stop);signal.alarm(600);status='RUNNING'
 try:
  freeze=read(OWN/'SOURCE_FREEZE.json');assert all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items())
  rng=np.random.default_rng(718);small=rng.random((21,23))<.2;expanded,steps=propagate(small,.08);brute=np.zeros_like(small)
  for i in range(len(small)):
   for j in range(small.shape[1]):
    if i<steps or j<steps or i>=len(small)-steps or j>=small.shape[1]-steps:brute[i,j]=True
    else:brute[i,j]=bool(small[i-steps:i+steps+1,j-steps:j+steps+1].any())
  morphology=np.array_equal(expanded,brute)
  cells=rng.integers(100,len(AXIS)-100,size=(4000,2));within=rng.uniform(-GRID/2,GRID/2,size=(4000,2));motion=rng.uniform(-.12*.08,.12*.08,size=(4000,2));moved=(LOWER+cells*GRID+within+motion-LOWER)/GRID;target=np.rint(moved).astype(int);outer_cover=bool(np.all(abs(target-cells)<=steps))
  pair=REPO/'runs/v712_joint_field_continuation/main01/paired';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json')
  with gzip.open(pair/'geometry_memory/sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
  domain=RecursiveDomain(protocol['start_qpos'][:2]);records=[];checkpoints=[];truth_keep=True;truth_cover=True
  field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.empty((0,4)),circles=np.empty((0,3)),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-100.,upper=100.))
  for packet in packets:
   start=time.monotonic();record=domain.update(packet);record.update(step=packet['step'],update_wall_s=time.monotonic()-start)
   t=packet['time'];center=np.array(config['anchor_xy'])+np.array(config['axis_xy'])*config['amplitude_m']*math.sin(config['omega_rad_s']*t+config['phase_rad']);ix=np.rint((center-LOWER)/GRID).astype(int);kept=bool(domain.possible[tuple(ix)]);truth_keep &= kept;record['evaluator_true_actor_cell_retained']=kept
   poses=np.repeat([[*packet['xy'],packet['yaw']]],329,axis=0);tau=np.arange(329)*.01;times=t+tau;lower=domain.body_lower(poses,times);true=[]
   for pose,at in zip(poses,times):
    xy=np.array(config['anchor_xy'])+np.array(config['axis_xy'])*config['amplitude_m']*math.sin(config['omega_rad_s']*at+config['phase_rad']);field.circles=np.array([[*xy,.10]]);true.append(float(pose_values(field,[pose])[0]))
   excess=float(np.max(lower-true));truth_cover &= excess<=1e-8;record['evaluator_maximum_lower_bound_excess_m']=excess;records.append(record)
   if packet['step'] in [64,104,145]:
    future=poses.copy();future[:,:2]+=np.minimum(tau/1.6,1.)[:,None]*.30*np.array([math.cos(packet['yaw']),math.sin(packet['yaw'])]);value=domain.body_lower(future,times)
    static=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));static_min=float(pose_values(static,future).min())
    checkpoints.append(dict(step=packet['step'],minimum_actor_clearance_lower_bound_m=float(value.min()),minimum_known_clearance_m=static_min,passed=bool(value.min()>=.155 and static_min>=.155)))
    np.savez_compressed(root/('DOMAIN_%03d.npz'%packet['step']),possible=domain.possible,distance=domain.distance,time=t,origin=domain.origin,axis=AXIS)
   if packet['step']%25==0:write(root/'ACTIVE.json',dict(step=packet['step'],retained_possible_cells=record['retained_possible_cells']))
  # Exact maximum rays certify nothing beyond the original initial prior.
  blank=RecursiveDomain(protocol['start_qpos'][:2])
  for packet in packets:
   missing={**packet,'lidar':[1.]*32,'depth':[1.]*15};blank.update(missing)
  observed_subset=bool(np.all(~domain.possible|blank.possible));new_free=int(np.sum(blank.possible&~domain.possible))
  checks=dict(morphology_matches_scalar_bruteforce=morphology,all4000_subcell_motion_outer_covered=outer_cover,all146_true_actor_cells_retained=truth_keep,all146x329_finite_forecast_lower_bounds=truth_cover,maxrange_only_never_adds_free_information=observed_subset,original_v715_checks_pass=all(read(REPO/'runs/v715_submaximum_free_certificate/RESULT.json')['checks'].values()),frozen_inputs=all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items()),zero_simulator_import='mujoco'not in sys.modules)
  passed=all(checks.values())and checkpoints[-1]['passed'];status='RECURSIVE_UNSEEN_OFFLINE_FEASIBILITY_PASS'if passed else'RECURSIVE_UNSEEN_NOT_CERTIFIED'if all(checks.values())else'RECURSIVE_UNSEEN_AUDIT_FAILED'
  write(root/'RESULT.json',dict(status=status,checks=checks,checkpoints=checkpoints,records=records,additional_free_cells_vs_no_observation=new_free,grid_m=GRID,max_axis_speed_numeric_outer_bound_m_s=GRID/.08,physical_candidate_admissible=passed,new_initializations=0,new_integrations=0,training_updates=0,scope='Conditional finite sampled-trajectory certificate under conservative grid propagation; not an executed vehicle control or navigation acceptance.'))
 except BaseException as error:
  status='STOPPED_EXCEPTION';write(root/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
 finally:
  signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-begun);write(root/'ROUND_WINDOW.json',window);write(root/'COMPLETION.json',dict(status=status,round_closed=True,new_initializations=0,new_integrations=0));write(root/'ACTIVE.json',dict(completed=True,status=status));print(json.dumps(dict(status=status,elapsed_s=window['elapsed_s'])))
