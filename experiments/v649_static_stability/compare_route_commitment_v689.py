"""Read-only mechanism comparison of frozen six-meter learned policies."""
from pathlib import Path
import json,hashlib
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v689_dynamic_route_commitment'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=repo/'runs/v688_dynamic_distance_curriculum/learned6m_train_task/paired';new=root/'learned6m_train_task/paired';records={}
for label,pair in [('V688',old),('V689',new)]:
 cell=pair/'geometry_memory';r=read(cell/'result.json');trace=read(cell/'trace.json');ad=lines(cell/'model_admission.jsonl');dist=np.r_[6.,[x['goal_distance_m']for x in trace]];xy=np.asarray([[-3.,-2.],*[t['pose'][:2]for t in trace]]);reverse=[x['step']for x in ad if not x.get('observation_initialization')and x.get('active_gear')==-1];samples=lines(cell/'proposal_learning_samples.jsonl')
 records[label]={'public_steps':r['public_steps'],'strict_arrival':r['strict_safe_arrival'],'goal_distance_m':r['goal_distance_m'],'planning_attempts':r['planning_attempts'],'backup_steps':r['backup_steps'],'reverse_steps':len(reverse),'reverse_net_goal_progress_m':float(np.sum((dist[:-1]-dist[1:])[reverse])),'executed_path_length_m':float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum()),'learned_actual_ordinary_steps':sum(x['selected_role']=='LEARNED'for x in samples),'frozen_model_sha256':r['proposal_model_sha256'],'normalized_initial_state_hash':r['normalized_initial_state_hash']}
a,b=[lines(p/'geometry_memory/v648_execution.jsonl')for p in [old,new]]
differences={k:next((i for i,(x,y)in enumerate(zip(a,b))if np.max(abs(np.asarray(x[k])-y[k]))>1e-12),None)for k in ['ctrl','qpos_full','qvel_full']}
checks={'same_proposal_network_weights':records['V688']['frozen_model_sha256']==records['V689']['frozen_model_sha256']=='c77b5f833fe77d3cadbab9fb41835426a058249728eee94a0cf8e92aa88796c0','same_scene_model_bytes':sha(old/'scene_model.mjb')==sha(new/'scene_model.mjb'),'same_initial_state':records['V688']['normalized_initial_state_hash']==records['V689']['normalized_initial_state_hash']}
out={'status':'MATCHED_CONTEXT_COMPARISON'if all(checks.values())else'FAIL','checks':checks,'records':records,'first_numeric_difference_steps':differences,'robot_integrations':0,'gradient_updates':0,'scope':'one paired development task, two coupled route-trigger changes; not statistical superiority or separated per-change causal effect'}
(root/'MATCHED_ROUTE_COMPARISON.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert all(checks.values())
