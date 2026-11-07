"""Closed actual logs: V802 prefix equivalence, work and route following."""
import gzip,json,sys,signal
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v802_exact_rejection_global';out=repo/'runs/v802_saved_comparison'
read=lambda p:json.loads(p.read_text());lines=lambda p:list(map(json.loads,p.read_text().splitlines()))
assert(repo/'REVIEW_PENDING').exists()and read(root/'ROUND_WINDOW.json')['round_closed']and not out.exists();out.mkdir()
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('SAVED_ANALYSIS_180S')));signal.alarm(180)
sys.path.insert(0,str(repo/'experiments/v802_exact_rejection_global'));from serial_predictor import project_to_segment_path
all_records=[]
for task in read(root/'development01/COMPLETION.json')['records']:
 cell=repo/task['run']/'geometry_memory';r=read(cell/'result.json')if(cell/'result.json').exists()else task.get('interrupted');ex=lines(cell/'v648_execution.jsonl');dec=lines(cell/'control_decisions.jsonl');p=read(cell.parent/'STATIC_PROTOCOL.json');goal=np.asarray(p['goal_xy']);start=np.asarray(p['start_qpos'][:2]);xy=np.asarray([x['xy']for x in ex]);q=np.asarray([x['qpos_full']for x in ex]);yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));delta=np.diff(np.vstack([start,xy]),axis=0);signed=np.sum(delta*np.c_[np.cos(yaw),np.sin(yaw)],axis=1);progress=np.linalg.norm(start-goal)-np.linalg.norm(xy-goal,axis=1)
 native=list(map(json.loads,gzip.open(cell/'dynamic_native.jsonl.gz','rt')));nq=np.asarray([x['qpos_full']for x in native]);ny=np.arctan2(2*(nq[:,3]*nq[:,6]+nq[:,4]*nq[:,5]),1-2*(nq[:,5]**2+nq[:,6]**2));poses=np.c_[nq[:,:2],ny];plans=sorted(cell.glob('planning_*.json'));tracking=[]
 for i,file in enumerate(plans):
  plan=read(file);a=plan['step']*8;b=len(native)if i+1==len(plans)else read(plans[i+1])['step']*8
  if b>a:
   arc,contour,reference_heading=project_to_segment_path(poses[a:b],np.asarray(plan['path'])[:,:3]);heading=(ny[a:b]-reference_heading+np.pi)%(2*np.pi)-np.pi;tracking.extend(zip(contour.tolist(),heading.tolist()))
 tails=[t for x in dec if x.get('stage')=='BACKUP_APPEND'for t in x['detail'].get('candidates',[])];ordinary=[x for x in dec if x.get('stage')=='NOMINAL'and x.get('candidate_role')=='ORDINARY'];append=[x for x in dec if x.get('stage')=='BACKUP_APPEND'and x.get('candidate_role')=='ORDINARY'];early=[t for t in tails if t.get('full_minimum_not_evaluated')];audit=read(cell.parent/'EXACT_REJECTION_AUDIT.json')if(cell.parent/'EXACT_REJECTION_AUDIT.json').exists()else None
 record=dict(name=task['name'],case=task['task']['case_id'],outcome=r.get('outcome','UNKNOWN'),strict_arrival=r.get('strict_safe_arrival'),public_steps=len(ex),navigation_native=r.get('physics_steps'),private_native=r.get('prediction_steps'),wall_s=r.get('elapsed_s'),final_native_speed_m_s=float(np.linalg.norm(native[-1]['qvel_full'][:2])),simulated_s=float(ex[-1]['time']),maximum_goal_progress_m=float(progress.max()),final_goal_progress_m=float(progress[-1]),remaining_goal_distance_m=float(np.linalg.norm(xy[-1]-goal)),final_xy=xy[-1].tolist(),actual_path_length_m=float(np.linalg.norm(delta,axis=1).sum()),reverse_projection_m=float(np.maximum(-signed,0).sum()),central_x0_crossed=bool((xy[:,0]>=0).any())if start[0]<0 else None,first_discovery=r.get('first_discovery_step'),closest_actual_actor_center_m=min(float(np.linalg.norm(np.asarray(x['mocap_pos'])[0,:2]-np.asarray(x['qpos_full'])[:2]))for x in native),full_native_tracking_samples=len(tracking),max_native_contour_m=max(x[0]for x in tracking),final_native_contour_m=tracking[-1][0],max_native_heading_error_rad=max(abs(x[1])for x in tracking),tail_predictions=len(tails),early_rejects=len(early),complete_evaluations=len(tails)-len(early),online_tail_geometry_wall_s=sum(t.get('geometry_wall_s',0.)for t in tails),ordinary_append_calls=len(append),ordinary_nominal_forecasts=sum(len(x['candidates'])for x in ordinary),rejection_audit=audit,new_models_analysis=0,new_integrations_analysis=0)
 def work_before(limit):
  ns=[x for x in ordinary if x['step']<limit];aps=[x for x in append if x['step']<limit and x['detail']['status']!='SKIPPED_NO_NOMINAL'];ts=[t for x in aps for t in x['detail'].get('candidates',[])]
  return sum(len(x['candidates'])for x in ns)*240+len(aps)*8+len(ts)*320
 record['ordinary_counted_private_native']=work_before(100000)
 record['counted_private_equals_result']=record['ordinary_counted_private_native']==r.get('prediction_steps')
 record['first200_counted_private_native']=work_before(200)
 record['after200_counted_private_native']=work_before(100000)-work_before(200)
 record['first200_private_per_public']=work_before(200)/min(len(ex),200)
 record['after200_private_per_public']=record['after200_counted_private_native']/(len(ex)-200)if len(ex)>200 else None
 all_records.append(record)
res=dict(status='CLOSED_EXACT_ACCELERATION_INTERPRETATION',records=all_records,new_models=0,new_integrations=0,not_new_confirmation=True)
(out/'RESULT.json').write_text(json.dumps(res,indent=2)+'\n');signal.alarm(0);print(json.dumps(res))
