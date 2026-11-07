"""Plot only saved public states and registered geometry; no MuJoCo/model loading."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import numpy as np

repo = Path(__file__).resolve().parents[2]
pair = repo / 'runs/v809_time_reference_global/main_slot01/paired'
out = repo / 'runs/report_materials_v809_20261104'
out.mkdir(exist_ok=False)
read = lambda p: json.loads(p.read_text())
t = read(pair / 'geometry_memory/trace.json')
p = np.array([x['pose'] for x in t])
clock = np.array([x['physical_step'] for x in t]) * .01
distance = np.array([x['goal_distance_m'] for x in t])
gear = np.array([x['active_gear'] for x in t])
static = read(pair / 'STATIC_PROTOCOL.json')
plan = np.array(read(pair / 'geometry_memory/planning_0303.json')['path'])
result = read(pair / 'geometry_memory/result.json')
fig = plt.figure(figsize=(16, 9), layout='constrained')
gs = fig.add_gridspec(2, 2, width_ratios=[1.3, 1])
ax = fig.add_subplot(gs[:, 0])
for x, y, hx, hy in static['known_rectangles']:
    ax.add_patch(Rectangle((x-hx, y-hy), 2*hx, 2*hy, color='#9faabd'))
for x, y, radius in static['known_circles']:
    ax.add_patch(Circle((x, y), radius, color='#9faabd'))
ax.plot(plan[:, 0], plan[:, 1], '--', color='#858585', lw=1.4, label='First post-stop reference (contains reverse)')
ax.plot(p[:263, 0], p[:263, 1], color='#1874c5', lw=2.2, label='Actual before detection')
ax.plot(p[262:304, 0], p[262:304, 1], color='#db9634', lw=2.2, label='Actual 328-native brake')
ax.plot(p[303:, 0], p[303:, 1], color='#ba3757', lw=1.8, label='Actual after replan')
ax.scatter([-4, 4], [-2, -2], c=['#1874c5', '#269c66'], s=85, zorder=5)
ax.add_patch(Circle((4, -2), .45, fill=False, ec='#269c66', lw=1.5))
ax.scatter(*p[-1, :2], c='black', marker='x', s=90, zorder=6, label='Actual final state')
ax.add_patch(Circle(result['actor_position_at_end'], .1, color='#e4a529', label='Physical actor at final time (evaluation only)'))
ax.set(xlim=(-6, 6), ylim=(-5.2, 5.2), xlabel='x (m)', ylabel='y (m)',
       title='Original 19 obstacles; recorded trajectory only')
ax.set_aspect('equal')
ax.grid(alpha=.15)
ax.legend(fontsize=8, loc='upper left')
ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(clock, distance, color='#ba3757', lw=1.8)
ax2.axhline(.45, color='#269c66', ls='--', label='Arrival tolerance 0.45 m')
for step, label in [(262, 'Detection'), (302, 'Brake complete')]:
    ax2.axvline(clock[step], ls=':', color='#858585')
    ax2.text(clock[step]+.4, 7.4 if step == 262 else 6.5, label, fontsize=9)
ax2.set(xlabel='Recorded simulation time (s)', ylabel='Distance to goal (m)',
        title='HORIZON: final 2.403 m; best 2.116 m')
ax2.grid(alpha=.2)
ax2.legend(fontsize=9)
ax3 = fig.add_subplot(gs[1, 1])
ax3.step(clock, gear, where='post', color='#425b82')
ax3.set(xlabel='Recorded simulation time (s)', ylabel='Reference active gear',
        yticks=[-1, 1], yticklabels=['Reverse', 'Forward'], ylim=(-1.5, 1.5),
        title='After stop: 9.88 m sampled travel, 4.06 m reverse')
ax3.grid(alpha=.2)
fig.suptitle('V809 global dynamic development: NOT PASSED\n'
             '1200 public / 9600 native steps; all physical and replay checks passed; goal not reached', fontsize=15)
fig.savefig(out / 'v809_actual_global_failure.png', dpi=160)
plt.close(fig)
(out / 'PROVENANCE.json').write_text(json.dumps(dict(
    status='SAVED_PUBLIC_STATE_PLOT_ONLY', source_trace=str((pair/'geometry_memory/trace.json').relative_to(repo)),
    static_geometry=str((pair/'STATIC_PROTOCOL.json').relative_to(repo)),
    first_new_reference_step=303, public_states=1200, models_loaded=0, integrations=0,
    not_mujoco_video=True, no_interpolation_or_generated_success=True), indent=2) + '\n')
print(out / 'v809_actual_global_failure.png')
