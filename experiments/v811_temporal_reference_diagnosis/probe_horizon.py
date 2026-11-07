"""Minimized real-helper probe: same pose, 6.56s versus 6.560001s; no model."""
import argparse
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

repo = Path(__file__).resolve().parents[2]
own = repo/'experiments/v810_forward_reference_global'
class NoPhysics(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname == 'mujoco' or fullname.startswith('mujoco.'):
            raise RuntimeError('NO_MODELS_ALLOWED_IN_DIAGNOSIS')
sys.meta_path.insert(0,NoPhysics())
sys.path.insert(0,str(own))
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
from exact_footprint import build
from timed_reference import attach
spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py')
F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
ap=argparse.ArgumentParser();ap.add_argument('--assert-continuous',action='store_true');args=ap.parse_args()
rows=json.loads((repo/'runs/v810_forward_reference_global/pre_navigation/RESULTS.json').read_text())
row=next(x for x in rows if x['step']==303)
f=build(F,row['causal_world']);attach(f,row['causal_state'])
path=np.asarray(row['path']);t=np.asarray(row['stats']['reference_arrival_times_s'])
points=path[t>6.56,:3]
a=f.reference_values(points,np.full(len(points),6.56))
b=f.reference_values(points,np.full(len(points),6.560001))
j=int(np.argmax(b-a))
result=dict(status='HORIZON_DISCONTINUITY_REPRODUCED',fixed_step=303,pose=points[j].tolist(),
    at_6_56_s=float(a[j]),at_6_560001_s=float(b[j]),clearance_jump_m=float(b[j]-a[j]),
    gate_before=bool(a[j]>=.155),gate_after=bool(b[j]>=.155),new_models=0,integrations=0,
    scope='Intentionally uncertified reference beyond horizon; this probe demonstrates optimistic guidance discontinuity, not a violated execution guarantee.')
print(json.dumps(result,indent=2))
if args.assert_continuous:
    assert np.max(b-a)<1e-3,'REFERENCE_TIME_CUTOFF_DISCONTINUITY'
