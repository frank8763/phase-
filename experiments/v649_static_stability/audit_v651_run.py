"""Read-only development audit: pairing, source snapshot, cusp transitions, safety."""
import argparse, gzip, hashlib, json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('run')
a = p.parse_args()
repo = Path(__file__).resolve().parents[2]
run = Path(a.run).resolve()
pair = run/'paired'
cell = pair/'geometry_memory'
result = json.loads((cell/'result.json').read_text())
trace = json.loads((cell/'trace.json').read_text())
admission = [json.loads(s) for s in (cell/'model_admission.jsonl').read_text().splitlines()]
plans = {int(f.stem.split('_')[-1]) for f in cell.glob('planning_*.json')}
transition_file = cell/'gear_transitions.jsonl'
transitions = [json.loads(s) for s in transition_file.read_text().splitlines()] if transition_file.exists() else []
logged_switches = {x['step'] for x in transitions}
bypasses = [x['step'] for previous, x in zip(admission[:-1],admission[1:]) if x['active_gear'] != previous['active_gear'] and x['step'] not in plans and x['step'] not in logged_switches]
snapshot = run/'source_snapshot'
source_hashes = json.loads((snapshot/'SHA256.json').read_text())
source_verified = all(hashlib.sha256((snapshot/name).read_bytes()).hexdigest() == digest for name,digest in source_hashes.items())
candidate_path = repo/'experiments/v651_static_progress'/('CANDIDATE_29.json' if result['source_revision'].startswith('progress_29') else 'CANDIDATE_28.json')
candidate = json.loads(candidate_path.read_text())['source_sha256']
source_matches_candidate = all(source_hashes.get(name) == digest for name,digest in candidate.items())
protocol = json.loads((pair/'STATIC_PROTOCOL.json').read_text())
seed, scene = result['seed'], protocol['scene']
baseline = repo/'runs/v650_static_acceptance'/f'confirm_{seed}_{scene}/paired/geometry_memory/result.json'
same_initial_state = None
if baseline.exists():
    previous = json.loads(baseline.read_text())
    same_initial_state = previous['normalized_initial_state_hash'] == result['normalized_initial_state_hash']
contact_digest = hashlib.sha256()
with gzip.open(cell/'contacts.jsonl.gz','rb') as stream:
    for block in iter(lambda:stream.read(1048576),b''):
        contact_digest.update(block)
native = json.loads((pair/'NATIVE_REPLAY_AUDIT.json').read_text())
checks = {
    'source_snapshot_verified':source_verified,
    'source_matches_registered_candidate':source_matches_candidate,
    'same_initial_state_as_confirmation_failure':same_initial_state,
    'contact_digest_matches':contact_digest.hexdigest() == result['contacts']['contact_log_content_sha256'],
    'actual_native_steps_match':len(trace) == result['public_steps'] and result['physics_steps'] == 8*len(trace),
    'all_contacts_zero':all(result['contacts'][k] == 0 for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records']),
    'native_replay_matched':native['status'] == 'MATCHED_RECORDED_PUBLIC_STATES' and native['maximum_full_public_qpos_error'] <= 1e-8 and native['maximum_full_public_qvel_error'] <= 1e-8,
    'native_clearance_floor_met':native['minimum_reconstructed_native_actual_axis_AABB_clearance_m'] is not None and native['minimum_reconstructed_native_actual_axis_AABB_clearance_m'] >= .15-1e-8 and native['reconstructed_native_states_below_015'] == 0,
    'self_domain_all_ticks':result['minimum_actual_self_domain_margin_m'] >= 0 and result['self_geometry_checked_native_ticks'] == result['physics_steps'],
    'static_and_integrated_only':result['static_obstacle_pose_unchanged'] and result['root_mutations_outside_mjstep'] == 0,
    'no_unchecked_same_plan_cusp_switch':not bypasses,
}
out = {'run':run.name,'source_revision':result['source_revision'],'strict_safe_arrival':result['strict_safe_arrival'],'checks':checks,'unchecked_cusp_switch_steps':bypasses,'checks_passed':all(v is not False for v in checks.values()),'public_steps':result['public_steps'],'goal_distance_m':result['goal_distance_m'],'minimum_native_reconstructed_clearance_m':native['minimum_reconstructed_native_actual_axis_AABB_clearance_m'],'simulation_steps_in_auditor':0,'static_acceptance_passed':False,'scope':'development only; original confirmation failures remain failures'}
(pair/'DEVELOPMENT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
