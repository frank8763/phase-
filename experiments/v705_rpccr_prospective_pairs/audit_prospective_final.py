"""Independent persisted evidence, pair effects and exact prefix/repeat audit."""
import gzip,hashlib,json,sys
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).resolve().parent;root=repo/'runs/v705_rpccr_prospective_pairs';window=root/'prospective01'
sys.path.insert(0,str(own));from contact_fingerprint import compare_contacts
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
lines=lambda p:[json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []
completion=read(window/'COMPLETION.json');ledger=read(root/'ROUND_WINDOW.json');freeze=read(own/'CANDIDATE_FREEZE.json');plan=read(own/'EXECUTION_PLAN.json')
records=completion['results'];summaries=[];known_nav=known_replay=known_private=0;exact_nav=exact_replay=exact_private=True
checks={'frozen_all_inputs':all(sha(repo/n)==h for n,h in freeze['files'].items()),'closed':ledger['round_closed'] and completion['round_closed'],
        'registered_window':ledger['limit_s']==7200 and ledger['absolute_deadline_unix']-ledger['started_unix']==7200 and ledger['elapsed_s']<=7205,
        'no_extra_tasks_or_training':ledger['navigation_attempts']<=10 and ledger['algorithm_revisions']==ledger['training_updates']==0,
        'exact_fixed_schedule':[{k:x[k] for k in item} for x,item in zip(records,plan)]==plan and len(records)==10,
        'locked_plan':read(window/'LOCKED_EXECUTION_PLAN.json')==plan,'driver_completed':completion['status']=='FIXED_PROSPECTIVE_COMPUTE_PAIRS_COMPLETE'}
for record in records:
    pair=repo/record['run'];cell=pair/'geometry_memory';rp=cell/'result.json';partial=cell/'interrupted.json';result=read(rp) if rp.exists() else None;observed=result or (read(partial) if partial.exists() else {})
    replay=read(pair/'NATIVE_REPLAY_AUDIT.json') if (pair/'NATIVE_REPLAY_AUDIT.json').exists() else None
    known_nav+=observed.get('physics_steps',0);known_private+=observed.get('prediction_steps',0);known_replay+=(replay or {}).get('replay_integration_steps',0)
    exact_nav &= 'physics_steps' in observed;exact_private &= 'prediction_steps' in observed;exact_replay &= replay is not None or observed.get('physics_steps')==0
    local={};metrics=None
    if result is not None:
        for name,status in [('INDEPENDENT_CANONICAL_AUDIT.json','ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS'),('ROUTE_COMMITMENT_AUDIT.json','PASS'),('PROJECTION_LEARNING_AUDIT.json','PASS'),('SAVED_TAIL_GEOMETRY_AUDIT.json','ALL_SAVED_TAIL_GEOMETRY_DIRECTION_SCHEDULE_PASS'),('SHADOW_MODE_AUDIT.json','PASS')]:
            file=pair/name;a=read(file) if file.exists() else {};local[name]=a.get('status')==status and all(a.get('checks',{}).values())
        local['full_replay']=replay is not None and replay['status']=='MATCHED_RECORDED_PUBLIC_STATES' and replay['replay_integration_steps']==result['physics_steps']==result['public_steps']*8 and max(replay['maximum_full_public_qpos_error'],replay['maximum_full_public_qvel_error'],replay['maximum_public_mocap_error'])<=1e-8
        local['model']=replay is not None and replay['scene_model_sha256']==sha(pair/'scene_model.mjb')==read(pair/'STATIC_PROTOCOL.json')['full_model_sha256']
        gate=read(pair/'INITIALIZATION_PROVENANCE.json').get('bootstrap_repair',{})
        local['bootstrap_repair_verified']=gate.get('reset_calls')==1 and gate.get('disabled_before_original_reset') is True and gate.get('old_detour_calls')==gate.get('bootstrap_integrations')==0
        local['raw_safety']=result['minimum_dynamic_native_clearance_m']>=.15 and result['root_mutations_outside_mjstep']==0 and all(result['contacts'][k]==0 for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records'])
        local['task_and_mode']=result['seed']==record['task']['seed'] and result['course_phase']==record['task']['phase'] and read(pair/'ABLATION_PROTOCOL.json')['mode']==record['mode'] and result['proposal_model_sha256']=='fc9d3132c912033e2ec04cd8ae1ce236c818c484d5b96961c6f3dc1b0548b527'
        chain=read(pair/'v699_discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json');failed=[k for k,v in chain['checks'].items() if not v]
        local['causal_chain_except_function']=not(set(failed)-{'moving_before_discovery','new_causal_route_after_stop','actually_continued_after_replanning','strict_arrival'})
        arrived=bool(result['strict_safe_arrival'] and chain['status']=='PASS');local['functional_flag']=arrived==record['functional_passed']
        trace=lines(cell/'v648_execution.jsonl');protocol=read(pair/'STATIC_PROTOCOL.json');goal=np.asarray(protocol['goal_xy']);start=np.asarray(protocol['start_qpos'])[:2]
        xy=np.asarray([start]+[x['qpos_full'][:2] for x in trace]);dist=np.linalg.norm(xy-goal,axis=1);velocity=np.asarray([x['qvel_full'][:2] for x in trace]);yaw=[]
        for x in trace:
            q=x['qpos_full'];yaw.append(np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2)))
        signed=np.sum(velocity*np.c_[np.cos(yaw),np.sin(yaw)],axis=1);handover=lines(cell/'handover_attempts.jsonl');mechanism=read(pair/'SHADOW_MODE_AUDIT.json');learn=read(pair/'PROJECTION_LEARNING_AUDIT.json')
        metrics={'full_chain_arrival':arrived,'outcome':result['outcome'],'public_steps':len(trace),'simulated_time_s':len(trace)*.08,'goal_distance_m':result['goal_distance_m'],'path_length_m':float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum()),'accumulated_goal_regression_m':float(np.maximum(np.diff(dist),0).sum()),'low_speed_public_steps':int((np.linalg.norm(velocity,axis=1)<.05).sum()),'reverse_public_steps':int((signed<-.02).sum()),'backup_steps':result['backup_steps'],'backup_attempts':result['backup_attempts'],'certified_returns':sum(x['status']=='CERTIFIED_RETURN' for x in handover),'suppressed_return_attempts':mechanism['shadow_feasible_returns'],'planning_attempts':result['planning_attempts'],'private_integrations':result['prediction_steps'],'wall_seconds':result['elapsed_s'],'minimum_clearance_m':result['minimum_dynamic_native_clearance_m'],'ordinary_learned_steps':learn['learned_actual_ordinary_steps'],'ordinary_steps':learn['ordinary_teacher_sample_count']}
    summaries.append({'name':record['name'],'slot':record['slot'],'mode':record['mode'],'role':record['role'],'run':record['run'],'checks':local,'all_physical_evidence':bool(local) and all(local.values()),'metrics':metrics,'native_steps':observed.get('physics_steps'),'replay_steps':None if replay is None else replay['replay_integration_steps'],'private_integrations':observed.get('prediction_steps')})
