"""Offline views of every locked task; no environment, inference, or simulation.

Ground truth below is read solely for retrospective plotting. It never enters
the online controller. Failed/interrupted/unexecuted tasks remain visible.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle
import numpy as np

repo = Path(__file__).resolve().parents[2]
root = repo / 'runs/v657_static_fixed_work_confirmation'
window = root / 'confirmation01'


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def panel(ax, task, row):
    ax.set_aspect('equal')
    ax.grid(alpha=.14)
    if row is None:
        ax.text(.5, .5, 'NOT EXECUTED', transform=ax.transAxes, ha='center')
        ax.set_title(f'{task["seed"]} | {task["scene"]}', fontsize=9)
        return
    pair = repo / row['run_root'] / row['name'] / 'paired'
    protocol = read(pair / 'STATIC_PROTOCOL.json')
    trace = read(pair / 'geometry_memory/trace.json', [])
    if not trace:
        ax.text(.5, .5, 'NO TRAJECTORY', transform=ax.transAxes, ha='center')
        return
    points = np.array([x['pose'][:2] for x in trace])
    start = np.array(protocol['start_qpos'][:2])
    goal = np.array(protocol['goal_xy'])
    for x, y, hx, hy in protocol['known_rectangles']:
        ax.add_patch(Rectangle((x-hx, y-hy), 2*hx, 2*hy,
                               facecolor='#b6bec7', edgecolor='#7c8996', lw=.6))
    for x, y, radius in protocol['known_circles']:
        ax.add_patch(Circle((x, y), radius, facecolor='#b6bec7', edgecolor='#7c8996', lw=.6))
    for obstacle in protocol['physical_unknown_obstacles']:
        ax.add_patch(Circle(obstacle['xy'], obstacle['radius'], facecolor='#d66b51',
                            edgecolor='#8f352a', lw=.8, zorder=3))
    interrupted = row['result'] is None
    failed = not row['strict_success']
    color = '#ba6b21' if failed else '#2466a0'
    ax.plot(np.r_[start[0], points[:, 0]], np.r_[start[1], points[:, 1]],
            color=color, lw=1.5, zorder=4)
    # This is the declared fixed planning envelope, not reconstructed geometry.
    low_x, low_y, high_x, high_y = protocol['footprint_bounds']
    corners = np.array([[low_x, low_y], [high_x, low_y],
                        [high_x, high_y], [low_x, high_y]])
    for index in sorted(set([0, len(trace)//3, 2*len(trace)//3, len(trace)-1])):
        x, y, yaw = trace[index]['pose']
        c, s = np.cos(yaw), np.sin(yaw)
        transformed = corners @ np.array([[c, s], [-s, c]]) + [x, y]
        ax.add_patch(Polygon(transformed, closed=True, fill=False,
                             edgecolor=color, lw=.65, alpha=.55, zorder=5))
    ax.scatter(*start, marker='o', s=22, color='#197b55', zorder=6)
    ax.scatter(*goal, marker='*', s=64, color='#197b55', zorder=6)
    ax.add_patch(Circle(goal, .45, fill=False, edgecolor='#197b55', lw=.7, ls=':'))
    ax.scatter(*points[-1], marker='x', s=24, color=color, zorder=7)
    extent = np.vstack([points, start, goal])
    low = extent.min(axis=0)-.9
    high = extent.max(axis=0)+.9
    ax.set_xlim(low[0], high[0]); ax.set_ylim(low[1], high[1])
    status = 'INCOMPLETE / NON-SUCCESS' if interrupted else row['result']['outcome']
    native = read(pair / 'NATIVE_REPLAY_AUDIT.json', {})
    clearance = native.get('minimum_reconstructed_native_actual_axis_AABB_clearance_m')
    clear = f'{clearance:.3f} m' if clearance is not None else 'pending'
    ax.set_title(f'{task["seed"]} | {task["scene"]}\n{status} | {len(trace)} steps | min {clear}',
                 fontsize=8, color='#9a551c' if failed else '#243e51')
    ax.tick_params(labelsize=7)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--partial', action='store_true', help='write preview under runs only')
    args = parser.parse_args()
    if not args.partial:
        assert (window/'COMPLETION.json').exists(), 'Final plot requires closed continuation'
    tasks = read(window/'SELECTION_FREEZE.json')['tasks']
    rows = read(window/'CONFIRMATION_RESULTS.json', [])
    by_seed = {x['seed']: x for x in rows}
    out = root/'trajectory_preview' if args.partial else repo/'docs/figures'
    out.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(6, 4, figsize=(15, 22), constrained_layout=True)
    for task, ax in zip(tasks, axes.flat):
        panel(ax, task, by_seed.get(task['seed']))
    fig.suptitle('Every locked static task: recorded trajectories, failures retained\n'
                 'Grey: known map | Red: initially unknown truth (offline display only) | '
                 'Green: start/goal | Outlines: fixed planning envelope\n'
                 'No added simulation; native-step clearance audited separately', fontsize=11)
    fig.savefig(out/'v657_all_trajectories.png', dpi=150)
    plt.close(fig)
    # Descriptive examples fixed by list order; never used to estimate success rate.
    examples = [next(t for t in tasks if t['scene']==s) for s in ['single_event','legacy_two']]
    fig, axes = plt.subplots(1, 2, figsize=(11, 6), constrained_layout=True)
    for task, ax in zip(examples, axes):
        panel(ax, task, by_seed.get(task['seed']))
        ax.set_xlabel('x (m)'); ax.set_ylabel('y (m)')
    fig.suptitle('First locked task of each class — recorded static trajectories\n'
                 'Red: initially unknown obstacles, shown retrospectively | '
                 'Outlines: fixed planning envelope', fontsize=11)
    fig.savefig(out/'v657_first_each_class.png', dpi=180)
    plt.close(fig)
    print(json.dumps({'task_panels': len(tasks), 'completed_records': len(rows),
                      'simulation_steps': 0, 'output': str(out.relative_to(repo))}))


if __name__ == '__main__':
    main()
