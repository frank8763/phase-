"""Persisted teacher/learner comparison, no new rollouts or gradient updates."""
import os,json,hashlib
from pathlib import Path
import numpy as np
repo=Path(os.environ['PHASE_REPO']);root=repo/'runs/v690_visible_eight_meter'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[];traces={}
for p in sorted(root.glob('*/paired/geometry_memory/result.json')):
 pair=p.parents[1];r=read(p);execution=[json.loads(s)for s in(p.parent/'v648_execution.jsonl').read_text().splitlines()];ad=[json.loads(s)for s in(p.parent/'model_admission.jsonl').read_text().splitlines()];xy=np.asarray([read(pair/'STATIC_PROTOCOL.json')['start_qpos'][:2],*[e['qpos_full'][:2]for e in execution]]);goal=np.asarray(read(pair/'STATIC_PROTOCOL.json')['goal_xy']);signed=[]
 for i,a in enumerate(ad):
  if a['status']!='MODEL_SAFE_COMMAND'or a.get('observation_initialization')or a.get('certified_backup_handover'):continue
  q=read(pair/'STATIC_PROTOCOL.json')['start_qpos']if i==0 else execution[i-1]['qpos_full'];yaw=np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));signed.append(float((xy[i+1]-xy[i])@np.array([np.cos(yaw),np.sin(yaw)])))
 records.append({'name':pair.parent.name,'strict_arrival':r['strict_safe_arrival'],'public_steps':r['public_steps'],'simulated_duration_s':r['physics_steps']*.01,'path_length_m':float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum()),'ordinary_reverse_steps':sum(x<-.0001 for x in signed),'backup_steps':r['backup_steps'],'planning_attempts':r['planning_attempts'],'minimum_actual_clearance_m':r['minimum_dynamic_native_clearance_m'],'final_goal_distance_m':r['goal_distance_m'],'minimum_goal_distance_m':float(np.linalg.norm(xy-goal,axis=1).min()),'net_goal_progress_m':float(np.linalg.norm(xy[0]-goal)-r['goal_distance_m'])});traces[pair.parent.name]=(pair,r,execution)
paired={}
if 'teacher8m'in traces and 'learned8m_train_task'in traces:
 a,ar,aa=traces['teacher8m'];b,br,bb=traces['learned8m_train_task'];differences=[]
 for i,(x,y)in enumerate(zip(aa,bb)):
  if max(np.max(abs(np.asarray(x[k])-y[k]))for k in ['qpos_full','qvel_full','ctrl','mocap_pos'])>1e-8:differences.append(i)
 paired={'same_scene_model':sha(a/'scene_model.mjb')==sha(b/'scene_model.mjb'),'same_normalized_initial_state':ar['normalized_initial_state_hash']==br['normalized_initial_state_hash'],'first_full_state_control_difference_step':min(differences)if differences else None,'causal_limit':'teacher vs added and fine-tuned learned proposal; no unmodified6mcheckpoint8m rollout, no isolated weight-training ablation or statistical superiority'}
out={'records':records,'teacher_vs_learner':paired,'verification_integrations':0,'gradient_updates':0,'scope':'finite matched-course descriptive comparison only'}
(root/'TEACHER_LEARNER_COMPARISON.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