checks['locked_tasks']=read(window/'LOCKED_TASK_LIST.json')==read(own/'TASK_LIST.json')
checks['all10_physical_evidence']=len(summaries)==10 and all(x['all_physical_evidence'] for x in summaries)
comparisons=[]
for record in records:
    if record['role'] not in ('ANCHOR_REFERENCE','ANCHOR_SHADOW','FULL_REPEAT'):continue
    pair=repo/record['run'];base=repo/'runs/v701_rpccr_recovery_ablation/full14/paired' if record['role']=='ANCHOR_REFERENCE' else repo/'runs/v701_rpccr_recovery_ablation/tail14/paired' if record['role']=='ANCHOR_SHADOW' else root/record['repeat_of']/'paired'
    try:
        aa=lines(base/'geometry_memory/v648_execution.jsonl');bb=lines(pair/'geometry_memory/v648_execution.jsonl');errors={k:float(np.max(abs(np.asarray([x[k] for x in aa])-np.asarray([x[k] for x in bb])))) if aa and len(aa)==len(bb) else None for k in ['qpos_full','qvel_full','ctrl','mocap_pos']};a=read(base/'geometry_memory/result.json');b=read(pair/'geometry_memory/result.json');contact=compare_contacts(base,pair)
        good=all(v is not None and v<=1e-8 for v in errors.values()) and contact['passed'] and sha(base/'scene_model.mjb')==sha(pair/'scene_model.mjb') and a['normalized_initial_state_hash']==b['normalized_initial_state_hash'] and a['outcome']==b['outcome'] and a['strict_safe_arrival']==b['strict_safe_arrival'] and read(base/'geometry_memory/FIRST_DISCOVERY.json')==read(pair/'geometry_memory/FIRST_DISCOVERY.json')
        comparisons.append({'name':record['name'],'passed':bool(good),'errors':errors,'contacts':contact})
    except Exception as e:comparisons.append({'name':record['name'],'passed':False,'error':repr(e)})
