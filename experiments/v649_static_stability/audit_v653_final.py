"""Independent audit of logging-only continuation, retaining original failure.
No simulation, no mutation of original outcomes or frozen candidate code.
"""
import gzip,hashlib,json
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2]
prior=repo/'runs/v652_static_confirmation/confirmation_window01'
root=repo/'runs/v653_static_log_recovery'
window=root/'continuation01'
def read(p,default=None):return json.loads(p.read_text())if p.exists()else default
selection=read(prior/'SELECTION_FREEZE.json');tasks=selection['tasks']
outcomes=read(window/'CONFIRMATION_RESULTS.json',[])
completion=read(window/'COMPLETION.json',{})
old_freeze=read(prior/'SOURCE_FREEZE.json');new_freeze=read(window/'SOURCE_FREEZE.json',{})
original=repo/'experiments/v652_static_confirmation';fixed=repo/'experiments/v653_static_log_recovery'
old="if candidate is None and preferred is not None:candidate,stats=preferred,preferred_stats\n                            stats['preferred_search']=preferred_stats"
new="if candidate is None and preferred is not None:candidate,stats=preferred,dict(preferred_stats)\n                            stats['preferred_search']=dict(preferred_stats)"
equivalence={}
for name in old_freeze:
    if name in ['execute_confirmation.py','replay_native_audit.py']:continue
    copied=(fixed/name).read_text()
    if name=='run_static.py':copied=copied.replace("/'v653_static_log_recovery'/a.name","/'v652_static_confirmation'/a.name").replace(new,old)
    equivalence[name]=hashlib.sha256(copied.encode()).hexdigest()==old_freeze[name]
