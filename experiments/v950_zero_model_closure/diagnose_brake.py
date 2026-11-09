"""Locate the closed curved-response error in saved control/encoder time series."""
import importlib.abc
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel())
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/v949_steering_handoff'))
from vehicle_control import old
P=ROOT/'runs/v858_nav2_verified/v950/response_03';O=ROOT/'runs/v951_component_output_entry'
setup=json.loads((P/'physics/SETUP.json').read_text());commands=json.loads((P/'physics/BODY_COMMANDS.json').read_text())
with np.load(P/'BODY_AND_STEERING.npz')as saved:
    body=saved['body'];servo=saved['steering'];expected=saved['expected'];origin=saved['origin']
with np.load(P/'physics/NATIVE_TRACE.npz')as trace:actual=trace['ctrl'][:,setup['actuator_ids']].copy()
bounds=np.asarray(setup['limits']);rate=np.asarray(setup['slew_per_second'])
adapter=old.Adapter.__new__(old.Adapter);adapter.dt=.01;adapter.last=np.zeros(4);adapter.integral=0.
adapter.wheelbase=.60;adapter.track=.54;adapter.radius=.12;adapter.center_limit=.42722137342572125
adapter.max_curvature=np.tan(adapter.center_limit)/adapter.wheelbase
adapter.commands=SimpleNamespace(lower=bounds[:,0],upper=bounds[:,1],rate=rate*.08,
    legal=lambda v:bool(np.all(v>=bounds[:,0])and np.all(v<=bounds[:,1])))
old_outputs=np.asarray([adapter.compute(v,w,mv,mw,stale).copy()for _,v,w,mv,mw,stale in commands])
delta=abs(old_outputs-actual).max(axis=1);different=np.flatnonzero(delta>1e-8)
rotation=np.arctan2(np.sin(body[200:,2]-expected[:,2]),np.cos(body[200:,2]-expected[:,2]))
first=np.flatnonzero(abs(rotation)>.035)
result=dict(models=0,integrations=0,closed_v950_v951_status='NOT_PASSED',
    first_original_vs_candidate_actuator_difference_tick=None if not len(different)else int(different[0]+1),
    first_brake_tick=221,moving_prefix_original_adapter_max_difference=float(delta[:220].max()),
    requested_moving_prefix_yaw_error_at_tick220_rad=float(rotation[19]),
    first_yaw_bound_violation_tick=int(first[0]+201),
    brake_phase_yaw_error_max_rad=float(abs(rotation[20:]).max()),
    measured_peak_yaw_rate_during_centering_rad_s=float(abs(body[220:280,4]).max()),
    measured_peak_steering_rate_during_centering_rad_s=float(abs(servo[220:280,2:]).max()),
    yaw_at_brake_start_rad=float(body[219,2]),yaw_after_stop_rad=float(body[-1,2]),
    body_yaw_rate_half_second_after_brake=float(body[269,4]),
    engineering_diagnosis='The actual moving prefix is unchanged to roundoff; first changed actuator action is steering-neutralization at the brake boundary. Most yaw error accumulates while braking and steering are simultaneously moving. This isolates the transition mechanism; old-output counterfactuals are not a new physical trajectory.',
    next_design='Decelerate with the original held-steering stop first; only after measured body stop permit zero-drive steering alignment, then require measured servo settling before a new forward plan. Requalify both phases and their complete composition without relaxing .035 or .03 gates.',
    counterfactual_trajectory_or_success_claimed=False)
(O/'BRAKE_TRANSITION_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
