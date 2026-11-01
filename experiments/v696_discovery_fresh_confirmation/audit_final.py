"""Independent zero-integration frozen24 functional/account audit."""
from pathlib import Path
import os,json,hashlib
import numpy as np
repo=Path(__file__).resolve().parents[2];src=Path(__file__).resolve().parent
root=repo/'runs/v696_discovery_fresh_confirmation';window=root/'confirmation01'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tasks=read(src/'TASK_LIST.json');completion=read(window/'COMPLETION.json');records=completion['results']
freeze=read(src/'CANDIDATE_FREEZE.json');sources=read(window/'CONFIRMATION_SOURCE_FREEZE.json')
checks={'all_preregistered_files_unchanged':all(sha(repo/p)==h for p,h in freeze['files'].items()),'all_runner_files_unchanged':all(sha(repo/p)==h for p,h in sources.items()),'exact_locked_task_list':read(window/'LOCKED_TASK_LIST.json')==tasks,'closed':completion['round_closed'],'declared_provisional_pass':completion['status']=='PROVISIONAL_FRESH24_AND_THREE_REPEATS_PASS','records_27':len(records)==27}
main=[x for x in records if x.get('repeat')is False];again=[x for x in records if x.get('repeat')is True]
checks['fixed24_no_replacements']=len(main)==24 and [x.get('task')for x in main]==tasks
summaries=[];all_audits=True;all_functional=True
for x in records:
    pair=repo/x['run'];r=read(pair/'geometry_memory/result.json');physical=read(pair/'INDEPENDENT_CANONICAL_AUDIT.json');replay=read(pair/'NATIVE_REPLAY_AUDIT.json');chain=read(pair/'DISCOVERY_CHAIN_AUDIT.json')
    passed=physical['status']=='ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS' and all(physical['checks'].values())
    passed &= read(pair/'ROUTE_COMMITMENT_AUDIT.json')['status']=='PASS' and read(pair/'PROJECTION_LEARNING_AUDIT.json')['status']=='PASS'
    passed &= replay['status']=='MATCHED_RECORDED_PUBLIC_STATES' and max(replay['maximum_full_public_qpos_error'],replay['maximum_full_public_qvel_error'],replay['maximum_public_mocap_error'])<=1e-8
    passed &= sha(pair/'scene_model.mjb')==replay['scene_model_sha256']
    passed &= r['physics_steps']==replay['replay_integration_steps']==8*r['public_steps']
    passed &= r['minimum_dynamic_native_clearance_m']>=.15 and r['root_mutations_outside_mjstep']==0
    passed &= r['contacts']['robot_obstacle_contact_records']==r['contacts']['robot_obstacle_penetration_records']==r['contacts']['unknown_contact_records']==0
    passed &= r['proposal_model_sha256']=='fc9d3132c912033e2ec04cd8ae1ce236c818c484d5b96961c6f3dc1b0548b527'
    passed &= x.get('task',{}).get('seed')==r['seed'] and x.get('task',{}).get('phase')==r['course_phase']
    functional=r['strict_safe_arrival']and chain['status']=='PASS'and all(chain['checks'].values())
    all_audits &= bool(passed)
    if x.get('repeat'):all_functional &= bool(functional)
    summaries.append({'name':x['name'],'task':x.get('task'),'repeat':x.get('repeat'),'strict_functional_arrival':bool(functional),'all_physical_causal_audits':bool(passed),'public_steps':r['public_steps'],'native_steps':r['physics_steps'],'replay_steps':replay['replay_integration_steps'],'private_integrations':r['prediction_steps'],'minimum_actual_clearance_m':r['minimum_dynamic_native_clearance_m'],'goal_distance_m':r['goal_distance_m']})
main_s=[s for s in summaries if s['repeat']is False]
groups={g:sum(s['strict_functional_arrival']for s in main_s if s['task']['initial_motion_direction']==g)for g in ['POSITIVE_Y','NEGATIVE_Y']}
checks['all_physical_causal_audits']=bool(all_audits)
checks['at_least23_strict']=sum(groups.values())>=23
checks['both_groups_at_least11']=min(groups.values())>=11
checks['three_preselected_repeats']=len(again)==3 and [x['task']['slot']for x in again]==[1,8,20] and all_functional
repeat_errors=[]
for x in again:
    slot=x['task']['slot'];base=next(y for y in main if y['task']['slot']==slot);a=repo/base['run'];b=repo/x['run']
    aa=[json.loads(s)for s in(a/'geometry_memory/v648_execution.jsonl').read_text().splitlines()];bb=[json.loads(s)for s in(b/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
    errors={k:float(np.max(abs(np.asarray([v[k]for v in aa])-np.asarray([v[k]for v in bb]))))if len(aa)==len(bb)else None for k in ['qpos_full','qvel_full','ctrl','mocap_pos']}
    good=all(v is not None and v<=1e-8 for v in errors.values())and read(b/'EXACT_REPEAT_AUDIT.json')['passed']and sha(a/'scene_model.mjb')==sha(b/'scene_model.mjb')
    repeat_errors.append({'slot':slot,'errors':errors,'passed':bool(good)})
checks['full_repeats_recomputed']=len(repeat_errors)==3 and all(x['passed']for x in repeat_errors)
result={'status':'FINITE_MOVING_DISCOVERY_CONFIRMATION_PASS'if all(checks.values())else'FAIL','checks':{k:bool(v)for k,v in checks.items()},'fixed_denominator':24,'strict_functional_arrivals':sum(groups.values()),'groups':groups,'repeat_errors':repeat_errors,'records':summaries,'navigation_native_steps':sum(x['native_steps']for x in summaries),'replay_native_steps':sum(x['replay_steps']for x in summaries),'private_integrations':sum(x['private_integrations']for x in summaries),'minimum_actual_clearance_m':min((x['minimum_actual_clearance_m']for x in summaries),default=None),'verification_integrations':0,'scope':'finite blank8m range-entry with public3m startup prior; not original complex field, arbitrary occlusion, statistics superiority or infinite safety'}
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='records'},indent=2));assert result['status']=='FINITE_MOVING_DISCOVERY_CONFIRMATION_PASS'
