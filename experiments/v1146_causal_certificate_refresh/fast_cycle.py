"""Conservative first-tier certification without a 4096-LP phase table.

Fresh directional coefficient bounds enclose the obstacle for the entire
declared harmonic cycle. Passing this bound is sufficient, not necessary.
Failure requests timed refinement; it never authorizes a control.
"""
import math
import numpy as np
from source import final_gate as cycle_gate
from bindings import ref, REQUIRED


def certify(x, states, controls, rows):
    proof, requests = cycle_gate(x, states, controls, rows)
    geometry = ref._old.Geometry(x['setup']['known'],x['source']['periodic'])
    a,b = geometry.clearances(states[-1:,:3])
    terminal = np.asarray(x['safe_terminal_pose'])
    proof['terminal_full_cycle_raw_m'] = float(min(a[0],b[0]))
    proof['checks'].update(
        terminal_full_cycle_hold=proof['terminal_full_cycle_raw_m']>=REQUIRED,
        safe_terminal_position=bool(np.linalg.norm(states[-1,:2]-terminal[:2])<=.025),
        safe_terminal_heading=bool(abs(math.atan2(math.sin(states[-1,2]-terminal[2]),math.cos(states[-1,2]-terminal[2])))<=.1))
    proof['passed'] = bool(all(proof['checks'].values()))
    proof['phase_LPs'] = 0
    return proof
