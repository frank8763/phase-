"""Fixed-checkpoint interval feasibility; entirely outside MuJoCo."""
import fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from interval_certificate import certify,minimum_displacement,maximum_displacement,past_box
REPO=Path(__file__).resolve().parents[2];OWN=Path(__file__).parent
sys.path.insert(1,str(REPO/'experiments/v715_submaximum_free_certificate'))
from free_certificate import Certificate
sys.path.insert(2,str(REPO/'experiments/v712_joint_field_continuation'))
from motion_tracker import paired_rectangle_clearance
root=REPO/'runs/v717_temporal_free_viability';root.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
with (REPO/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});begun=time.time();window=dict(started_unix=begun,absolute_deadline_unix=begun+600,limit_s=600,round_closed=False);write(root/'ROUND_WINDOW.json',window)
 def stop(*_):raise TimeoutError('V717_600S_HARD_STOP')
 signal.signal(signal.SIGALRM,stop);signal.alarm(600);status='RUNNING'
 try:
  freeze=read(OWN/'SOURCE_FREEZE.json');assert all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items())
  rng=np.random.default_rng(717);bound_error=0.;cases=4000;n=1200
  initial=rng.uniform(-.12,.12,size=(cases,2));duration=rng.uniform(0,12,size=(cases,1));dt=duration/n;v=initial.copy();displacement=np.zeros((cases,2))
  for k in range(n):
   acceleration=rng.uniform(-.04,.04,size=(cases,2));next_v=np.clip(v+dt*acceleration,-.12,.12);displacement+=(v+next_v)*.5*dt;v=next_v
  lo=minimum_displacement(duration,initial);hi=maximum_displacement(duration,initial)
  backward_lo=displacement-maximum_displacement(duration,v);backward_hi=displacement-minimum_displacement(duration,v)
  bound_error=max(0.,float(np.max(displacement-hi)),float(np.max(lo-displacement)),float(np.max(backward_lo)),float(np.max(-backward_hi)))
  assert bound_error<=1e-8
  pair=REPO/'runs/v712_joint_field_continuation/main01/paired';protocol=read(pair/'STATIC_PROTOCOL.json')
  with gzip.open(pair/'geometry_memory/sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
  certificates=[Certificate(p,protocol['start_qpos'][:2])for p in packets];results=[]
  for step in [64,104,145]:
   packet=next(p for p in packets if p['step']==step);tau=np.arange(329)*.01;poses=np.repeat([[*packet['xy'],packet['yaw']]],329,axis=0);poses[:,:2]+=np.minimum(tau/1.6,1.)[:,None]*.30*np.array([math.cos(packet['yaw']),math.sin(packet['yaw'])]);history=[c for c in certificates if c.time<=packet['time']+1e-10]
   write(root/'ACTIVE.json',dict(step=step,stage='INTERVAL_BRANCH_BOUND'))
   result=certify(poses,tau,float(packet['time']),history,paired_rectangle_clearance);result.update(step=step,history_certificates=len(history));write(root/('CHECKPOINT_%03d.json'%step),result)
   nodes={n['id']:n for n in result['nodes']};checks=[]
   for row in result['nodes']:
    if row['classification']=='SPLIT'and all(i in nodes for i in row['children']):
     a,b=[nodes[i]for i in row['children']];axis=row['axis'];checks.append(a['lower']==row['lower']and b['upper']==row['upper']and a['upper'][axis]==b['lower'][axis])
   assert all(checks)
   results.append(dict(step=step,status=result['status'],processed_nodes=result['processed_nodes'],pending_nodes=result['pending_nodes'],unresolved_leaf_count=result['unresolved_leaf_count'],split_checks=len(checks)))
  empty=certify(poses,tau,float(packet['time']),[],paired_rectangle_clearance,limit=64)
  assert not empty['passed'],'MISSING_OBSERVATIONS_FALSE_CERTIFICATE'
  sufficient=results[-1]['status']=='FULL_INTERVAL_CERTIFICATE';status='TEMPORAL_INTERVAL_FEASIBILITY_PASS'if sufficient else'TEMPORAL_INTERVAL_NOT_CERTIFIED'
  write(root/'RESULT.json',dict(status=status,checkpoints=results,velocity_acceleration_bound_test_cases=4000,maximum_bound_violation_m=bound_error,missing_observations_rejected=True,physical_candidate_admissible=sufficient,new_initializations=0,new_integrations=0,training_updates=0,scope='Fixed finite pose interpolation certificate under conditional sensor/motion assumptions; not a MuJoCo control or dynamic navigation success.'))
 except BaseException as error:
  status='STOPPED_EXCEPTION';write(root/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
 finally:
  signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-begun);write(root/'ROUND_WINDOW.json',window);write(root/'COMPLETION.json',dict(status=status,round_closed=True,new_initializations=0,new_integrations=0));write(root/'ACTIVE.json',dict(completed=True,status=status));print(json.dumps(dict(status=status,elapsed_s=window['elapsed_s'])))
