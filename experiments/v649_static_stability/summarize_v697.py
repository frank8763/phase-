"""Zero-simulation final accounting and trace metrics for the V697 round."""
import gzip,hashlib,json,math
from collections import Counter
from pathlib import Path
import numpy as np

repo=Path(__file__).resolve().parents[2];src=repo/'experiments/v697_rpccr_dynamic_initialization'
root=repo/'runs/v697_rpccr_dynamic_initialization';window=root/'development01'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ledger=read(root/'ROUND_WINDOW.json');assert ledger['round_closed'],'ROUND_NOT_CLOSED'
completion=read(window/'COMPLETION.json');base=read(root/'FINAL_INDEPENDENT_AUDIT.json')
freeze=read(src/'CANDIDATE_FREEZE.json');checks={'frozen_parent_and_old_failure_records':all(sha(repo/n)==h for n,h in freeze['files'].items()),'base_independent_audit':base['status']=='ALL_DEVELOPMENT_CHECKS_PASS','exact24_seeded_sensor_packet_reconstruction':read(root/'NOISE_PROVENANCE_AUDIT.json')['status']=='PASS'}
metrics=[];supplemental=[];native_total=replay_total=private_total=0
for record in completion['results']:
    pair=repo/record['run'];cell=pair/'geometry_memory';result=read(cell/'result.json') if (cell/'result.json').exists() else read(cell/'interrupted.json')
    rrows=[json.loads(s) for s in (cell/'v648_execution.jsonl').read_text().splitlines()] if (cell/'v648_execution.jsonl').exists() else []
    q=np.asarray([x['qpos_full'] for x in rrows]);v=np.asarray([x['qvel_full'] for x in rrows]);start=np.asarray(read(pair/'STATIC_PROTOCOL.json')['start_qpos'])[:2]
    xy=np.vstack((start,q[:,:2]));goal=np.asarray(read(pair/'STATIC_PROTOCOL.json')['goal_xy']);distance=np.linalg.norm(xy-goal,axis=1)
    selections=[json.loads(s) for s in (cell/'model_admission.jsonl').read_text().splitlines()] if (cell/'model_admission.jsonl').exists() else []
    discovery=read(cell/'FIRST_DISCOVERY.json') if (cell/'FIRST_DISCOVERY.json').exists() else None
    stop=read(cell/'DISCOVERY_BRAKE_COMPLETION.json') if (cell/'DISCOVERY_BRAKE_COMPLETION.json').exists() else None
    tail=read(pair/'SAVED_TAIL_GEOMETRY_AUDIT.json') if (pair/'SAVED_TAIL_GEOMETRY_AUDIT.json').exists() else None
    local={'tail_audit_pass':tail is not None and tail['status']=='ALL_SAVED_TAIL_GEOMETRY_DIRECTION_SCHEDULE_PASS',
           'tail_auditor_source_verified':(pair/'TAIL_AUDITOR_SOURCE.json').exists() and read(pair/'TAIL_AUDITOR_SOURCE.json')['sha256']==sha(repo/'experiments/v649_static_stability/audit_later_stop_certificate_geometry.py'),
           'full_physical_checks':(pair/'INDEPENDENT_CANONICAL_AUDIT.json').exists() and all(read(pair/'INDEPENDENT_CANONICAL_AUDIT.json')['checks'].values()),
           'full_discovery_checks':(pair/'DISCOVERY_CHAIN_AUDIT.json').exists() and all(read(pair/'DISCOVERY_CHAIN_AUDIT.json')['checks'].values())}
    task=read(src/'ORIGINAL_V696_TASK_LIST.json')[11]
    expected_seed=95000011 if record['name']=='anchor_phase0' else task['seed']
    expected_phase=0. if record['name']=='anchor_phase0' else task['phase']
    local['registered_seed_phase']=result.get('seed')==expected_seed and result.get('course_phase')==expected_phase
    supplemental.append({'case':record['name'],'checks':{k:bool(v) for k,v in local.items()},'passed':bool(all(local.values()))})
    physical_steps=result.get('physics_steps',8*len(rrows));native_total+=physical_steps;private_total+=result.get('prediction_steps',0)
    replay=read(pair/'NATIVE_REPLAY_AUDIT.json') if (pair/'NATIVE_REPLAY_AUDIT.json').exists() else {};replay_total+=replay.get('replay_integration_steps',0)
    times=np.r_[0.,[x['time'] for x in rrows]];length=float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum())
    # Signed motion is a measured projection onto current vehicle heading.
    yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    signed=v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw)
    metric={'case':record['name'],'seed':result.get('seed'),'phase':result.get('course_phase'),'outcome':result.get('outcome'),'strict_arrival':result.get('strict_safe_arrival',False),'public_steps':len(rrows),'native_steps':physical_steps,'replay_steps':replay.get('replay_integration_steps',0),'private_integrations':result.get('prediction_steps',0),'simulated_duration_s':float(times[-1]),'path_length_m':length,'final_goal_distance_m':float(distance[-1]),'minimum_actual_clearance_m':result.get('minimum_dynamic_native_clearance_m'),'public_low_speed_endpoint_count':int(np.sum(np.linalg.norm(v[:,:2],axis=1)<.025)),'public_reverse_endpoint_count':int(np.sum(signed<-.025)),'local_goal_distance_increase_endpoints':int(np.sum(np.diff(distance)>.001)),'backup_attempts':result.get('backup_attempts'),'backup_steps':result.get('backup_steps'),'discovery_step':None if discovery is None else discovery['step'],'discovery_progress_m':None if discovery is None else discovery['forward_progress_before_m'],'discovery_speed_m_s':None if discovery is None else discovery['speed_before_m_s'],'stop_finished_step':None if stop is None else stop.get('finished_step'),'source_run':str(pair.relative_to(repo))}
    metrics.append(metric)
    samples=cell/'proposal_learning_samples.jsonl'
    if samples.exists():
        proposal_rows=[json.loads(s) for s in samples.read_text().splitlines()]
        metric['ordinary_selected_commands']=len(proposal_rows)
        metric['learned_selected_commands']=sum(x['selected_role']=='LEARNED' for x in proposal_rows)
    statefile=cell/'motion_estimate.jsonl'
    if statefile.exists():
        states=[json.loads(s) for s in statefile.read_text().splitlines()];tracked=[x for x in states if x['center'] is not None]
        metric['sensor_update_frames']=len(states)
        metric['tracked_frames']=len(tracked)
        metric['frames_with_new_actor_rays']=sum(bool(x.get('observed_this_frame')) for x in tracked)
        metric['maximum_tracked_observation_age_s']=max((x.get('age_s',0.) for x in tracked),default=0.)
        metric['observation_age_caveat']='Includes out-of-range/view geometry after passing; not a count of consecutive random dropouts.'
    decisions=cell/'control_decisions.jsonl'
    if decisions.exists():
        reasons=Counter()
        for line in decisions.open():
            decision=json.loads(line)
            if decision['stage']=='NOMINAL':
                for candidate in decision['candidates']:reasons[str(candidate.get('reason'))]+=1
        metric['ordinary_candidate_reasons']=dict(reasons)
checks['all_supplemental_tail_and_physical_checks']=len(supplemental)==3 and all(x['passed'] for x in supplemental)
report={'status':'ALL_FINAL_EVIDENCE_CHECKS_PASS' if all(checks.values()) else 'NOT_PASSED','checks':{k:bool(v) for k,v in checks.items()},'metrics':metrics,'supplemental_checks':supplemental,'navigation_native_steps':native_total,'native_replay_steps':replay_total,'private_prediction_integrations':private_total,'preflight_count':len(completion['preflights']),'unique_new_development_tasks':1,'old_anchor_reexecutions':sum(x['name']=='anchor_phase0' for x in completion['results']),'conditional_repeats':sum(x['name']=='original_slot12_repeat' for x in completion['results']),'independent_confirmation_navigation_trials':0,'training_updates':0,'algorithm_revisions':0,'original_v696_not_relabelled':True,'verification_integrations':0,'window_elapsed_s':ledger['elapsed_s'],'stop_reason':'REGISTERED_BOUNDED_ROUND_COMPLETE' if all(checks.values()) else 'REGISTERED_ROUND_NOT_PASSED_NO_AUTOMATIC_REPAIR'}
(root/'FINAL_EVIDENCE_ACCOUNT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
