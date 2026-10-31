"""Independent read-only final gate; partial evidence cannot pass. Zero physics."""
import gzip, hashlib, json
from pathlib import Path
import numpy as np
repo = Path(__file__).resolve().parents[2]
root = repo/'runs/v652_static_confirmation'
window = root/'confirmation_window01'
def read(p, default=None):
    return json.loads(p.read_text()) if p.exists() else default
selection = read(window/'SELECTION_FREEZE.json',{})
tasks = selection.get('tasks',[])
outcomes = read(window/'CONFIRMATION_RESULTS.json',[])
ledger = read(window/'LEDGER.json',[])
completion = read(window/'COMPLETION.json',{})
freeze = read(window/'SOURCE_FREEZE.json',{})
timebox = read(window/'WINDOW.json',{})
preflights = [x for x in ledger if x['feasibility_only']]
expected = []
for scene in ['single_event','legacy_two']:
    expected += [x for x in preflights if x['scene'] == scene and x['feasibility'] and x['feasibility']['eligible']][:12]
expected.sort(key=lambda x:x['seed'])
selection_ok = bool(tasks and [(x['seed'],x['scene']) for x in tasks] == [(x['seed'],x['scene']) for x in expected] and [x['seed'] for x in preflights] == list(range(94000001,94000001+len(preflights))) and len(preflights) <= 360)
checks_per_run = []
def audit(name):
    pair = root/name/'paired'
    branch = pair/'geometry_memory'
    result = read(branch/'result.json')
    native = read(pair/'NATIVE_REPLAY_AUDIT.json')
    protocol = read(pair/'STATIC_PROTOCOL.json')
    snapshot = pair.parent/'source_snapshot'
    source_hashes = read(snapshot/'SHA256.json',{})
    if not result or not native or not protocol:
        checks_per_run.append({'name':name,'passed':False,'reason':'missing result/replay/protocol'})
        return False
    digest = hashlib.sha256()
    with gzip.open(branch/'contacts.jsonl.gz','rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):digest.update(block)
    trace = read(branch/'trace.json',[])
    admission = [json.loads(line) for line in (branch/'model_admission.jsonl').read_text().splitlines()]
    plans = {int(f.stem.split('_')[-1]) for f in branch.glob('planning_*.json')}
    transition_file = branch/'gear_transitions.jsonl'
    switches = {json.loads(line)['step'] for line in transition_file.read_text().splitlines()} if transition_file.exists() else set()
    unchecked_cusps = [x['step'] for prior,x in zip(admission[:-1],admission[1:]) if x['active_gear'] != prior['active_gear'] and x['step'] not in plans and x['step'] not in switches]
    actual_model_digest = hashlib.sha256((pair/'scene_model.mjb').read_bytes()).hexdigest()
    safe = bool(not unchecked_cusps and len(admission) == len(trace) and all(x['hidden_world_geometry_used'] is False for x in admission) and actual_model_digest == protocol['full_model_sha256'] == native['scene_model_sha256'] and source_hashes == freeze and all(hashlib.sha256((snapshot/n).read_bytes()).hexdigest() == h for n,h in freeze.items()) and digest.hexdigest() == result['contacts']['contact_log_content_sha256'] and len(trace) == result['public_steps'] and result['physics_steps'] == 8*len(trace) and result['self_geometry_checked_native_ticks'] == result['physics_steps'] and result['minimum_actual_self_domain_margin_m'] >= 0 and result['root_mutations_outside_mjstep'] == 0 and result['static_obstacle_pose_unchanged'] and len(protocol['physical_unknown_obstacles']) == (1 if protocol['scene'] == 'single_event' else 2) and protocol['model_sha256'] == '4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f' and all(result['contacts'][k] == 0 for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records']) and native['status'] == 'MATCHED_RECORDED_PUBLIC_STATES' and native['replay_integration_steps'] == result['physics_steps'] and native['maximum_full_public_qpos_error'] <= 1e-8 and native['maximum_full_public_qvel_error'] <= 1e-8 and native['minimum_reconstructed_native_actual_axis_AABB_clearance_m'] is not None and native['minimum_reconstructed_native_actual_axis_AABB_clearance_m'] >= .15-1e-8 and native['reconstructed_native_states_below_015'] == 0 and native['replay_obstacle_contact_records'] == 0)
    checks_per_run.append({'name':name,'passed':safe,'native_clearance_min_m':native['minimum_reconstructed_native_actual_axis_AABB_clearance_m'],'native_steps':result['physics_steps'],'unchecked_cusp_switch_steps':unchecked_cusps})
    return safe
actual_successes = []
for row in outcomes:
    result = row.get('result')
    task = next((x for x in tasks if x['seed'] == row['seed'] and x['scene'] == row['scene']),None)
    protocol = read(root/row['name']/'paired/STATIC_PROTOCOL.json',{})
    same = bool(task and protocol.get('full_model_sha256') == task['scene_model_sha256'] and protocol.get('seed') == row['seed'] and protocol.get('scene') == row['scene'])
    safe = audit(row['name'])
    actual_successes.append(bool(result and result['goal_distance_m'] <= .45 and result['strict_safe_arrival'] and same and safe))
repeat_checks = []
for seed,scene in [(93000074,'legacy_two'),(93000045,'single_event'),(91000002,'single_event')]:
    name = f'repeat_{seed}_{scene}'
    pair = root/name/'paired'
    if not (pair/'geometry_memory/result.json').exists():
        repeat_checks.append({'name':name,'passed':False,'reason':'not completed'});continue
    safe = audit(name)
    base = repo/'runs/v651_static_progress'/f'dev29_seed{seed}_{scene}/paired'
    new,old = read(pair/'geometry_memory/result.json'),read(base/'geometry_memory/result.json')
    old_rows = [json.loads(s) for s in (base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
    new_rows = [json.loads(s) for s in (pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
    errors = {key:float(np.max(np.abs(np.array([r[key] for r in old_rows])-np.array([r[key] for r in new_rows])))) if len(old_rows) == len(new_rows) else None for key in ['qpos_full','qvel_full','ctrl']}
    same = bool(safe and new['strict_safe_arrival'] and new['outcome'] == old['outcome'] and new['normalized_initial_state_hash'] == old['normalized_initial_state_hash'] and new['contacts']['contact_log_content_sha256'] == old['contacts']['contact_log_content_sha256'] and all(v is not None and v <= 1e-8 for v in errors.values()) and read(pair/'STATIC_PROTOCOL.json')['full_model_sha256'] == read(base/'STATIC_PROTOCOL.json')['full_model_sha256'])
    repeat_checks.append({'name':name,'passed':same,'maximum_full_state_errors':errors})
classes = {s:sum(ok for row,ok in zip(outcomes,actual_successes) if row['scene'] == s) for s in ['single_event','legacy_two']}
checks = {'execution_completed':bool(completion),'selection_fixed_and_first_eligible_per_class':selection_ok,'24_distinct_tasks':len(tasks) == 24 and len({x['seed'] for x in tasks}) == 24,'24_completed_records':len(outcomes) == 24,'at_least_23_audited_arrivals':sum(actual_successes) >= 23,'single_at_least_11':classes['single_event'] >= 11,'two_at_least_11':classes['legacy_two'] >= 11,'all_27_native_and_source_records':len(checks_per_run) == 27 and all(x['passed'] for x in checks_per_run),'three_full_state_repeats_match':len(repeat_checks) == 3 and all(x['passed'] for x in repeat_checks),'execution_within_timebox':bool(completion and timebox and completion['elapsed_s'] <= timebox['limit_s']),'current_source_unchanged':bool(freeze) and all(hashlib.sha256((repo/'experiments/v652_static_confirmation'/n).read_bytes()).hexdigest() == h for n,h in freeze.items())}
out = {'static_engineering_acceptance_passed':all(checks.values()),'checks':checks,'completed_confirmation_attempts':len(outcomes),'strict_audited_arrivals':sum(actual_successes),'class_successes':classes,'runs':checks_per_run,'repeats':repeat_checks,'simulation_steps':0,'training_updates':0,'dynamic_started':False,'scope':'finite selected static cylinder benchmark; independent read-only recomputation, not general probabilistic/continuous-time/real-time/real-robot certification'}
dump = root/'INDEPENDENT_ACCEPTANCE_AUDIT.json'
dump.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
