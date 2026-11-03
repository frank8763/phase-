"""Known-map certificate, finite analytic sweep qualification. No simulator."""
import fcntl, hashlib, json, math, os, signal, sys, time, traceback
from pathlib import Path
import numpy as np
REPO=Path(__file__).resolve().parents[2];OWN=Path(__file__).parent
sys.path.insert(0,str(REPO/'experiments/v708_joint_field_qualification'))
from joint_constructor import load_footprint,world,build,write,project,point_clearance,wrap
from task_preflight import certify
ROOT=REPO/'runs/v709_joint_reference_certificate';ROOT.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text())
with (REPO/'runs/v648_static_unknown/execution.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
 start=time.time();window=dict(started_unix=start,absolute_deadline_unix=start+1200,limit_s=1200,pid=os.getpid(),round_closed=False);write(ROOT/'ROUND_WINDOW.json',window)
 freeze=read(OWN/'SOURCE_FREEZE.json')
 def unchanged():assert all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items()),'FROZEN_INPUT_CHANGED'
 def stop(*_):raise TimeoutError('V709_1200S_ABSOLUTE_DEADLINE')
 signal.signal(signal.SIGALRM,stop);signal.alarm(1200);results=[]
 try:
  unchanged();known=read(REPO/'experiments/v706_global_field_qualification/KNOWN_FIELD.json');cases=read(REPO/'experiments/v706_global_field_qualification/SCENE_CASES.json');F=load_footprint()
  for case in cases:
   directory=ROOT/case['id'];directory.mkdir();write(ROOT/'ACTIVE.json',dict(case_id=case['id'],stage='PURE_GEOMETRY'))
   old=read(REPO/'runs/v708_joint_field_qualification'/case['id']/'RESULT.json')
   if old['eligible']:
    result={**old,'reuse_scope':'Exact V708 geometry, not navigation','source':str((REPO/'runs/v708_joint_field_qualification'/case['id']/'RESULT.json').relative_to(REPO))}
   else:
    start_pose=[*case['start_xy'],case['yaw']];w=world(known);field=build(F,w)
    certificate=certify(w,start_pose,case['goal_xy'],.6,.42722137342572125,F,float(field.pose_values([start_pose])[0]))
    write(directory/'KNOWN_REFERENCE_CERTIFICATE.json',certificate)
    if not certificate['eligible']:raise AssertionError('KNOWN_REFERENCE_CONTINUOUS_CERTIFICATE_NOT_FOUND')
    path=np.asarray(certificate['reference_path']);poses=[];remainders=[];rho=math.hypot(.44,.375)
    for a,b in zip(path,path[1:]):
     ds=float(np.linalg.norm(b[:2]-a[:2]));dy=wrap(b[2]-a[2]);n=max(1,math.ceil(ds/.01),math.ceil(abs(dy)/.01))
     for k in range(n):poses.append([*(a[:2]+(k+.5)/n*(b[:2]-a[:2])),a[2]+(k+.5)/n*dy]);remainders.append((ds+rho*abs(dy))/n/2)
    poses=np.array(poses);rem=np.array(remainders);axis=np.arange(-45,46)/10.;xx,yy=np.meshgrid(axis,axis,indexing='ij');points=np.c_[xx.ravel(),yy.ravel()]
    distance,arc,segment,fraction,yaw,total=project(points,path);clearance=point_clearance(points,known)
    tests=dict(near_reference=distance<=1.50,after_start_arc=arc>=1.8,before_goal_arc=arc<=total-1.4,known_point_clearance=clearance>=.90,
      initially_outside_range=np.linalg.norm(points-case['start_xy'],axis=1)>=3.60,away_from_goal=np.linalg.norm(points-case['goal_xy'],axis=1)>=1.4,
      protected_junction=np.linalg.norm(np.maximum(abs(points)-.8,0),axis=1)>=.40)
    ids=np.flatnonzero(np.logical_and.reduce(list(tests.values())));ids=sorted(ids,key=lambda i:(distance[i],-clearance[i],points[i,0],points[i,1]))
    c,s=np.cos(poses[:,2]),np.sin(poses[:,2]);known_lower=float(np.min(field.pose_values(poses)-rem));candidates=[]
    for i in ids:
     d=points[i]-poses[:,:2];local=np.c_[d[:,0]*c+d[:,1]*s,-d[:,0]*s+d[:,1]*c];res=abs(local)-[.44,.375]
     cd=np.where(res.max(axis=1)<=0,res.max(axis=1),np.linalg.norm(np.maximum(res,0),axis=1))-.35
     lower=float(min(known_lower,np.min(cd-rem)))
     candidates.append(dict(grid_index=int(i),anchor_xy=points[i].tolist(),nearest_reference_distance_m=float(distance[i]),nearest_reference_arc_m=float(arc[i]),
       point_clearance_m=float(clearance[i]),swept_radius_m=.35,continuous_lower_bound_m=lower,eligible=lower>=.15,
       axis_xy=[-math.sin(yaw[i]),math.cos(yaw[i])],segment=int(segment[i]),segment_fraction=float(fraction[i])))
    write(directory/'CANDIDATE_GRID.json',dict(points=points,tests=tests,ranked_eligible_ids=[int(i) for i in ids],candidates=candidates))
    chosen=next((x for x in candidates if x['eligible']),None)
    result=dict(case_id=case['id'],eligible=chosen is not None,status='JOINT_REFERENCE_SWEEP_CERTIFIED' if chosen else 'NO_JOINT_REFERENCE_SWEEP_CANDIDATE',attempts=[],navigation_integrations=0)
    if chosen:
     cert={**certificate,'continuous_polygonal_pose_clearance_lower_bound_m':chosen['continuous_lower_bound_m'],'truth_scope':'Whole motion disk permanent occupation outside this unchanged known reference; no claim this actor necessarily obstructs that reference.'}
     result['selection']={**chosen,'rank':next(i for i,x in enumerate(candidates) if x['eligible']),'certificate':cert,'initial_distance_m':float(np.linalg.norm(np.array(chosen['anchor_xy'])-case['start_xy']))}
   write(directory/'RESULT.json',result);results.append(result);write(ROOT/'RESULTS.json',results)
  unchanged();status='ALL_THREE_JOINT_GEOMETRY_CANDIDATES' if all(x['eligible'] for x in results) else 'JOINT_GEOMETRY_NOT_PASSED'
 except BaseException as error:
  status='STOPPED_EXCEPTION';write(ROOT/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
 finally:
  signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-start);write(ROOT/'ROUND_WINDOW.json',window)
  write(ROOT/'COMPLETION.json',dict(status=status,results=results,round_closed=True,simulator_imported='mujoco' in sys.modules,initializations=0,navigation_integrations=0,private_integrations=0,replay_integrations=0,training_updates=0))
  write(ROOT/'ACTIVE.json',dict(completed=True,status=status));print(json.dumps(dict(status=status,elapsed_s=window['elapsed_s'],routes=[dict(case_id=x['case_id'],eligible=x['eligible']) for x in results])))
