"""Read-only information timing along actual certified stages, no new dynamics."""
import gzip,json,math,os,signal,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo/'experiments/v735_scan_differential_navigation'))
from renewal_state import decode
from exact_footprint import pose_values
root=repo/'runs/v741_preemptive_timing_analysis';root.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text());assert(repo/'REVIEW_PENDING').exists();raw=repo/'runs/v740_preemptive_observation_cycles';r=read(raw/'RESULT.json');p=read(repo/'runs/v735_scan_differential_navigation/main01/paired/STATIC_PROTOCOL.json');static=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));records=[];start=time.time();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('TIMING_ANALYSIS_300S')));signal.alarm(300);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
for branch in r['branches']:
 for cycle in branch['cycles']:
  stages=[cycle['scan']]+[c for c in cycle['successors']if c['index']==cycle['selected_successor']]
  for stage in stages:
   file=raw/(stage['label']+'_OBSERVATIONS.json.gz')
   if not file.exists():continue
   with gzip.open(file,'rt')as f:rows=json.load(f)
   samples=[];actual=np.load(raw/(stage['label']+'_ACTUAL.npz'))
   for j,row in enumerate(rows):
    domain=decode(row['domain']);q=actual['qpos'][8*j+7];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));now=np.r_[q[:2],yaw];dt=np.linspace(0,3.28,329);hold=np.repeat([now],329,axis=0);forward=hold.copy();forward[:,:2]+=np.minimum(dt/1.6,1)[:,None]*.30*np.array([np.cos(yaw),np.sin(yaw)]);hv=float(np.minimum(pose_values(static,hold),domain.body_lower(hold,domain.time+dt)).min());fv=float(np.minimum(pose_values(static,forward),domain.body_lower(forward,domain.time+dt)).min());samples.append(dict(actual_public_step=row['packet']['step'],actual_time=domain.time,geometric_hold_3_28s_lower_m=hv,geometric_forward_0_30m_lower_m=fv,geometric_diagnostic_not_native_control_proof=True))
   records.append(dict(label=stage['label'],samples=samples,hold_qualified_sample_count=sum(x['geometric_hold_3_28s_lower_m']>=.155 for x in samples),forward_qualified_sample_count=sum(x['geometric_forward_0_30m_lower_m']>=.155 for x in samples),end_hold_m=samples[-1]['geometric_hold_3_28s_lower_m'],end_forward_m=samples[-1]['geometric_forward_0_30m_lower_m']))
signal.alarm(0);out=dict(status='ACTUAL_OBSERVATION_INFORMATION_TIMING_ANALYZED',actual_stages=len(records),actual_packets=sum(len(x['samples'])for x in records),records=records,new_initializations=0,new_integrations=0,elapsed_s=time.time()-start,scope='Geometric information timing only; no new native handover verified.');(root/'RESULT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='records'}))
