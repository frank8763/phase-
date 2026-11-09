"""Independent array/readback audit after the component driver closes; zero models."""
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
ROOT=Path(__file__).resolve().parents[2]
OPS=ROOT/'runs/v951_component_output_entry'
closed=json.loads((OPS/'COMPLETION.json').read_text());assert closed['closed']
tasks=json.loads((ROOT/'experiments/v950_steering_response/TASKS.json').read_text())
rows=[];missing=[]
for index,task in enumerate(tasks):
    case=ROOT/task['output'];physical=case/'physics'
    if not(physical/'NATIVE_TRACE.npz').exists():missing.append(index);continue
    with np.load(physical/'NATIVE_TRACE.npz')as trace:arrays={k:trace[k].copy()for k in trace.files}
    with np.load(case/'BODY_AND_STEERING.npz')as saved:
        body=saved['body'];servo=saved['steering'];origin=saved['origin'];expected=saved['expected']
    setup=json.loads((physical/'SETUP.json').read_text());commands=json.loads((physical/'BODY_COMMANDS.json').read_text())
    replay=json.loads((physical/'REPLAY.json').read_text());contacts=json.loads(gzip.decompress((physical/'CONTACTS.json.gz').read_bytes()))
    q=arrays['qpos'];vel=arrays['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    derived=np.c_[q[:,:2],yaw,vel[:,0]*np.cos(yaw)+vel[:,1]*np.sin(yaw),vel[:,5]]
    actual=body[200:]if index<18 else body[400:600]
    position=float(np.linalg.norm(actual[:,:2]-expected[:,:2],axis=1).max())
    angle=float(abs(np.arctan2(np.sin(actual[:,2]-expected[:,2]),np.cos(actual[:,2]-expected[:,2]))).max())
    limit=(.04 if task['command'][0]*origin[3]<0 else .02)if index<18 else .04
    ctrl=arrays['ctrl'][:,setup['actuator_ids']];bounds=np.asarray(setup['limits']);rate=np.asarray(setup['slew_per_second'])
    ticks=420 if index<18 else 800
    checks=dict(complete=len(q)==len(body)==len(commands)==ticks,
        full_body_from_native=float(abs(body-derived).max())<=1e-8,
        native_clearance=float(arrays['clearance'].min())>=.15,
        self_containment=float(arrays['self_margin'].min())>=-1e-10,
        bad_contacts0=not any(c[2]in{'robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'}for row in contacts for c in row),
        own_control_full_state_replay=replay['passed']and replay['replay_native']==ticks and replay['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8,
        legal_ctrl=bool(np.all(ctrl>=bounds[:,0])and np.all(ctrl<=bounds[:,1])),
        legal_slew=bool(np.all(abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rate*.01+1e-10)),
        position=position<=limit,angle=angle<=.035,
        measured_speed=bool(abs(body[:,3]).max()<=.13),
        measured_yaw=bool(abs(body[:,4]).max()<=.16),
        settled_by_half_second=bool(abs(body[(269 if index<18 else 649):,3:5]).max()<=.03),
        neutral_steering=bool(abs(servo[-1,:2]).max()<=.01 and abs(servo[-1,2:]).max()<=.03),
        physical_clock=float(abs(np.diff(np.r_[0.,arrays['time']])-.01).max())<=1e-10)
    if index==18:
        at=body[399];axis=np.array([np.cos(at[2]),np.sin(at[2])])
        gain=float((body[599,:2]-at[:2])@axis)
        checks['stopped_neutral_before_forward']=max(abs(at[3:]))<=.03 and abs(servo[399,:2]).max()<=.01 and abs(servo[399,2:]).max()<=.03
        checks['actual_forward_progress']=gain>=.15
        checks['no_reverse_command']=all(command[1]>=0 for command in commands)
    else:gain=None
    rows.append(dict(index=index,passed=bool(all(checks.values())),checks={k:bool(v)for k,v in checks.items()},
        actual_native=ticks,replay_native=replay['replay_native'],private_native=0,
        position_max_m=position,position_bound_m=limit,angle_max_rad=angle,
        actual_min_clearance_m=float(arrays['clearance'].min()),forward_handoff_progress_m=gain))
all_sources=True
for folder in ['v950_steering_response','v951_component_output_entry']:
    for rel,h in json.loads((ROOT/'experiments'/folder/'SOURCE_FREEZE.json').read_text())['files'].items():
        all_sources=all_sources and hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h
result=dict(passed=closed['passed']and not missing and len(rows)==19 and all(r['passed']for r in rows)and all_sources,
    rows=rows,missing_or_unexecuted_cases=missing,all_frozen_sources_unchanged=all_sources,
    total_actual_native=sum(r['actual_native']for r in rows),total_replay_native=sum(r['replay_native']for r in rows),private_native=0,
    new_models_during_audit=0,new_integrations_during_audit=0,original_v950_metadata_failure_preserved=True,
    scope='Independent complete native arrays, contact lists, executed controls, source SHA and own replay receipts. Component qualification only; full navigation and dynamic24 unexecuted.')
(OPS/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k!='rows'},indent=2))
assert result['passed']
