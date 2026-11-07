"""One bounded interpretation of saved V797 states; no simulator imports."""
import ast, gzip, hashlib, json, os, signal
from pathlib import Path
import numpy as np

repo = Path(__file__).resolve().parents[2]
root = repo / 'runs/v797_retained_tail_mpc'
out = repo / 'runs/v797_saved_interpretation'
assert (repo / 'REVIEW_PENDING').exists()
read = lambda p: json.loads(p.read_text())
assert read(root / 'ROUND_WINDOW.json')['round_closed']
assert not out.exists()
os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('SAVED_INTERPRETATION_120S')))
signal.alarm(120)
source = repo / 'experiments/v793_complete_joint_navigation/serial_predictor.py'
tree = ast.parse(source.read_text())
node = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'project_to_segment_path')
namespace = {'np': np}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), namespace)
project = namespace[node.name]
reference = np.asarray(read(repo / 'experiments/v797_retained_tail_mpc/REFERENCE_PATH.json')['path'])
result = read(root / 'RESULT.json')
def error(pose):
    arc, contour, heading = project(np.asarray(pose).reshape(-1, 3), reference)
    yaw_error = abs((np.asarray(pose).reshape(-1, 3)[:, 2] - heading + np.pi) % (2*np.pi) - np.pi)
    return dict(arc_m=float(arc[-1]), contour_m=float(contour[-1]), heading_error_rad=float(yaw_error[-1]))
records = []
for r in result['records']:
    if r['selected'] is None:
        continue
    s = r['selected']; z = np.load(root / (s['label'] + '.npz'))
    q = z['initial_qpos']; yaw = np.arctan2(2*(q[3]*q[6]+q[4]*q[5]), 1-2*(q[5]**2+q[6]**2))
    checkpoints = {'initial': error([q[0], q[1], yaw])}
    for tick in [32, 64, 160, 328]:
        checkpoints[str(tick)] = error(z['poses'][tick-1])
    records.append(dict(refresh=r['refresh'], selected=s['label'], metrics=checkpoints,
                        parameters=s['parameters'], first_stage_native=64, executed_prefix_native=32))
last = read(root / ('S200_R%02d_CANDIDATES.json' % (len(result['records'])-1)))
best = max(last, key=lambda x: x['clearance_m'])
z = np.load(root / (best['label'] + '.npz'))
actual = []
with gzip.open(root / 'ACTUAL_NATIVE.jsonl.gz', 'rt') as f:
    for line in f:
        r = json.loads(line)
        if r['context'] != 'ORIGINAL_REPLAY' and not r['context'].endswith('_REPEAT'):
            actual.append(r)
q = np.asarray([r['qpos'] for r in actual]); v = np.asarray([r['qvel'] for r in actual])
yaw = np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]), 1-2*(q[:,5]**2+q[:,6]**2))
poses = np.c_[q[:,:2], yaw]
arc, contour, heading = project(poses, reference)
previous = np.load(root / 'S200_R00_I0_N47.npz')['initial_qpos'][:2]
delta = np.diff(np.vstack([previous, q[:,:2]]), axis=0)
signed = np.sum(delta*np.c_[np.cos(yaw), np.sin(yaw)], axis=1)
low = (np.linalg.norm(v[:,:2], axis=1) <= .025) & (np.linalg.norm(v[:,3:6], axis=1) <= .025)
initial_active = result['committed_replans'] * 32
old = read(repo / 'runs/v796_corridor_cem_continuation/RESULT.json')
summary = dict(status='SAVED_RETAINED_MPC_MECHANISM_INTERPRETATION_COMPLETE',
    new_model_initializations=0, new_integrations=0,
    source_projection_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    committed_replans=result['committed_replans'], attempted_replans=result['attempted_replans'],
    saved_proposals=result['attempted_replans']*192,
    actual_path_length_m=float(np.linalg.norm(delta,axis=1).sum()),
    reverse_projection_m=float(np.maximum(-signed,0).sum()),
    actual_final_xy=q[-1,:2].tolist(),
    actual_maximum_contour_m=float(contour.max()),
    actual_final_contour_m=float(contour[-1]),
    actual_final_heading_error_rad=float(abs((yaw[-1]-heading[-1]+np.pi)%(2*np.pi)-np.pi)),
    actual_main_simulated_s=len(actual)*.01,
    active_prefix_simulated_s=initial_active*.01,
    low_speed_active_prefix_s=float(low[:initial_active].sum()*.01),
    low_speed_whole_branch_s=float(low.sum()*.01),
    terminal_rejected_proposals=dict(count=len(last),
        static_pass=sum(r['static_minimum_m']>=.155 for r in last),
        self_pass=sum(r['self_margin_m']>=.002 for r in last),
        linear_pass=sum(r['terminal_speed_m_s']<=.025 for r in last),
        angular_pass=sum(r['terminal_angular_rad_s']<=.025 for r in last),
        causal_clearance_pass=sum(r['clearance_m']>=.155 for r in last),
        best=best,
        best_causal_minimum_tick=int(np.argmin(z['causal_values'])+1),
        best_causal_minimum_m=float(z['causal_values'].min())),
    full_tail_V796=dict(maximum_absolute_goal_progress_m=old['maximum_absolute_goal_progress_m'],
        reference_arc_progress_m=old['reference_arc_progress_m'],private_integrations=old['private_integrations']),
    retained_mpc_V797=dict(maximum_absolute_goal_progress_m=result['maximum_absolute_goal_progress_m'],
        reference_arc_progress_m=result['reference_arc_progress_m'],private_integrations=result['private_integrations']),
    old_V793_best_progress_difference_m=result['maximum_absolute_goal_progress_m']-result['old_best_absolute_progress_m'],
    private_work_ratio_to_V796=result['private_integrations']/old['private_integrations'],
    per_refresh_tracking=records,
    interpretation_limits=[
        'One already observed checkpoint, not independent navigation success-rate evidence.',
        'V796 and V797 share first 192 proposals and first 32 native states exactly; later states, counts and random arrays differ.',
        'The cost penalizes terminal contour/heading only; the saved prefix-versus-tail metrics characterize the selected schedules, not a counterfactual controller.',
        'Late predicted turns, distribution reset and missing nominal warm-start are hypotheses for another preregistered test, not proven causes.',
        'All final finite proposals failing causal future clearance does not prove all physical controls infeasible.',
        'A static collision-free reference alone is not a causal future-clearance certificate.'
    ])
out.mkdir()
(out / 'RESULT.json').write_text(json.dumps(summary, indent=2)+'\n')
signal.alarm(0)
print(json.dumps({k:v for k,v in summary.items() if k != 'per_refresh_tracking'}))
