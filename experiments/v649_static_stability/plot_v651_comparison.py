"""Plot recorded static development trajectories; no simulator/controller import."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import numpy as np

repo = Path(__file__).resolve().parents[2]
fig, axes = plt.subplots(2, 2, figsize=(12, 9), constrained_layout=True)
for row, (seed, scene) in enumerate([(93000074, 'legacy_two'), (93000045, 'single_event')]):
    old = repo / 'runs/v650_static_acceptance' / f'confirm_{seed}_{scene}' / 'paired'
    protocol = json.loads((old / 'STATIC_PROTOCOL.json').read_text())
    ax, distance_ax = axes[row]
    for x, y, hx, hy in protocol['known_rectangles']:
        ax.add_patch(Rectangle((x-hx, y-hy), 2*hx, 2*hy, facecolor='.75', edgecolor='.4'))
    for x, y, r in protocol['known_circles']:
        ax.add_patch(Circle((x, y), r, facecolor='.75', edgecolor='.4'))
    for obstacle in protocol['physical_unknown_obstacles']:
        ax.add_patch(Circle(obstacle['xy'], obstacle['radius'], facecolor='#dc8d26', edgecolor='#935400'))
    goal = protocol['goal_xy']
    ax.add_patch(Circle(goal, .45, facecolor='#3c9f6c', alpha=.15))
    ax.scatter(*goal, marker='*', s=100, color='#23754b', label='Goal (0.45 m)')
    trials = [('V650 frozen / failed', old, '#b4474a')]
    for run in sorted((repo/'runs/v651_static_progress').glob(f'dev*_seed{seed}_{scene}')):
        branch = run/'paired/geometry_memory'
        if (branch/'result.json').exists():
            result = json.loads((branch/'result.json').read_text())
            revision = result['source_revision'].replace('progress_', '')
            trials.append((f'V651 {revision} / {result["outcome"]}', run/'paired', '#2372a5' if '28_' in revision else '#7f4f99'))
    for label, pair, color in trials:
        branch = pair/'geometry_memory'
        trace = json.loads((branch/'trace.json').read_text())
        pose = np.array([x['pose'] for x in trace])
        result = json.loads((branch/'result.json').read_text())
        ax.plot(pose[:,0], pose[:,1], color=color, linewidth=1.5, label=f'{label}: {len(trace)} steps')
        ax.scatter(*pose[-1,:2], color=color, marker='x', s=45)
        distance_ax.plot([x['step'] for x in trace], [x['goal_distance_m'] for x in trace], color=color, label=label)
    distance_ax.axhline(.45, color='#23754b', linestyle='--', linewidth=1)
    ax.set(xlim=(-5,5), ylim=(-5,5), aspect='equal', xlabel='x (m)', ylabel='y (m)', title=f'{seed}: {scene}')
    distance_ax.set(xlabel='Public control step (8 native physics ticks)', ylabel='Distance to goal (m)', title='Recorded task progress')
    ax.legend(fontsize=7, loc='lower left')
    distance_ax.legend(fontsize=8)
    distance_ax.grid(alpha=.2)
fig.suptitle('Static unknown obstacles: recorded failures and bounded development\nDevelopment reruns are not independent confirmation trials', fontsize=13)
out = repo/'runs/v651_static_progress/failure_repair_comparison.png'
fig.savefig(out, dpi=180)
print(out)
