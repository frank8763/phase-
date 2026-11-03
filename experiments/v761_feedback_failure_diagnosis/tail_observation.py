import gzip,json,hashlib,sys,signal,os,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(repo/'experiments/v735_scan_differential_navigation'))
from renewal_state import decode
from exact_footprint import pose_values
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
f=read(own/'TAIL_OBSERVATION_FREEZE.json');assert all(sha(repo/n)==h for n,h in f.items());assert(repo/'REVIEW_PENDING').exists()
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('ZERO_PHYSICS_600S_STOP')));signal.alarm(600);start=time.time()
raw=repo/'runs/v759_state_feedback_execution';a=np.load(raw/'FEEDBACK_MAIN_ACTUAL.npz');p=read(repo/'runs/v735_scan_differential_navigation/main01/paired/STATIC_PROTOCOL.json');b=np.asarray(p['footprint_bounds']);field=SimpleNamespace(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
with gzip.open(raw/'FEEDBACK_MAIN_OBSERVATIONS.json.gz','rt')as stream:obs=json.load(stream)
rows=[]
for j,o in enumerate(obs):
 q=a['qpos'][8*j+7];yaw=np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));domain=decode(o['domain']);poses=np.repeat([[q[0],q[1],yaw]],329,axis=0);times=domain.time+np.linspace(0,3.28,329);static=float(pose_values(field,poses).min());unknown=float(domain.body_lower(poses,times).min());rows.append(dict(local_public=j+1,static_clearance_m=static,unknown_future_clearance_m=unknown,geometric_hold_only_pass=min(static,unknown)>=.155))
result=dict(status='SAVED_GEOMETRIC_HOLD_REFERENCE_ONLY',rows=rows,passing_before_rejection=[x['local_public']for x in rows if x['local_public']<52 and x['geometric_hold_only_pass']],passing_after_rejection=[x['local_public']for x in rows if x['local_public']>=52 and x['geometric_hold_only_pass']],new_model_initializations=0,new_integrations=0,new_physical_predictions=0,new_observations=0,new_navigation=0,physical_action_qualification=False,elapsed_s=time.time()-start)
assert all(sha(repo/n)==h for n,h in f.items());(repo/'runs/v761_feedback_failure_diagnosis/TAIL_OBSERVATION.json').write_text(json.dumps(result,indent=2)+'\n');signal.alarm(0)
print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