checks['two_fixed_full_repeats_exact']=len(comparisons)==2 and all(x['passed'] for x in comparisons)
from audit_pair import compare_pair
pairs=[]
for slot in range(1,5):
    full=root/('full%d'%slot)/'paired';shadow=root/('shadow%d'%slot)/'paired'
    if (full/'geometry_memory/result.json').exists() and (shadow/'geometry_memory/result.json').exists():
        try:pairs.append({'slot':slot,**compare_pair(full,shadow)})
        except Exception as e:pairs.append({'slot':slot,'status':'FAIL','error':repr(e)})
checks['four_pairs_independently_recomputed']=len(pairs)==4 and all(x['status']=='PASS' for x in pairs)
try:anchor=compare_pair(repo/'runs/v704_bootstrap_repair/anchor_full/paired',repo/'runs/v704_bootstrap_repair/anchor_shadow/paired');checks['anchor_compute_and_commit_isolation']=anchor['status']=='PASS' and anchor['mechanism_triggered']
except Exception as e:anchor={'status':'FAIL','error':repr(e)};checks['anchor_compute_and_commit_isolation']=False
checks['validated_initialization_and_old_anchors']=read(repo/'runs/v704_bootstrap_repair/FINALIZED.json')['status']=='BOOTSTRAP_REPAIR_AND_ANCHOR_EQUIVALENCE_VALIDATED' and all(read(repo/'runs/v704_bootstrap_repair/FINAL_INDEPENDENT_AUDIT.json')['checks'].values())
checks['four_preflights_noise']= (root/'PREFLIGHT_INDEPENDENT_AUDIT.json').exists() and read(root/'PREFLIGHT_INDEPENDENT_AUDIT.json')['status']=='PASS'
main=[x for x in summaries if x['role']=='PROSPECTIVE_MAIN'];groups={mode:sum(bool((x['metrics'] or {}).get('full_chain_arrival')) for x in main if x['mode']==mode) for mode in ['FULL','SHADOW_COMPLETE_TAIL']}
complete_denominator=len(main)==8 and all(x['metrics'] is not None and x['all_physical_evidence'] for x in main)
out={'status':'PROSPECTIVE_COMPUTE_EVIDENCE_COMPLETE' if all(checks.values()) else 'INCOMPLETE_OR_EXCEPTION','checks':checks,'records':summaries,'comparisons':comparisons,'paired_effects':pairs,'anchor_compute_audit':anchor,'main_arrivals_by_condition':groups,'new_task_denominator':4,'full_condition_success_rates':{m:n/4 for m,n in groups.items()} if complete_denominator else None,'mechanism_triggered_pairs':sum(x.get('mechanism_triggered',False) for x in pairs),'navigation_native_steps':known_nav,'replay_native_steps':known_replay,'private_integrations':known_private,'native_account_exact':bool(exact_nav),'replay_account_exact':bool(exact_replay),'private_account_exact':bool(exact_private),'new_unique_prospective_tasks':4,'old_calibration_executions':0,'reused_old_calibration_executions':2,'fixed_repeat_executions':2,'verification_integrations':0,'training_updates':0,'algorithm_development_revisions':0,'unexecuted_registered_executions':[x['name'] for x in plan if x['name'] not in {r['name'] for r in records}],'mechanism_superiority_established':False,'scope':'Four prespecified new noise/phase tasks, same-state return evaluation matched before commit; not equal divergent total work, geometry generalization or full RP-CCR superiority.'}
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['records','comparisons']},indent=2))
