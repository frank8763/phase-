"""Independent closed physical handoff and exact command/reference reconstruction."""
import gzip
import importlib.abc
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','vehicle','physical','factory'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


def audit():
    sys.meta_path.insert(0,NoModel())
    root=Path(__file__).resolve().parents[2];out=root/'runs/v858_nav2_verified/v962/handoff_left'
    parent=root/'runs/v963_continuous_dynamic';result=json.loads((out/'QUALIFICATION.json').read_text())
    if not(out/'HANDOFF_ARRAYS.npz').exists():
        report=dict(passed=False,complete=False,original_result=result,models=0,integrations=0)
        (parent/'HANDOFF_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n');return report
    sys.path.insert(0,str(root/'experiments/v961_steering_continuity'))
    from independent_shaping import check
    with np.load(out/'HANDOFF_ARRAYS.npz')as f:body=f['body'];servo=f['steering'];origin=f['origin'];expected=f['expected']
    with np.load(out/'physics/NATIVE_TRACE.npz')as f:data={k:f[k].copy()for k in f.files}
    setup=json.loads((out/'physics/SETUP.json').read_text());q=data['qpos'];v=data['qvel'];count=len(q)
    yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    derived=np.c_[q[:,:2],yaw,v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw),v[:,5]]
    enc=np.c_[q[:,setup['steering_qpos_addresses']],v[:,setup['steering_qvel_addresses']]]
    commands=json.loads((out/'physics/BODY_COMMANDS.json').read_text());shapes=json.loads((out/'SHAPING.json').read_text())
    last=None;shape_ok=True;controls_ok=True
    for i,row in enumerate(shapes):
        tick=420+i*5;p=row['packet'];s=row['shape']
        assert p['native_tick']==tick and np.max(abs(np.array(p['body'])-derived[tick-1]))<=1e-8
        assert np.max(abs(np.r_[p['steering']['position'],p['steering']['velocity']]-enc[tick-1]))<=1e-8
        last=check(s,p,last)
        controls_ok &= all(np.max(abs(np.asarray(commands[j][1:3])-s['selected']))<=1e-12 for j in range(tick,tick+5))
    reconstructed=[];p=derived[419,:3].copy()
    for tick in range(420,1820):
        if tick<1620:
            velocity,angular=commands[tick][1:3];a=p[2];b=a+angular*.01
            if abs(angular)<1e-10:p[:2]+=velocity*.01*np.array([math.cos(a),math.sin(a)])
            else:p[:2]+=[velocity/angular*(math.sin(b)-math.sin(a)),-velocity/angular*(math.cos(b)-math.cos(a))]
            p[2]=b
        reconstructed.append(p.copy())
    reference=np.asarray(reconstructed)
    position=float(np.linalg.norm(derived[420:,:2]-reference[:,:2],axis=1).max())
    angle=float(abs(np.arctan2(np.sin(derived[420:,2]-reference[:,2]),np.cos(derived[420:,2]-reference[:,2]))).max())
    progress=float((derived[1619,:2]-derived[419,:2])@np.array([math.cos(derived[419,2]),math.sin(derived[419,2])]))
    with np.load(root/'runs/v858_nav2_verified/v959/response_06/physics/NATIVE_TRACE.npz')as baseline:
        prefix=max(float(abs(data[k][:420]-baseline[k]).max())if data[k][:420].size else 0. for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat'])
    replay=json.loads((out/'physics/REPLAY.json').read_text());contacts=json.loads(gzip.decompress((out/'physics/CONTACTS.json.gz').read_bytes()))
    bounds=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second']);ctrl=data['ctrl'][:,setup['actuator_ids']]
    spec=importlib.util.spec_from_file_location('handoff_base_adapter',root/'experiments/v958_hold_steering_contract/vehicle_control.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    a=module.Adapter.__new__(module.Adapter);a.dt=.01;a.last=np.zeros(4);a.integral=0.;a.mode='DRIVING';a.wheelbase=.6;a.track=.54;a.radius=.12;a.center_limit=.42722137342572125;a.max_curvature=np.tan(a.center_limit)/a.wheelbase
    a.commands=SimpleNamespace(lower=bounds[:,0],upper=bounds[:,1],rate=rates*.08,legal=lambda z:bool(np.all(z>=bounds[:,0])and np.all(z<=bounds[:,1])))
    maximum=0.
    for i,(_,velocity,angular,mv,mw,stale)in enumerate(commands):maximum=max(maximum,float(abs(a.compute(velocity,angular,mv,mw,stale)-ctrl[i]).max()))
    checks=dict(full1820=count==len(commands)==len(body)==1820,actual_body=float(abs(body-derived).max())<=1e-8,
        actual_encoders=float(abs(servo-enc).max())<=1e-8,shaped_controls=bool(controls_ok),reference_exact=float(abs(reference-expected).max())<=1e-8,
        same_old420_prefix=prefix<=1e-8,full_position_bound=position<=.04,full_heading_bound=angle<=.035,actual_forward_1m=progress>=1.,
        all_native_safety=float(data['clearance'].min())>=.15 and float(data['self_margin'].min())>=-1e-10,
        bad_contacts0=not any(c[2]in{'robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'}for row in contacts for c in row),
        original_ctrl_bounds=bool(np.all(ctrl>=bounds[:,0])and np.all(ctrl<=bounds[:,1])),original_ctrl_slew=bool(np.all(abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rates*.01+1e-10)),
        exact_adapter_reconstruction=maximum<=1e-8,complete_own_replay=replay['passed']and replay['replay_native']==1820 and replay['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8,
        body_speed=float(abs(derived[:,3]).max())<=.13,body_yaw=float(abs(derived[:,4]).max())<=.16,final_stop=bool(abs(derived[1669:,3:5]).max()<=.03),
        final_forward_steering=bool(abs(enc[1619,:2]).max()<=.01 and abs(enc[1619,2:]).max()<=.03),no_reverse=all(c[1]>=0 for c in commands))
    report=dict(passed=bool(result['passed']and all(checks.values())),checks={k:bool(v)for k,v in checks.items()},actual_native=1820,replay_native=replay['replay_native'],
        position_max_m=position,heading_max_rad=angle,actual_forward_progress_m=progress,minimum_actual_clearance_m=float(data['clearance'].min()),
        prefix_state_ctrl_max_error=prefix,controller_max_error=maximum,models=0,integrations=0)
    (parent/'HANDOFF_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    answer=audit();print(json.dumps(answer,indent=2));assert answer['passed']
