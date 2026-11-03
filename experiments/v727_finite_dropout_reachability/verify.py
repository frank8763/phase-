"""Fixed finite model tests and persisted-data eligibility; no simulator calls."""
import gzip,hashlib,itertools,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v727_finite_dropout_reachability';root.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,x):(root/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def forbidden(*args,**kwargs):raise RuntimeError('V727_ZERO_INITIALIZATION_AND_INTEGRATION')
class Forbidden:
 from_binary_path=staticmethod(forbidden)
 from_xml_path=staticmethod(forbidden)
 from_xml_string=staticmethod(forbidden)
 def __init__(self,*a,**kw):forbidden()
mujoco.MjModel=Forbidden;mujoco.MjData=forbidden
for n in ['mj_step','mj_step1','mj_step2']:setattr(mujoco,n,forbidden)
sys.path.insert(0,str(own));sys.path.insert(1,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
from confidence_domain import ConfidenceDomain,ray_cell_patch,counter_step,MISS_THRESHOLD,ERROR_UPPER,MAX_OPPORTUNITIES,IMPOSSIBLE
from recursive_domain import AXIS,GRID,canonical_distance
from phase14_sensor_utils import ray_cast_distance
assert (repo/'REVIEW_PENDING').exists();os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});begun=time.time();w=dict(started_unix=begun,absolute_deadline_unix=begun+900,limit_s=900,round_closed=False,new_initializations=0,new_integrations=0)
dump('ROUND_WINDOW.json',w)
def timeout(*_):raise TimeoutError('V727_SINGLE_ABSOLUTE_900S_STOP')
signal.signal(signal.SIGALRM,timeout);signal.alarm(900);checks={};runs=[];tail_results=[]
try:
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 rng=np.random.default_rng(7270311);geometry=0
 for i in range(1000):
  xy=rng.uniform(-4,4,2);angle=float(rng.uniform(-np.pi,np.pi));clip=.06 if i%2 else .09;slices,mask=ray_cell_patch(xy,angle,3.,clip);indices=np.argwhere(mask);assert len(indices)>0;j=indices[rng.integers(len(indices))];index=np.array([slices[0].start,slices[1].start])+j;center=AXIS[index]+rng.uniform(-GRID/2,GRID/2,2)
  env=SimpleNamespace(robot_xy=np.asarray(xy,np.float32),map_min=-5.,map_max=5.,rect_obstacles=np.empty((0,4),np.float32),circle_obstacles=np.asarray([[*center,.10]],np.float32))
  distance=ray_cast_distance(env,angle,3.,.08);assert distance<3.-clip-1e-4;geometry+=1
 checks['1000_float32_sampled_whole_cell_hits']=geometry==1000
 n=16;k=4;p=.05;codes=np.arange(2**n,dtype=np.uint32);bits=((codes[:,None]>>np.arange(n))&1).astype(bool);streak=np.zeros(len(codes),int);event=np.zeros(len(codes),bool)
 for i in range(n):streak=np.where(bits[:,i],streak+1,0);event|=streak>=k
 counts=bits.sum(axis=1);exact=float(np.sum((p**counts*(1-p)**(n-counts))[event]));mass=np.zeros(k);mass[0]=1.
 for _ in range(n):new=np.zeros(k);new[0]=mass.sum()*(1-p);new[1:]=mass[:-1]*p;mass=new
 dp=1-float(mass.sum());checks['finite_enumeration_probability_dp_union_bound']=abs(exact-dp)<1e-13 and exact<=n*p**k
 toy=0
 for trial in range(1000):
  cost=np.zeros((11,11),np.uint8);xy=np.array([5,5]);reference=0;first_error=False
  for _ in range(25):
   xy=np.clip(xy+rng.integers(-1,2,2),2,8);total=rng.integers(0,5,(11,11),dtype=np.uint8);nonmax=np.zeros((11,11),bool);m=int(total[tuple(xy)]);drops=rng.random(m)<.05;nonmax[tuple(xy)]=bool(m and not drops.all());free=rng.random((11,11))<.1;free[tuple(xy)]=False
   reference=0 if nonmax[tuple(xy)]else reference+m;first_error|=reference>=MISS_THRESHOLD
   cost=counter_step(cost,total,nonmax,free,1)
   if not first_error:assert int(cost[tuple(xy)])<=reference and cost[tuple(xy)]!=IMPOSSIBLE
  toy+=1
 checks['1000_moving_path_minimum_counter_inequalities']=toy==1000
 cost=np.zeros((5,5),np.uint8);total=np.zeros_like(cost);total[2,2]=1;free=np.zeros_like(cost,bool)
 for i in range(20):
  nonmax=np.zeros_like(cost,bool);nonmax[2,2]=bool(i%2);cost=counter_step(cost,total,nonmax,free,0);assert cost[2,2]<=1
 checks['nonconsecutive_dropouts_do_not_accumulate']=cost[2,2]==0
 for _ in range(MISS_THRESHOLD):cost=counter_step(cost,total,np.zeros_like(cost,bool),free,0)
 checks['correlated_outage_explicitly_breaks_model_guarantee']=cost[2,2]==IMPOSSIBLE
 checks['fixed_finite_conditional_budget']=MISS_THRESHOLD==10 and MAX_OPPORTUNITIES==56447 and ERROR_UPPER<=1e-8
 dump('MATHEMATICAL_AND_SENSOR_TESTS.json',dict(checks={k:bool(v)for k,v in checks.items()},exact_finite_example_probability=exact,markov_probability=dp,finite_example_union_bound=n*p**k,full_task_conditional_error_upper=ERROR_UPPER,scope='Conditional model proof/tests, not empirical real-sensor calibration.'))
 snapshots={};maximum_coverage_excess=0.
 for version in ['v712_joint_field_continuation','v721_recursive_unseen_navigation','v724_progress_observation_recovery']:
  pair=repo/'runs'/version/'main01/paired';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json')
  with gzip.open(pair/'geometry_memory/sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
  domain=ConfidenceDomain(protocol['start_qpos'][:2]);detail=[]
  for packet in packets:
   domain.update(packet);times=packet['time']+np.linspace(0,3.28,329);truth=np.asarray(config['anchor_xy'])+np.sin(times*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy']);excess=float(domain.point_lower(truth,times).max());maximum_coverage_excess=max(maximum_coverage_excess,excess);assert excess<=1e-7,'ACTUAL_ACTOR_EXCLUDED'
   detail.append(dict(step=packet['step'],maximum_range_rays=domain.last['maximum_range_rays'],retained_possible_cells=int(domain.possible.sum()),maximum_actual_forecast_exclusion_excess_m=excess,counter_sha256=domain.last['counter_sha256']))
   if packet['step']in [64,92,133,145,174,len(packets)-1]:
    snapshots[(version,packet['step'])]=(domain.possible.copy(),domain.cost.copy(),float(domain.time),domain.origin.copy())
    np.savez_compressed(root/(version+'_step%03d.npz'%packet['step']),possible=domain.possible,cost=domain.cost,time=domain.time,origin=domain.origin)
   if packet['step']%50==0:print(json.dumps(dict(version=version,step=packet['step'],elapsed_s=time.time()-begun)),flush=True)
  for invalid in [packets[-1],dict(packets[-1],step=1201,time=domain.time+.08)]:
   try:domain.update(invalid)
   except AssertionError:pass
   else:raise AssertionError('DUPLICATE_OR_OVER_BUDGET_PACKET_ACCEPTED')
  runs.append(dict(version=version,packets=len(packets),forecast_samples=len(packets)*329,all_actual_coverage=True,details=detail));dump('SAVED_TRAJECTORIES.json',runs)
 checks['all_saved_trajectories_actual_329_coverage']=maximum_coverage_excess<=1e-7 and len(runs)==3
 checks['duplicate_and_out_of_budget_packets_rejected']=True
 records=read(repo/'runs/v723_recovery_observability_probe/CANDIDATES.json')
 for row in records:
  step=row['checkpoint'];mask,cost,when,origin=snapshots[('v721_recursive_unseen_navigation',step)];domain=ConfidenceDomain(origin);domain.possible=mask;domain.cost=cost;domain.time=when;domain.distance=canonical_distance(mask)
  data=np.load(repo/'runs/v723_recovery_observability_probe'/('CHECKPOINT_%03d_CANDIDATE_%02d.npz'%(step,row['index'])));values=domain.body_lower(data['poses'],when+np.arange(1,329)*.01);minimum=min(float(values.min()),row['minimum_static_clearance_m']);admissible=minimum>=.155 and row['self_domain_margin_m']>=.002 and row['terminal_speed_m_s']<=.025 and (row['kind']=='BRAKE_ONLY'or(row['kind']=='REVERSE_BRAKE'and row['signed_displacement_m']<=-.02)or(row['kind']=='FORWARD_BRAKE'and row['signed_displacement_m']>=.02))
  tail_results.append(dict(checkpoint=step,index=row['index'],kind=row['kind'],old_minimum_causal_m=row['minimum_causal_clearance_m'],new_minimum_causal_m=minimum,new_admissible=bool(admissible),target_command=row['target_command'],new_prediction_or_scene_integrations=0))
 checks['fixed_saved_full_forward_tail_eligible']=any(x['new_admissible']and x['kind']=='FORWARD_BRAKE'for x in tail_results)
 assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 result=dict(status='FINITE_DROPOUT_CONFIDENCE_OFFLINE_QUALIFIED'if all(checks.values())else'NOT_QUALIFIED',checks={k:bool(v)for k,v in checks.items()},saved_packet_count=sum(x['packets']for x in runs),actual_forecast_coverage_samples=sum(x['forecast_samples']for x in runs),maximum_actual_coverage_excess_m=maximum_coverage_excess,conditional_task_error_upper=ERROR_UPPER,full_forward_safe_count=sum(x['new_admissible']and x['kind']=='FORWARD_BRAKE'for x in tail_results),saved_tail_results=tail_results,new_initializations=0,new_integrations=0,training_updates=0,finite_conditional_model_only=True)
 dump('RESULT.json',result);w['status']=result['status']
except BaseException as error:
 w['status']='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
 raise
finally:
 w.update(round_closed=True,elapsed_s=time.time()-begun);dump('ROUND_WINDOW.json',w);signal.alarm(0)
print(json.dumps({k:v for k,v in result.items()if k!='saved_tail_results'}))
