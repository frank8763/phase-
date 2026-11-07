"""Zero-model saved-trajectory qualification and independent exact-rectangle audit."""
import os,json,sys,hashlib,time,signal
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;source=repo/'experiments/v778_global_retained_reentry';sys.path.insert(0,str(source));sys.path.insert(0,str(own));sys.path.insert(0,str(repo/'runs/v771_audit_dependencies/site'))
from scipy.spatial import cKDTree
from renewal_state import decode
from exact_footprint import pose_values
from free_certificate import old_lower
from recursive_domain import AXIS,GRID,HALF_DIAGONAL,SLACK,SPEED
from refined_body import refined,original
root=repo/'runs/v785_footprint_certificate_refinement';root.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items());started=time.time();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V785_300S_CAP')));signal.alarm(300);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
raw=repo/'runs/v778_global_retained_reentry/v780_main01/paired';cell=raw/'geometry_memory';protocol=read(raw/'STATIC_PROTOCOL.json');b=np.asarray(protocol['footprint_bounds']);field=SimpleNamespace(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));records=[];exact_checks=[]
def exact_body(tree,centers,pose,now):
 # Independent distance of lattice-center set to a rotated rectangle.
 c,s=np.cos(pose[2]),np.sin(pose[2]);rot=np.array([[c,-s],[s,c]]);corners=np.array([[-.44,-.375],[-.44,.375],[.44,-.375],[.44,.375]])@rot.T+pose[:2];query=np.vstack([pose[:2],corners]);_,indices=tree.query(query);local=(centers[np.asarray(indices)]-pose[:2])@rot;dist=np.linalg.norm(np.maximum(abs(local)-[.44,.375],0),axis=1);upper=float(dist.min());ids=tree.query_ball_point(pose[:2],upper+np.hypot(.44,.375)+1e-8);local=(centers[np.asarray(ids)]-pose[:2])@rot;value=float(np.linalg.norm(np.maximum(abs(local)-[.44,.375],0),axis=1).min());return max(0.,value-HALF_DIAGONAL-SLACK)-SPEED*now-.10
try:
 for file in sorted((cell/'retained_reentry').glob('step????.json')):
  x=read(file);domain=decode(x['forecast_state']['free_space_renewal']);ij=np.argwhere(domain.possible);centers=np.c_[AXIS[ij[:,0]],AXIS[ij[:,1]]];tree=cKDTree(centers);saved=[]
  for c in x['records']:
   z=np.load(cell/'retained_reentry'/(c['label']+'.npz'));p=z['poses'];times=domain.time+np.arange(1,329)*.01;old=original(domain,p,times);new=refined(domain,p,times);assert np.all(new>=old-1e-12);static=pose_values(field,p);before=float(np.minimum(static,old).min());after=float(np.minimum(static,new).min());assert abs(before-c['minimum_causal_clearance_m'])<=1e-8
   saved.append(dict(index=c['index'],target=c['target'],old_minimum_m=before,new_minimum_m=after,old_gate=c['reason'],new_geometric_passed=after>=.155,goal_progress_m=c['goal_progress_m'],other_original_gates=c['self_margin_m']>=.002 and c['terminal_speed_m_s']<=.025 and c['terminal_angular_speed_rad_s']<=.025));np.savez_compressed(root/(c['label']+'_LOWERS.npz'),old=old,refined=new,static=static)
   # First, critical and terminal native poses for two predeclared candidates 2 and 11.
   if c['index']in[2,11]:
    for k in sorted(set([0,int(np.argmin(new)),327])):
     exact=exact_body(tree,centers,p[k],times[k]-domain.time);reference=max(exact,float(old_lower(p[k:k+1],times[k:k+1],domain.origin)[0]));assert new[k]<=reference+1e-8,'REFINEMENT_EXCEEDS_INDEPENDENT_EXACT_RECTANGLE_BOUND';exact_checks.append(dict(step=x['step'],candidate=c['index'],native=k+1,refined=float(new[k]),independent_exact_lower=reference))
  record=dict(step=x['step'],old_admitted=sum(c['reason']is None for c in x['records']),new_admitted=sum(c['new_geometric_passed']and c['other_original_gates']for c in saved),positive_new=sum(c['new_geometric_passed']and c['other_original_gates']and c['goal_progress_m']>=.05 for c in saved),candidates=saved);records.append(record);(root/'STATES.json').write_text(json.dumps(records,indent=2)+'\n');print('STATE',record['step'],record['old_admitted'],record['new_admitted'],record['positive_new'],flush=True)
 assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 result=dict(status='FULL_BODY_REFINEMENT_SAVED_QUALIFIED',states=records,independent_exact_rectangle_checks=len(exact_checks),new_admission_flips=sum(x['new_admitted']-x['old_admitted']for x in records),new_model_initializations=0,new_integrations=0,new_navigation=0,thresholds_unchanged=True,axis_speed_unchanged=True,scope='tighter conservative certificate discretization; no controller or global acceptance result');(root/'EXACT_RECTANGLE_CHECKS.json').write_text(json.dumps(exact_checks,indent=2)+'\n');(root/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='states'}),flush=True)
finally:signal.alarm(0);(root/'ROUND_WINDOW.json').write_text(json.dumps(dict(started_unix=started,absolute_deadline_unix=started+300,round_closed=True,elapsed_s=time.time()-started,new_models=0,new_integrations=0),indent=2)+'\n')
