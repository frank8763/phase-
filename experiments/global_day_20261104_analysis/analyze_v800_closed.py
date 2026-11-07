"""Closed V800 versus old V793 logs, no model, prediction or action search."""
import json,hashlib,signal
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v800_spatial_nominal_global'
read=lambda p:json.loads(p.read_text());rows=lambda p:[json.loads(l)for l in p.open()]if p.exists()else[]
assert(repo/'REVIEW_PENDING').exists()and read(root/'ROUND_WINDOW.json')['round_closed']
out=repo/'runs/v800_saved_comparison';assert not out.exists();out.mkdir()
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('SAVED_V800_180S')));signal.alarm(180)
completion=read(root/'development01/COMPLETION.json');records=[]
for task in completion['records']:
    pair=repo/task['run'];cell=pair/'geometry_memory';execution=rows(cell/'v648_execution.jsonl')
    decisions=rows(cell/'control_decisions.jsonl');ad=rows(cell/'model_admission.jsonl')
    if not execution:continue
    result=read(cell/'result.json')if(cell/'result.json').exists()else task.get('interrupted')
    protocol=read(pair/'STATIC_PROTOCOL.json');goal=np.asarray(protocol['goal_xy']);start=np.asarray(protocol['start_qpos'])[:2]
    q=np.asarray([x['qpos_full']for x in execution]);xy=q[:,:2]
    yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    delta=np.diff(np.vstack([start,xy]),axis=0);signed=np.sum(delta*np.c_[np.cos(yaw),np.sin(yaw)],axis=1)
    distances=np.linalg.norm(xy-goal,axis=1);progress=np.linalg.norm(start-goal)-distances
    nominal=[x for x in decisions if x['stage']=='NOMINAL'];causal_rejected_nominal=sum(c['reason']is None and c['minimum_clearance_m']<.155 for x in nominal for c in x['candidates'])
    first_new=None;first_difference=None;common_error=0.
    if task['task']['slot']==1:
        oldcell=repo/'runs/v793_complete_joint_navigation/main_slot01/paired/geometry_memory';old=rows(oldcell/'v648_execution.jsonl')
        for a,b in zip(old,execution):
            e=max(float(np.max(abs(np.asarray(a[k])-b[k])))for k in ['qpos_full','qvel_full','ctrl','mocap_pos'])
            if e>1e-8:first_difference=a['step'];break
            common_error=max(common_error,e)
        for x in ad:
            if x['status']!='MODEL_SAFE_COMMAND' or x.get('certified_backup_handover'):continue
            nom=next(r for r in nominal if r['step']==x['step']and r['candidate_role']=='ORDINARY')
            safe=sorted([c for c in nom['candidates']if c['reason']is None],key=lambda c:c['score'],reverse=True)
            unique=[];seen=set()
            for c in safe:
                key=tuple(c['first_command'])
                if key not in seen:seen.add(key);unique.append(c)
            chosen=unique[x['joint_admission_distinct_command_rank']]
            if chosen['minimum_clearance_m']<.155:
                first_new=dict(step=x['step'],nominal_causal_minimum_m=chosen['minimum_clearance_m'],nominal_static_minimum_m=chosen['nominal_spatial_minimum_clearance_m'],actual_prefix_tail_causal_minimum_m=x['recovery_reserve']['reserve_minimum_clearance_m'],complete_native=328,nominal_role=chosen['proposal_role']);break
    record=dict(name=task['name'],case=task['task']['case_id'],outcome=(result or{}).get('outcome','UNKNOWN'),
        public_steps=len(execution),actual_native=len(execution)*8,private_native=(result or{}).get('prediction_steps'),
        wall_s=(result or{}).get('elapsed_s'),simulated_s=execution[-1]['time'],
        first_control_difference_from_V793=first_difference,common_prefix_max_error=common_error,
        first_actual_prefix_whose_nominal_future_was_rejected=first_new,
        maximum_original_goal_progress_m=float(progress.max()),best_step=int(np.argmax(progress)),
        final_original_goal_progress_m=float(progress[-1]),remaining_goal_distance_m=float(distances[-1]),final_xy=xy[-1].tolist(),
        path_length_m=float(np.linalg.norm(delta,axis=1).sum()),reverse_projection_m=float(np.maximum(-signed,0).sum()),
        central_root_x0_crossed=bool(np.any(xy[:,0]>=0))if start[0]<0 else None,
        closest_true_actor_center_m=min(float(np.linalg.norm(np.asarray(x['mocap_pos'])[0,:2]-np.asarray(x['qpos_full'])[:2]))for x in execution),
        first_discovery=read(cell/'FIRST_DISCOVERY.json')if(cell/'FIRST_DISCOVERY.json').exists()else None,
        nominal_calls=len(nominal),spatial_admissible_but_future_rejected_nominal=causal_rejected_nominal,
        actual_ordinary_steps=sum(x['status']=='MODEL_SAFE_COMMAND'and not x.get('certified_backup_handover')for x in ad),
        retained_tail_steps=sum(x['status']=='RETAINED_REVERSE_BRAKE_CONTRACT'for x in ad),
        model_initializations_analysis=0,integrations_analysis=0,
        source_result_sha256=hashlib.sha256((cell/'result.json').read_bytes()).hexdigest()if(cell/'result.json').exists()else None)
    records.append(record)
(out/'RESULT.json').write_text(json.dumps(dict(status='CLOSED_SPATIAL_NOMINAL_COMPARISON_COMPLETE',records=records,new_models=0,new_integrations=0,new_actions=0,not_independent_confirmation=True),indent=2)+'\n')
signal.alarm(0);print(json.dumps(records))
