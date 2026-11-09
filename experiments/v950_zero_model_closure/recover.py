"""Recover exact first-case accounting from completed native and replay evidence."""
import gzip
import hashlib
import importlib.abc
import json
import sys
from pathlib import Path
import numpy as np


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel())
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/v950_steering_response'
CASE=ROOT/'runs/v858_nav2_verified/v950/response_00';PHYS=CASE/'physics'
setup=json.loads((PHYS/'SETUP.json').read_text());task=json.loads((ROOT/'experiments/v950_steering_response/TASKS.json').read_text())[0]
commands=json.loads((PHYS/'BODY_COMMANDS.json').read_text())
replay=json.loads((PHYS/'REPLAY.json').read_text())
contacts=json.loads(gzip.decompress((PHYS/'CONTACTS.json.gz').read_bytes()))
with np.load(PHYS/'NATIVE_TRACE.npz')as trace:
    arrays={k:trace[k].copy()for k in trace.files}
with np.load(CASE/'BODY_AND_STEERING.npz')as saved:
    body=saved['body'];servo=saved['steering'];origin=saved['origin'];expected=saved['expected']
q=arrays['qpos'];vel=arrays['qvel'];angle=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
derived=np.c_[q[:,:2],angle,vel[:,0]*np.cos(angle)+vel[:,1]*np.sin(angle),vel[:,5]]
position=np.linalg.norm(body[200:,:2]-expected[:,:2],axis=1)
rotation=abs(np.arctan2(np.sin(body[200:,2]-expected[:,2]),np.cos(body[200:,2]-expected[:,2])))
limit=.04 if task['command'][0]*origin[3]<0 else .02
control=arrays['ctrl'][:,setup['actuator_ids']];bounds=np.asarray(setup['limits']);rate=np.asarray(setup['slew_per_second'])
checks=dict(complete420=len(body)==len(q)==len(commands)==420,
    body_reconstructed_from_native=float(abs(body-derived).max())<=1e-8,
    all_native_safety=float(arrays['clearance'].min())>=.15 and float(arrays['self_margin'].min())>=-1e-10,
    contacts0=not any(c[2]in{'robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'}for row in contacts for c in row),
    full_control_replay=replay['passed']and replay['replay_native']==420,
    bounded_position=float(position.max())<=limit,bounded_rotation=float(rotation.max())<=.035,
    measured_speed_bound=float(abs(body[:,3]).max())<=.13,measured_yaw_bound=float(abs(body[:,4]).max())<=.16,
    settled_by_half_second=bool(np.max(abs(body[269:,3:5]))<=.03),
    final_measured_steering_neutral=bool(abs(servo[-1,:2]).max()<=.01 and abs(servo[-1,2:]).max()<=.03),
    legal_actual_ctrl=bool(np.all(control>=bounds[:,0])and np.all(control<=bounds[:,1])),
    original_slew=bool(np.all(abs(np.diff(np.vstack([np.zeros(4),control]),axis=0))<=rate*.01+1e-10)))
result=dict(passed=all(checks.values()),checks=checks,index=0,models_attempted=1,
    actual_native=420,replay_native=420,private_native=0,fully_recorded_native=420,
    position_residual_max_m=float(position.max()),angle_residual_max_rad=float(rotation.max()),
    native_min_clearance_m=float(arrays['clearance'].min()),body_reconstruction_error=float(abs(body-derived).max()),
    original_campaign_status='NOT_PASSED_METADATA_OUTPUT_SCOPE_FAILURE',original_failure_preserved=True,
    source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in PHYS.iterdir()if p.is_file()},
    new_models=0,new_integrations=0,scope='Independent zero-model readback of completed first response. Does not relabel failed V950 campaign or qualify the remaining18 components.')
(OUT/'ACCOUNTING_RECOVERED.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k!='source_sha256'},indent=2));assert result['passed']
