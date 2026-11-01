"""Zero-integration accounting and cause analysis after frozen V696 t0 failure."""
from pathlib import Path
import json,hashlib,ast,fcntl
repo=Path(__file__).resolve().parents[2];read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=repo/'experiments/v696_discovery_fresh_confirmation';root=repo/'runs/v696_discovery_fresh_confirmation';window=root/'confirmation01';childroot=repo/'runs/v695_discovery_verified_fixture'
tasks=read(src/'TASK_LIST.json');original=read(window/'COMPLETION.json');roundstate=read(root/'ROUND_WINDOW.json');freeze=read(src/'CANDIDATE_FREEZE.json')
assert roundstate['round_closed'] and roundstate['navigation_attempts']==0 and original['status']=='STOPPED_EXCEPTION'
records=[]
for task in tasks:
    pair=childroot/('fresh01_t0_slot%02d'%task['slot'])/'paired';complete=pair/'completion.json'
    result=read(complete)if complete.exists()else None
    records.append({'task':task,'preflight_attempted':result is not None,'preflight_status':None if result is None else result['status'],'preflight_audit_passed':(pair/'INITIAL_UNSEEN_AUDIT.json').exists()and read(pair/'INITIAL_UNSEEN_AUDIT.json')['status']=='PASS','arena_constructed':(pair/'ARENA_CONSTRUCTION.json').exists(),'navigation_executed':False,'original_error':None if result is None else result.get('error')})
failure=next(x for x in records if x['preflight_status']=='FAILED');assert failure['task']['slot']==12
message=failure['original_error']['message'];metrics=json.loads(message.split(':',1)[1])
text=(repo/'current/runner.py').read_text();tree=ast.parse(text);constants={}
for node in ast.walk(tree):
    if isinstance(node,ast.Assign)and isinstance(node.value,(ast.Constant,ast.Num)):
        for name in node.targets:
            if isinstance(name,ast.Name)and name.id in ['MIN_STRAIGHT','MAX_STRAIGHT','MIN_PATH','ENDPOINT_TOL']:constants[name.id]=ast.literal_eval(node.value)
predicates={'straight_in_legacy_range':constants['MIN_STRAIGHT']<=metrics['straight_distance_m']<=constants['MAX_STRAIGHT'],'path_long_enough':metrics['global_path_length_m']>=constants['MIN_PATH'],'start_endpoint':metrics['path_start_error_m']<=constants['ENDPOINT_TOL'],'goal_endpoint':metrics['path_goal_error_m']<=constants['ENDPOINT_TOL']}
assert predicates=={'straight_in_legacy_range':False,'path_long_enough':True,'start_endpoint':True,'goal_endpoint':True}
log=(window/'fresh01_t0_slot12.console').read_text();line=next(line for line in log.splitlines()if line.startswith('LONG_GOAL_RESET_SELECTED '));selected=json.loads(line.split(' ',1)[1])
assert selected['straight_distance_m']<=constants['MAX_STRAIGHT']<metrics['straight_distance_m']
checks={'all_frozen_files_unchanged':all(sha(repo/p)==h for p,h in freeze['files'].items()),'original_results_empty':original['results']==[],'12attempts_11passed_1failed':sum(x['preflight_attempted']for x in records)==12 and sum(x['preflight_audit_passed']for x in records)==11,'remaining12preflights_not_attempted':sum(not x['preflight_attempted']for x in records)==12,'all24navigation_not_started':not any((childroot/('fresh01_slot%02d'%t['slot'])).exists()for t in tasks),'failed_before_new_arena':not failure['arena_constructed'],'legacy_range_only_predicate_rejection':not predicates['straight_in_legacy_range']and all(v for k,v in predicates.items()if k!='straight_in_legacy_range'),'independent_full_gate_failed':read(root/'FINAL_INDEPENDENT_AUDIT.json')['status']=='FAIL'}
lock=(repo/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN);checks['no_phase_simulation_holds_execution_lock']=True
assert all(checks.values()),checks
out={'status':'CLOSED_PREFLIGHT_BLOCKED_NOT_CONFIRMED','checks':checks,'frozen_task_denominator':24,'preflight_attempted':12,'preflight_passed':11,'preflight_failed':1,'preflight_unattempted':12,'navigation_tasks_executed':0,'navigation_tasks_unexecuted':24,'confirmation_repeats_executed':0,'confirmation_repeats_unexecuted':3,'navigation_success_rate':None,'navigation_success_rate_reason':'No fresh navigation was executed; do not report zero-of24 navigation success rate.','new_confirmation_navigation_native_steps':0,'new_confirmation_private_integrations':0,'new_confirmation_replay_native_steps':0,'training_updates':0,'failure_task':failure['task'],'legacy_sample_continuous_distance_m':selected['straight_distance_m'],'legacy_grid_aligned_distance_m':metrics['straight_distance_m'],'legacy_constants':constants,'legacy_gate_predicates':predicates,'initial_clearance_gate_passed':True,'actual8m_arena_built_for_failed_slot':False,'scope':'source-recomputed initialization gate; not dynamic control collision or global infeasibility','records':records,'all_prior_failures_and_unknown_ranges_preserved':True,'original_completion_unchanged':sha(window/'COMPLETION.json'),'verification_integrations':0}
(root/'FINAL_ACCOUNT_DIAGNOSIS.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items()if k not in ['records','checks']},indent=2))
