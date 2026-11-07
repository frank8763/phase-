"""Bounded, saved-byte-only navigation diagnosis; no simulator imports.

Require the navigation result to exist before reading. Never authorize commands,
construct actions, or turn offline actor coordinates into online planner inputs.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def read(p):
    return json.loads(p.read_text())


def rows(p):
    return [json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []


def yaw(q):
    w, x, y, z = q[3:7]
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pair', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--plot', action='store_true')
    a = ap.parse_args()
    repo = Path(__file__).resolve().parents[2]
    pair = a.pair.resolve()
    output = a.output.resolve()
    assert pair.is_relative_to(repo / 'runs') and output.is_relative_to(repo / 'runs')
    assert not output.exists(), 'Analysis output is immutable; choose a new namespace'
    cell = pair / 'geometry_memory'
    result = read(cell / 'result.json')
    protocol = read(pair / 'STATIC_PROTOCOL.json')
    source = [cell / 'result.json', pair / 'STATIC_PROTOCOL.json', cell / 'v648_execution.jsonl']
    execution = rows(source[-1])
    goal = np.asarray(protocol['goal_xy'], float)
    start = np.asarray(protocol['start_qpos'][:2], float)
    xy = np.asarray([x['xy'] for x in execution], float)
    assert len(xy) == result['public_steps']
    poses = np.vstack([start, xy])
    delta = np.diff(poses, axis=0)
    lengths = np.linalg.norm(delta, axis=1)
    signed = np.asarray([d @ np.array([math.cos(yaw(r['qpos'])), math.sin(yaw(r['qpos']))])
                         for d, r in zip(delta, execution)])
    distance = np.linalg.norm(xy - goal, axis=1)
    progress = float(np.linalg.norm(start - goal)) - distance
    best = int(np.argmax(progress))
    actor_dist = [float(np.linalg.norm(np.asarray(r['mocap_pos'][0][:2]) - r['xy']))
                  for r in execution]
    plans = []
    for p in sorted(cell.glob('planning_*.json')):
        d = read(p)
        path = np.asarray(d['path'], float) if d['path'] is not None else np.empty((0, 4))
        plans.append(dict(step=d['step'], status=d['stats']['status'],
                          reverse_nodes=int(np.sum(path[:, 3] < 0)) if len(path) else 0,
                          points=len(path), projection=d['route_projection_metadata']['status'],
                          xy=d['pose'][:2], path=path[:, :2].tolist(),
                          work=d['stats'].get('expanded'), wall_s=d['stats'].get('wall_s')))
        source.append(p)
    checks = rows(cell / 'route_revalidation.jsonl')
    gates = rows(cell / 'model_admission.jsonl')
    for name in ['route_revalidation.jsonl', 'model_admission.jsonl', 'FIRST_DISCOVERY.json']:
        p = cell / name
        if p.exists():
            source.append(p)
    discovery = read(cell / 'FIRST_DISCOVERY.json') if (cell / 'FIRST_DISCOVERY.json').exists() else None
    invalid = [d['step'] for d in checks if d['current_route_invalid']]
    stat = dict(
        scope='closed actual saved navigation only; not a new experiment or safety audit',
        outcome=result['outcome'], strict_safe_arrival=result['strict_safe_arrival'],
        public_steps=result['public_steps'], actual_native_steps=result['physics_steps'],
        private_native_steps=result['prediction_steps'],
        first_discovery=discovery,
        actual_simulation_s=float(execution[-1]['time']), wall_s=result['elapsed_s'],
        goal_remaining_m=float(distance[-1]), maximum_goal_progress_m=float(progress[best]),
        best_step=int(execution[best]['step']), best_xy=xy[best].tolist(),
        final_goal_progress_m=float(progress[-1]), final_xy=xy[-1].tolist(),
        actual_path_length_m=float(np.sum(lengths)),
        reverse_displacement_projection_m=float(-np.sum(np.minimum(signed, 0))),
        reverse_public_steps=int(np.sum(signed < -1e-4)),
        closest_actor_center_m=min(actor_dist), sensor_range_m=3.0,
        crossed_central_x0=bool(np.any(xy[:, 0] > 0)) if start[0] < 0 else None,
        plans=len(plans), all_plans_have_goal_path=all(p['status'] == 'GLOBAL_GOAL_PATH' for p in plans),
        plans_with_reverse_nodes=sum(p['reverse_nodes'] > 0 for p in plans),
        first_reverse_plan=next((p['step'] for p in plans if p['reverse_nodes']), None),
        reference_checks=len(checks), invalid_reference_checks=len(invalid),
        invalid_reference_steps=invalid,
        stagnation_flags=sum(d['stagnated_without_route_progress'] for d in checks),
        ordinary_reverse_gear_steps=sum(d.get('active_gear') == -1 for d in gates),
        plan_projection_statuses=sorted(set(p['projection'] for p in plans)),
        new_models=0, new_integrations=0, new_predictions=0, new_actions=0,
        source_sha256={str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in source},
    )
    output.mkdir(parents=True)
    (output / 'RESULT.json').write_text(json.dumps(stat, indent=2, allow_nan=False) + '\n')
    (output / 'PLAN_SUMMARIES.json').write_text(json.dumps(plans, indent=2, allow_nan=False) + '\n')
    if a.plot:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle, Circle
        fig, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)
        ax = axes[0]
        for x, y, hx, hy in protocol['known_rectangles']:
            ax.add_patch(Rectangle((x - hx, y - hy), 2 * hx, 2 * hy, color='#879ba9'))
        for x, y, r in protocol['known_circles']:
            ax.add_patch(Circle((x, y), r, color='#879ba9'))
        chosen = sorted(set([0, len(plans) - 1])) if plans else []
        for i in chosen:
            path = np.asarray(plans[i]['path'])
            if len(path):
                ax.plot(path[:, 0], path[:, 1], '--', lw=1.5, alpha=.8,
                        label=f"Reference @step {plans[i]['step']} ({plans[i]['projection']})")
        ax.plot(poses[:, 0], poses[:, 1], color='#1767ad', lw=2.5, label='Actual saved trajectory')
        ax.scatter(*start, color='black', marker='s', s=50, label='Start')
        ax.scatter(*goal, color='#e6ad15', marker='*', s=120, label='Original goal')
        ax.scatter(*xy[-1], color='#c33c3c', marker='x', s=65, label='Actual end')
        ax.set(xlabel='World x (m)', ylabel='World y (m)', title='Global references and actual execution')
        ax.set_aspect('equal')
        ax.legend(fontsize=7, loc='upper center', bbox_to_anchor=(.5, -.12), ncol=2)
        ax.grid(alpha=.15)
        ax = axes[1]
        times = [r['time'] for r in execution]
        ax.plot(times, progress, color='#1767ad', label='Actual target progress')
        ax.plot(times, actor_dist, color='#d68332', label='Actor center distance (offline evaluator)')
        ax.axhline(3, color='#d68332', linestyle=':', label='3 m sensor range')
        ax.set(xlabel='Actual simulator time (s)', ylabel='Distance (m)',
               title=f"{result['outcome']} | discovery {'recorded' if discovery else 'not recorded'}")
        ax.legend(fontsize=8)
        ax.grid(alpha=.2)
        fig.suptitle(f"Saved-state diagnosis: {pair.parent.name}; no new physics", fontsize=13)
        fig.savefig(output / 'actual_reference_progress.png', dpi=160)
        plt.close(fig)
    print(json.dumps({k: v for k, v in stat.items() if k not in ['source_sha256', 'invalid_reference_steps']}, indent=2))


if __name__ == '__main__':
    main()
