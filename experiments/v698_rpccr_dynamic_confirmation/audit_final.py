"""Independent immutable-task, full-evidence and actual-integration audit; no physics."""
import hashlib,json,sys
from pathlib import Path
import numpy as np

repo=Path(__file__).resolve().parents[2];own=Path(__file__).resolve().parent;worker=repo/'experiments/v697_rpccr_dynamic_initialization'
sys.path.insert(0,str(worker));from contact_fingerprint import compare_contacts
root=repo/'runs/v698_rpccr_dynamic_confirmation';window=root/'confirmation01'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tasks=read(own/'TASK_LIST.json');c=read(window/'COMPLETION.json');ledger=read(root/'ROUND_WINDOW.json');records=c['results'];freeze=read(own/'CANDIDATE_FREEZE.json')
main=[x for x in records if not x['repeat']];repeats=[x for x in records if x['repeat']]
checks={'frozen_all_inputs':all(sha(repo/n)==h for n,h in freeze['files'].items()),
        'task_list_exact':read(window/'LOCKED_TASK_LIST.json')==tasks,
        'closed':c['round_closed'] and ledger['round_closed'],
        'registered_absolute_window':ledger['limit_s']==15000 and ledger['absolute_deadline_unix']-ledger['started_unix']==15000 and ledger['elapsed_s']<=15005,
        'no_algorithm_training_change':ledger['algorithm_revisions']==ledger['gradient_updates']==ledger['sac_gradient_updates']==0,
        'preflight24_independent':(root/'PREFLIGHT_INDEPENDENT_AUDIT.json').exists() and read(root/'PREFLIGHT_INDEPENDENT_AUDIT.json')['status']=='PASS',
        'all24_main_without_replacement':len(main)==24 and [x['task'] for x in main]==tasks,
        'exact_three_preselected_repeats':len(repeats)==3 and [x['task']['slot'] for x in repeats]==[1,8,20],
        'driver_provisional_gate':c['status']=='PROVISIONAL_FRESH24_AND_THREE_REPEATS_PASS' and c['fresh_confirmation_gate_passed']}
