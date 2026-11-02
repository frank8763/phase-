"""Independent persisted-evidence closure for the three fixed field development routes."""
import gzip,hashlib,json,sys
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v706_global_field_qualification';window=root/'development01'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
completion=read(window/'COMPLETION.json');w=read(root/'ROUND_WINDOW.json');plan=read(own/'EXECUTION_PLAN.json');freeze=read(own/'CANDIDATE_FREEZE.json');records=completion['results']
checks={'all_frozen_inputs':all(sha(repo/n)==h for n,h in freeze['files'].items()),'closed':w['round_closed'] and completion['round_closed'],'fixed_window':w['limit_s']==5400 and abs(w['absolute_deadline_unix']-w['started_unix']-5400)<1e-6 and w['absolute_deadline_unix']<=1793664000. and w['elapsed_s']<=5405,'exact_schedule':len(records)==6 and [{k:x[k] for k in item} for x,item in zip(records,plan)]==plan,'driver_completed':completion['status']=='FIELD_DEVELOPMENT_AND_REPEATS_COMPLETE','no_training_or_extra_navigation':w['navigation_attempts']<=6 and w['training_updates']==w['algorithm_revisions']==0,'v705_closed_prerequisite':read(repo/'runs/v705_rpccr_prospective_pairs/FINALIZED.json')['status']=='PROSPECTIVE_COMPUTE_EVIDENCE_COMPLETE'}
details=[];nav=replay=private=0;nav_exact=replay_exact=private_exact=True
for row in records:
    pair=repo/row['run'];cell=pair/'geometry_memory';result=read(cell/'result.json') if (cell/'result.json').exists() else read(cell/'interrupted.json') if (cell/'interrupted.json').exists() else {}
    rr=read(pair/'NATIVE_REPLAY_AUDIT.json') if (pair/'NATIVE_REPLAY_AUDIT.json').exists() else None
    nav+=result.get('physics_steps',0);private+=result.get('prediction_steps',0);replay+=(rr or {}).get('replay_integration_steps',0)
    nav_exact &= 'physics_steps' in result;private_exact &= 'prediction_steps' in result;replay_exact &= rr is not None or result.get('physics_steps')==0
    local={}
    for filename,status in [('INDEPENDENT_CANONICAL_AUDIT.json','ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS'),('ROUTE_COMMITMENT_AUDIT.json','PASS'),('PROJECTION_LEARNING_AUDIT.json','PASS'),('SAVED_TAIL_GEOMETRY_AUDIT.json','ALL_SAVED_TAIL_GEOMETRY_DIRECTION_SCHEDULE_PASS'),('SHADOW_MODE_AUDIT.json','PASS'),('v699_discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json','PASS')]:
        f=pair/filename;a=read(f) if f.exists() else {};local[filename]=a.get('status')==status and all(a.get('checks',{}).values())
    local['strict_full_chain']=result.get('strict_safe_arrival') is True and row.get('functional_passed') is True and result.get('outcome')=='GOAL'
    local['complete_replay']=rr is not None and rr.get('status')=='MATCHED_RECORDED_PUBLIC_STATES' and rr.get('replay_integration_steps')==result.get('physics_steps')==result.get('public_steps',-1)*8 and max(rr.get('maximum_full_public_qpos_error',1),rr.get('maximum_full_public_qvel_error',1),rr.get('maximum_public_mocap_error',1))<=1e-8
    if row['role']=='DEVELOPMENT_REPEAT':
        f=pair/'EXACT_COMPARISON_AUDIT.json';a=read(f) if f.exists() else {};local['exact_same_version_repeat']=a.get('passed') is True and all(a.get('checks',{}).values())
    details.append({'name':row['name'],'role':row['role'],'case_id':row['task']['case_id'],'seed':row['task']['seed'],'checks':local,'passed':all(local.values()),'outcome':result.get('outcome','UNKNOWN_OR_UNEXECUTED'),'public_steps':result.get('public_steps'),'goal_distance_m':result.get('goal_distance_m'),'minimum_native_clearance_m':result.get('minimum_dynamic_native_clearance_m'),'native_steps':result.get('physics_steps'),'private_integrations':result.get('prediction_steps'),'replay_steps':None if rr is None else rr.get('replay_integration_steps'),'wall_seconds':result.get('elapsed_s')})
checks['all6_full_physical_causal_evidence']=len(details)==6 and all(x['passed'] for x in details)
f=window/'PREFLIGHT_INDEPENDENT_AUDIT.json';pre=read(f) if f.exists() else {};checks['all3_fixed_preflights']=pre.get('status')=='PASS' and pre.get('tasks')==3 and all(x['passed'] for x in pre.get('details',[]))
out={'status':'FIELD_DEVELOPMENT_AND_THREE_REPEATS_PASS' if all(checks.values()) else 'FIELD_DEVELOPMENT_NOT_PASSED','checks':checks,'records':details,'navigation_native_steps':nav,'replay_native_steps':replay,'private_integrations':private,'native_account_exact':bool(nav_exact),'replay_account_exact':bool(replay_exact),'private_account_exact':bool(private_exact),'unique_development_tasks_executed':sum(x['role']=='DEVELOPMENT_MAIN' for x in details),'confirmed_new_tasks':0,'unexecuted':[x['name'] for x in plan if x['name'] not in {r['name'] for r in records}],'training_updates':0,'new_integrations_in_audit':0,'scope':'Three predeclared routes in one original known field layout, development only. Not independent24 confirmation or algorithm superiority.'}
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='records'}))
