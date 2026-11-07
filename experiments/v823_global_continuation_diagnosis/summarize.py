"""Read-only source/pose linkage and scientific figure; no simulator import."""
import gzip
import hashlib
import importlib.abc
import json
import math
import os
import sys
from pathlib import Path

os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
class NoPhysics(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name == 'mujoco' or name.startswith('mujoco.'):
            raise RuntimeError('SUMMARY_FORBIDS_MODELS_AND_INTEGRATIONS')
sys.meta_path.insert(0, NoPhysics())
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

repo = Path(__file__).resolve().parents[2]
root = repo / 'runs/v823_global_continuation_diagnosis'
cell = repo / 'runs/v821_norm_route_development/main_slot02/paired/geometry_memory'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert not (root / 'EVIDENCE_CHECK.json').exists()
guard = (repo / 'REVIEW_PENDING').read_bytes()
freeze = read(Path(__file__).parent / 'INPUT_FREEZE.json')['files']
assert all(sha(repo / name) == expected for name, expected in freeze.items())
completion = read(root / 'renewal_probe/COMPLETION.json')
assert completion['status'] == 'FIXED_RENEWAL_REFERENCE_DIAGNOSIS_COMPLETE'
assert completion['original_sources_and_inputs_unchanged'] and completion['review_guard_bytes_unchanged']
packets = {}
with gzip.open(cell / 'sensor_packets.jsonl.gz', 'rt') as f:
    for line in f:
        packet = json.loads(line)
        if packet['step'] in (282, 500): packets[packet['step']] = packet
revalidations = {}
for line in (cell / 'route_revalidation.jsonl').open():
    record = json.loads(line)
    if record['step'] in (282, 500): revalidations[record['step']] = record
old = read(cell / 'planning_0265.json')
rows = []
for step in (282, 500):
    saved = read(root / f'renewal_probe/INPUT_{step:04d}.json')
    query = read(root / f'renewal_probe/ORIGINAL_SEARCH_{step:04d}.json')
    packet = packets[step]
    pose = np.asarray(saved['pose'])
    delta = np.r_[pose[:2] - packet['xy'], (pose[2]-packet['yaw']+math.pi)%(2*math.pi)-math.pi]
    error = float(np.max(abs(delta)))
    assert error <= 1e-12
    assert saved['motion_state']['time'] == packet['time']
    route = revalidations[step]
    assert route['last_plan'] == 265 and not route['current_route_invalid']
    assert np.array_equal(route['reference_path'], old['path'])
    assert query['selected_status'] == 'GLOBAL_GOAL_PATH' and query['remaining_goal_m'] < .28
    stats = query['records'][-1]['stats']
    rows.append(dict(step=step, pose_max_error_against_actual_sensor_packet=error,
        observation_age_s=saved['motion_state']['age_s'], original_active_reference_step=route['last_plan'],
        original_active_reference_exact265=True, original_reference_invalid=route['current_route_invalid'],
        original_stagnation=route['stagnated_without_route_progress'],
        queried_reference_status=query['selected_status'], reference_remaining_goal_m=query['remaining_goal_m'],
        original_search_expanded=stats['expanded'], original_search_wall_s=stats['wall_s'],
        geometric_dense_minimum_m=stats['minimum_clearance_m'],
        dynamic_control_tail_qualified=False, actual_new_reference_executed=False))

protocol = read(cell.parent / 'STATIC_PROTOCOL.json')
new = read(root / 'renewal_probe/ORIGINAL_SEARCH_0282.json')
newpath = np.asarray(new['records'][-1]['path'])
oldpath = np.asarray(old['path'])
actual = np.array([json.loads(line)['xy'] for line in (cell / 'v648_execution.jsonl').open()])
start = np.asarray(read(root / 'renewal_probe/INPUT_0282.json')['pose'])
actor_box = read(root / 'renewal_probe/INPUT_0282.json')['motion_state']['current_outer_rectangle']
goal = np.asarray(old['causal_route_input']['goal'])
fig, axes = plt.subplots(1, 2, figsize=(14, 7), constrained_layout=True)
for ax in axes:
    for x, y, hx, hy in protocol['known_rectangles']:
        ax.add_patch(Rectangle((x-hx, y-hy), 2*hx, 2*hy, facecolor='#b8c1cb', edgecolor='#66727f', lw=.7))
    for x, y, radius in protocol['known_circles']:
        ax.add_patch(Circle((x, y), radius, facecolor='#b8c1cb', edgecolor='#66727f', lw=.7))
    ax.plot(actual[:,0], actual[:,1], color='#9a9a9a', lw=2, alpha=.85, label='Actual V821 trajectory (failed)')
    ax.plot(oldpath[:,0], oldpath[:,1], color='#a347ba', lw=2.4, label='Step 265 partial reference')
    ax.plot(newpath[:,0], newpath[:,1], color='#078859', lw=2.5, ls='--', label='Step 282 full reference (NOT EXECUTED)')
    x, y, hx, hy = actor_box
    ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,facecolor='#ffb365',edgecolor='#bf6814',alpha=.55,
                           label='Causal estimated actor box at 282'))
    ax.scatter(*start[:2], s=60, c='#146bb4', zorder=5, label='Actual vehicle pose at 282')
    ax.scatter(*goal, marker='*', s=180, c='#d4422c', zorder=5, label='Original goal')
    ax.set_aspect('equal'); ax.grid(alpha=.15); ax.set_xlabel('x (m)'); ax.set_ylabel('y (m)')
axes[0].set(xlim=(-6,6),ylim=(-5.7,5.7),title='Original full static map / saved references')
axes[1].set(xlim=(-3,1.6),ylim=(-3.6,1.5),title='A full goal reference existed after a fresh observation')
axes[0].legend(loc='upper left', fontsize=8, framealpha=.95)
fig.suptitle('Zero-model diagnosis: geometric references only; no new execution or safety claim', fontsize=13)
fig.savefig(root / 'reference_comparison.png', dpi=160)
plt.close(fig)
result = dict(status='SAVED_POSE_AND_REFERENCE_LINKAGE_VERIFIED', models=0, integrations=0, rows=rows,
    first_finite_observed_step=read(root/'renewal_probe/OBSERVATION_CONNECTIVITY.json')['first_finite_observed_step'],
    original_files_sha256_unchanged=True, review_guard_bytes_unchanged=(repo/'REVIEW_PENDING').read_bytes()==guard,
    raw_packets_sha256=sha(cell/'sensor_packets.jsonl.gz'),
    figure_sha256=sha(root/'reference_comparison.png'),
    limits='No native command/prefix/tail qualification, new navigation or dynamic acceptance established')
assert result['review_guard_bytes_unchanged']
(root/'EVIDENCE_CHECK.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(result,ensure_ascii=False))