checks['outer_freeze_unchanged']=all(sha(repo/n)==h for n,h in read(window/'CONFIRMATION_SOURCE_FREEZE.json').items())
summaries=[];known_native=known_private=known_replay=0;exact_private=True
for record in records:
    pair=repo/record['run'];result_path=pair/'geometry_memory/result.json';partial_path=pair/'geometry_memory/interrupted.json'
    r=read(result_path) if result_path.exists() else None;p=read(partial_path) if partial_path.exists() else None;observed=r or p or {}
    known_native+=observed.get('physics_steps',0);known_private+=observed.get('prediction_steps',0);exact_private &= 'prediction_steps' in observed
    replay_path=pair/'NATIVE_REPLAY_AUDIT.json';replay=read(replay_path) if replay_path.exists() else None
    if replay:known_replay+=replay['replay_integration_steps']
    local={};functional=False
    if r is not None:
        for filename,status in [('INDEPENDENT_CANONICAL_AUDIT.json','ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS'),('ROUTE_COMMITMENT_AUDIT.json','PASS'),('PROJECTION_LEARNING_AUDIT.json','PASS'),('SAVED_TAIL_GEOMETRY_AUDIT.json','ALL_SAVED_TAIL_GEOMETRY_DIRECTION_SCHEDULE_PASS')]:
            path=pair/filename;a=read(path) if path.exists() else None;local[filename]=a is not None and a['status']==status and all(a.get('checks',{}).values())
        local['replay_exact']=replay is not None and replay['status']=='MATCHED_RECORDED_PUBLIC_STATES' and replay['replay_integration_steps']==r['physics_steps']==8*r['public_steps'] and max(replay['maximum_full_public_qpos_error'],replay['maximum_full_public_qvel_error'],replay['maximum_public_mocap_error'])<=1e-8
        local['full_model']=replay is not None and sha(pair/'scene_model.mjb')==replay['scene_model_sha256']==read(pair/'STATIC_PROTOCOL.json')['full_model_sha256']
        local['correct_task']=record['task']['seed']==r['seed'] and record['task']['phase']==r['course_phase']
        local['actual_clearance_contacts']=r['minimum_dynamic_native_clearance_m']>=.15 and r['root_mutations_outside_mjstep']==0 and all(r['contacts'][k]==0 for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records'])
        local['frozen_model']=r['proposal_model_sha256']=='fc9d3132c912033e2ec04cd8ae1ce236c818c484d5b96961c6f3dc1b0548b527'
        chain_path=pair/'DISCOVERY_CHAIN_AUDIT.json';chain=read(chain_path) if chain_path.exists() else None
        functional=bool(r['strict_safe_arrival'] and r['goal_distance_m']<=.45 and chain is not None and chain['status']=='PASS' and all(chain['checks'].values()))
        local['functional_flag_consistent']=functional==record.get('functional_passed',False)
    summaries.append({'slot':record['task']['slot'],'seed':record['task']['seed'],'phase':record['task']['phase'],'group':record['task']['initial_motion_direction'],'repeat':record['repeat'],'name':record['name'],'run':record['run'],'result_present':r is not None,'functional_arrival':functional,'physical_evidence_passed':bool(r is not None and local and all(local.values())),'checks':{k:bool(v) for k,v in local.items()},'public_steps':observed.get('public_steps'),'native_steps':observed.get('physics_steps'),'private_integrations':observed.get('prediction_steps'),'replay_steps':None if replay is None else replay['replay_integration_steps'],'minimum_actual_clearance_m':None if r is None else r['minimum_dynamic_native_clearance_m'],'goal_distance_m':None if r is None else r['goal_distance_m'],'outcome':observed.get('outcome')})
main_summary=[s for s in summaries if not s['repeat']]
groups={group:sum(s['functional_arrival'] for s in main_summary if s['group']==group) for group in ['POSITIVE_Y','NEGATIVE_Y']}
checks.update(all_physical_evidence=len(summaries)==27 and all(s['physical_evidence_passed'] for s in summaries),at_least23_main_arrivals=sum(groups.values())>=23,both_groups_at_least11=min(groups.values())>=11)
repeat_details=[]
for record in repeats:
    base=next((x for x in main if x['task']==record['task']),None)
    if base is None:repeat_details.append({'slot':record['task']['slot'],'passed':False});continue
    a=repo/base['run'];b=repo/record['run'];path_a=a/'geometry_memory/v648_execution.jsonl';path_b=b/'geometry_memory/v648_execution.jsonl'
    try:
        aa=[json.loads(s) for s in path_a.read_text().splitlines()];bb=[json.loads(s) for s in path_b.read_text().splitlines()]
        errors={k:float(np.max(abs(np.asarray([x[k] for x in aa])-np.asarray([x[k] for x in bb])))) if len(aa)==len(bb) else None for k in ['qpos_full','qvel_full','ctrl','mocap_pos']}
        contacts=compare_contacts(a,b);ar=read(a/'geometry_memory/result.json');br=read(b/'geometry_memory/result.json')
        passed=all(v is not None and v<=1e-8 for v in errors.values()) and contacts['passed'] and sha(a/'scene_model.mjb')==sha(b/'scene_model.mjb') and ar['normalized_initial_state_hash']==br['normalized_initial_state_hash'] and read(a/'geometry_memory/FIRST_DISCOVERY.json')==read(b/'geometry_memory/FIRST_DISCOVERY.json') and base['functional_passed'] and record['functional_passed']
        repeat_details.append({'slot':record['task']['slot'],'passed':bool(passed),'errors':errors,'contacts':contacts})
    except Exception as e:repeat_details.append({'slot':record['task']['slot'],'passed':False,'error':repr(e)})
checks['three_full_repeats_recomputed']=len(repeat_details)==3 and all(x['passed'] for x in repeat_details)
result={'status':'FINITE_MOVING_DISCOVERY_CONFIRMATION_PASS' if all(checks.values()) else 'NOT_PASSED','checks':{k:bool(v) for k,v in checks.items()},'fixed_task_denominator':24,'main_navigation_attempted':len(main),'main_result_count':sum(s['result_present'] for s in main_summary),'main_functional_arrivals':sum(groups.values()),'main_navigation_unexecuted':24-len(main),'groups':groups,'complete_repeats_attempted':len(repeats),'full24_navigation_success_rate':sum(groups.values())/24 if len(main_summary)==24 and all(s['result_present'] for s in main_summary) else None,'records':summaries,'repeat_details':repeat_details,'known_navigation_native_steps':known_native,'known_native_replay_steps':known_replay,'known_private_integrations':known_private,'private_account_exact':bool(exact_private),'minimum_actual_clearance_m':min((s['minimum_actual_clearance_m'] for s in summaries if s['minimum_actual_clearance_m'] is not None),default=None),'verification_integrations':0,'training_updates':0,'algorithm_revisions':0,'scope':'Finite fixed blank8m/small actor/full-phase range-entry test under public3m startup prior; not arbitrary emergence, complex field, statistical superiority, mechanism attribution or infinite safety.'}
result['native_account_exact']=all(s['native_steps'] is not None for s in summaries)
result['replay_account_exact']=all(s['replay_steps'] is not None or s['native_steps']==0 for s in summaries)
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['records','repeat_details']},indent=2))
