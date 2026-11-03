"""Evidence-only local comparison and next failure decomposition."""
import gzip,hashlib,json,math,os,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];src=repo/'experiments/v721_recursive_unseen_navigation';sys.path.insert(0,str(src))
from renewal_state import decode
from recursive_domain import AXIS,GRID,LOWER
from free_certificate import body_points
from exact_footprint import pose_values
root=repo/'runs/v722_renewal_navigation_diagnosis';root.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]if p.exists()else[]
old=repo/'runs/v712_joint_field_continuation/main01/paired';new=repo/'runs/v721_recursive_unseen_navigation/main01/paired';aa=lines(old/'geometry_memory/v648_execution.jsonl');bb=lines(new/'geometry_memory/v648_execution.jsonl');pa=read(old/'STATIC_PROTOCOL.json');pb=read(new/'STATIC_PROTOCOL.json')
first=None
for a,b in zip(aa,bb):
 error=max(float(np.max(abs(np.asarray(a[k])-b[k])))for k in ['qpos_full','qvel_full','ctrl','mocap_pos'])
 if error>1e-8:first=a['step'];break
comparison=[]
for label,pair,rows in [('OLD_V712',old,aa),('NEW_V721',new,bb)]:
 p=read(pair/'STATIC_PROTOCOL.json');r=read(pair/'geometry_memory/result.json');xy=np.array([x['qpos_full'][:2]for x in rows]);goal=np.array(p['goal_xy']);origin=np.array(p['start_qpos'][:2]);comparison.append(dict(branch=label,outcome=r['outcome'],public_steps=r['public_steps'],goal_distance_at_end_m=r['goal_distance_m'],minimum_goal_distance_m=float(np.min(np.linalg.norm(xy-goal,axis=1))),maximum_displacement_from_start_m=float(np.max(np.linalg.norm(xy-origin,axis=1))),path_length_m=float(np.linalg.norm(np.diff(np.vstack([origin,xy]),axis=0),axis=1).sum()),native_steps=r['physics_steps'],private_integrations=r['prediction_steps'],first_discovery=r['first_discovery_step']))
cell=new/'geometry_memory';states={x['step']:x for x in lines(cell/'motion_estimate.jsonl')};ad=lines(cell/'model_admission.jsonl');decisions=lines(cell/'control_decisions.jsonl');nominal={x['step']:x for x in decisions if x['stage']=='NOMINAL'};activations=[read(p)for p in []]
contracts=[]
for p in sorted((cell/'recovery_contracts').glob('*.gz')):
 with gzip.open(p,'rt')as f:d=json.load(f)
 contracts.append(dict(activation_step=d['activation_step'],created_step=d['created_step'],kind=d['recovery_kind'],target=d['target'],minimum_causal_clearance=d['minimum_causal_predicted_clearance_m'],signed_displacement_m=d['signed_longitudinal_displacement_m']))
append=[x for x in decisions if x['stage']=='BACKUP_APPEND'and 'candidates'in x.get('detail',{})];candidate_counts={};forward_evaluated=0;reverse_selected=0
for event in append:
 for c in event['detail']['candidates']:
  key=c['library']+'/'+c['kind']+'/'+str(c['reason']);candidate_counts[key]=candidate_counts.get(key,0)+1
  forward_evaluated+=c['library']=='FORWARD_EXTENSION'
checkpoints=sorted(set([0,64,*[c['activation_step']-1 for c in contracts],max(states)]));details=[]
for step in checkpoints:
 state=states[step];domain=decode(state['free_space_renewal']);q=pb['start_qpos']if step==0 else bb[step-1]['qpos_full'];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));poses=np.repeat([[q[0],q[1],yaw]],329,axis=0);times=state['time']+np.arange(329)*.01
 dynamic=domain.body_lower(poses,times);field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(pb['known_rectangles']),circles=np.asarray(pb['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));static=float(pose_values(field,poses[:1])[0])
 points,cover=body_points(poses[:1]);values=domain.point_lower(points,np.array([[state['time']]]));j=int(np.argmin(values));critical=points[0,j];ids=np.argwhere(domain.possible);loc=np.array(critical);nearest_id=ids[int(np.argmin(np.sum((LOWER+ids*GRID-loc)**2,axis=1)))];nearest=LOWER+nearest_id*GRID
 in_known=False
 for x,y,hx,hy in pb['known_rectangles']:in_known |= bool(np.all(abs(nearest-[x,y])<=[hx,hy]))
 for x,y,r in pb['known_circles']:in_known |= float(np.linalg.norm(nearest-[x,y]))<=r
 last=nominal.get(step);reason={}
 for c in (last or {}).get('candidates',[]):reason[str(c['reason'])]=reason.get(str(c['reason']),0)+1
 details.append(dict(step=step,time=state['time'],ego_pose=poses[0].tolist(),known_current_clearance_m=static,renewed_current_stationary_actor_clearance_lower_bound_m=float(dynamic[0]),renewed_stationary_328_end_clearance_lower_bound_m=float(dynamic[-1]),minimum_body_probe_xy=critical.tolist(),nearest_possible_center_grid_xy=nearest.tolist(),nearest_possible_center_inside_known_geom=in_known,local_nominal_rejection_counts=reason))
checks=dict(same_registered_start=pa['start_qpos']==pb['start_qpos'],same_goal=pa['goal_xy']==pb['goal_xy'],same_model_bytes=hashlib.sha256((old/'scene_model.mjb').read_bytes()).hexdigest()==hashlib.sha256((new/'scene_model.mjb').read_bytes()).hexdigest(),same_phase=read(old/'DYNAMIC_PROTOCOL.json')['phase_rad']==read(new/'DYNAMIC_PROTOCOL.json')['phase_rad'],new_full_renewal_causal_audit=all(read(new/'v699_discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json')['checks'][k]for k in ['all_raw_packets_reconstructed','all_causal_states_reconstructed','all329_future_coverage']),new_native_audits=read(new/'INDEPENDENT_CANONICAL_AUDIT.json')['status']=='ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS')
out=dict(status='RENEWAL_PILOT_EVIDENCE_DIAGNOSIS_COMPLETE',checks=checks,first_full_state_or_control_difference_step=first,comparison=comparison,contracts=contracts,checkpoints=details,append_candidate_counts=candidate_counts,forward_extension_candidates_evaluated=forward_evaluated,all_new_states_undetected=all(x['center']is None for x in states.values()),new_navigation_integrations=0,new_prediction_integrations=0,new_replay_integrations=0,training_updates=0,
next_unimplemented_hypothesis='Observation renewal improved early admissibility but the unchanged recovery policy can still choose retreat without retaining future observation-supported viability. Test terminal renewal/visibility quality and forward-vs-reverse backup choices under equal full safety checks, only in a separately frozen bounded protocol; untested forward alternatives are not presumed feasible.')
(root/'DIAGNOSIS.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));assert all(checks.values())