all_frozen=all(hashlib.sha256((original/n).read_bytes()).hexdigest()==h for n,h in old_freeze.items())and bool(new_freeze)and all(hashlib.sha256((fixed/n).read_bytes()).hexdigest()==h for n,h in new_freeze.items())
records=[]
def audit_pair(pair,interrupted=False):
    cell=pair/'geometry_memory'
    result=read(cell/('interrupted.json'if interrupted else'result.json'))
    native=read(pair/'NATIVE_REPLAY_AUDIT.json')
    protocol=read(pair/'STATIC_PROTOCOL.json')
    snapshot=pair.parent/'source_snapshot'
    expected=old_freeze if pair.parent.parent.name=='v652_static_confirmation'else new_freeze
    snapshot_hashes=read(snapshot/'SHA256.json',{})
    if not result or not native or not protocol:
        records.append({'pair':str(pair.relative_to(repo)),'passed':False,'reason':'missing result/interruption/native/protocol'});return False
    digest=hashlib.sha256()
    with gzip.open(cell/'contacts.jsonl.gz','rb')as stream:
        for b in iter(lambda:stream.read(1048576),b''):digest.update(b)
    trace=read(cell/'trace.json',[])
    execution=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()]
    admission=[json.loads(s)for s in(cell/'model_admission.jsonl').read_text().splitlines()]
    plans={int(p.stem.split('_')[-1])for p in cell.glob('planning_*.json')}
    transition=cell/'gear_transitions.jsonl'
    switches={json.loads(s)['step']for s in transition.read_text().splitlines()}if transition.exists()else set()
    bypasses=[x['step']for a,x in zip(admission[:-1],admission[1:])if x['active_gear']!=a['active_gear']and x['step']not in plans and x['step']not in switches]
    actual_model=hashlib.sha256((pair/'scene_model.mjb').read_bytes()).hexdigest()
    checks={'frozen_snapshot':snapshot_hashes==expected and all(hashlib.sha256((snapshot/n).read_bytes()).hexdigest()==h for n,h in expected.items()),'contact_digest':digest.hexdigest()==result['contacts']['contact_log_content_sha256'],'zero_obstacle_contacts':all(result['contacts'][k]==0 for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records']),'public_and_native_counts':len(trace)==len(execution)==len(admission)==result['public_steps']and result['physics_steps']==8*len(trace),'state_replay_match':native['status']=='MATCHED_RECORDED_PUBLIC_STATES'and native['maximum_full_public_qpos_error']<=1e-8 and native['maximum_full_public_qvel_error']<=1e-8 and native['replay_integration_steps']==result['physics_steps'],'native_clearance':native['minimum_reconstructed_native_actual_axis_AABB_clearance_m']is not None and native['minimum_reconstructed_native_actual_axis_AABB_clearance_m']>=.15-1e-8 and native['reconstructed_native_states_below_015']==0 and native['replay_obstacle_contact_records']==0,'native_self_domain':native['minimum_reconstructed_self_domain_margin_m']is not None and native['minimum_reconstructed_self_domain_margin_m']>=0,'model':actual_model==native['scene_model_sha256']==protocol['full_model_sha256']and protocol['model_sha256']=='4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f','unknown_count':len(protocol['physical_unknown_obstacles'])==(1 if protocol['scene']=='single_event' else 2),'causal_admission':all(x['hidden_world_geometry_used']is False for x in admission),'cusp_gate':not bypasses}
    if interrupted:
        done=read(pair/'completion.json',{});checks['original_logged_interruption_preserved']=result['strict_safe_arrival']is False and done.get('error',{}).get('type')=='RecursionError'and not(cell/'result.json').exists()and result['public_steps']==19 and result['physics_steps']==152
    else:
        checks['live_self_and_static_audit']=result['self_geometry_checked_native_ticks']==result['physics_steps']and result['minimum_actual_self_domain_margin_m']>=0 and result['static_obstacle_pose_unchanged']and result['root_mutations_outside_mjstep']==0
    passed=all(checks.values());records.append({'pair':str(pair.relative_to(repo)),'passed':passed,'checks':checks,'interrupted_prefix_only':interrupted,'public_steps':result['public_steps'],'native_steps':result['physics_steps'],'minimum_native_clearance_m':native['minimum_reconstructed_native_actual_axis_AABB_clearance_m']});return passed
successes=[]
for i,row in enumerate(outcomes):
    task=tasks[i]if i<len(tasks)else{}
    pair=repo/row['run_root']/row['name']/'paired'
    interrupted=row['seed']==94000040 and row['result']is None
    safe=audit_pair(pair,interrupted)
    model=read(pair/'STATIC_PROTOCOL.json',{}).get('full_model_sha256')
    same=row['seed']==task.get('seed')and row['scene']==task.get('scene')and model==task.get('scene_model_sha256')
    result=row['result']
    successes.append(bool(safe and same and result and result['strict_safe_arrival']and result['goal_distance_m']<=.45))
repeat_checks=[]
for seed,scene in [(93000074,'legacy_two'),(93000045,'single_event'),(91000002,'single_event')]:
    pair=root/f'repeat_{seed}_{scene}'/'paired';base=repo/'runs/v651_static_progress'/f'dev29_seed{seed}_{scene}/paired'
    current=read(pair/'geometry_memory/result.json')
    if not current:repeat_checks.append({'seed':seed,'scene':scene,'passed':False,'reason':'not completed'});continue
    safe=audit_pair(pair)
    old_result=read(base/'geometry_memory/result.json')
    a=[json.loads(s)for s in(base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
    b=[json.loads(s)for s in(pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
    errors={key:float(np.max(np.abs(np.array([r[key]for r in a])-np.array([r[key]for r in b]))))if len(a)==len(b)else None for key in ['qpos_full','qvel_full','ctrl']}
    same=bool(safe and current['strict_safe_arrival']and current['outcome']==old_result['outcome']and current['normalized_initial_state_hash']==old_result['normalized_initial_state_hash']and current['contacts']['contact_log_content_sha256']==old_result['contacts']['contact_log_content_sha256']and all(v is not None and v<=1e-8 for v in errors.values())and read(pair/'STATIC_PROTOCOL.json')['full_model_sha256']==read(base/'STATIC_PROTOCOL.json')['full_model_sha256'])
    repeat_checks.append({'seed':seed,'scene':scene,'passed':same,'maximum_full_state_error':errors})
screened=read(prior/'LEDGER.json',[]);expected=[]
for scene in ['single_event','legacy_two']:expected += [x for x in screened if x['feasibility_only']and x['scene']==scene and x['feasibility']and x['feasibility']['eligible']][:12]
expected.sort(key=lambda x:x['seed'])
reference_ok=len(expected)==24 and all(x['feasibility']['search']['minimum_clearance_m']>=.155-1e-8 and x['feasibility']['continuous_polygonal_pose_clearance_lower_bound_m']>=.15 and x['feasibility']['reference_goal_distance_m']<=.28 for x in expected)
classes={s:sum(ok for row,ok in zip(outcomes,successes)if row['scene']==s)for s in ['single_event','legacy_two']}
origin=read(prior/'WINDOW.json');old_done=read(prior/'COMPLETION.json')
checks={'original_batch_stopped_and_failure_preserved':old_done['static_engineering_acceptance_passed']is False and len(outcomes)>=5 and outcomes[4]['result']is None and outcomes[4]['strict_success']is False,'same_locked24_selection':len(tasks)==24 and[(x['seed'],x['scene'])for x in tasks]==[(x['seed'],x['scene'])for x in expected],'registered_reference_requirements':reference_ok,'decision_source_equivalent':bool(equivalence)and all(equivalence.values()),'all_sources_frozen':all_frozen,'24_attempt_records':len(outcomes)==24,'at_least23_strict_audited_arrivals':sum(successes)>=23,'single_at_least11':classes['single_event']>=11,'two_at_least11':classes['legacy_two']>=11,'all27_full_or_actual_prefix_physical_audits':len(records)==27 and all(x['passed']for x in records),'three_full_state_repeats':len(repeat_checks)==3 and all(x['passed']for x in repeat_checks),'original_deadline_not_reset':bool(completion and completion['elapsed_from_original_origin_s']<=origin['limit_s']and read(window/'WINDOW.json')['absolute_deadline_unix']==origin['absolute_deadline_unix'])}
out={'static_engineering_acceptance_passed':all(checks.values()),'checks':checks,'strict_audited_arrivals':sum(successes),'completed_attempt_records':len(outcomes),'class_successes':classes,'original_logging_interruption_permanently_one_non_success':True,'source_equivalence':equivalence,'runs':records,'repeats':repeat_checks,'simulation_steps':0,'dynamic_started':False,'training_updates':0,'scope':'same fixed selected finite benchmark with a declared non-decision diagnostic repair; not a pristine single-runner run, general safety or statistical superiority certificate'}
(root/'INDEPENDENT_ACCEPTANCE_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
