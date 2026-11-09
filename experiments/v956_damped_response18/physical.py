"""Original physical factory, with V955 controller before first model integration."""
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


base=load('v956_original_physical',ROOT/'experiments/v945_rpccr_observation_liveness/physical.py')
source=ROOT/'experiments/v955_damped_stopped_alignment/vehicle_control.py'
control=load('v956_damped_alignment',source)


def create_vehicle(out,task):
    vehicle=base.create_vehicle(out,task)
    import mujoco as mj
    assert vehicle.count==0 and vehicle.d.time==0.
    joints=vehicle.m.actuator_trnid[np.asarray(vehicle.adapter.commands.ids[:2]),0]
    q=vehicle.m.jnt_qposadr[joints];vel=vehicle.m.jnt_dofadr[joints]
    assert len(set(joints))==2 and np.all(q>=7)and np.all(vel>=6)
    def encoders():return vehicle.d.qpos[q].copy(),vehicle.d.qvel[vel].copy()
    initial=encoders();assert abs(initial[0]).max()<=.01 and abs(initial[1]).max()<=.03
    vehicle.adapter=control.Adapter(vehicle.m,mj,vehicle.dt,encoders=encoders)
    vehicle.steering_sample=lambda:np.r_[vehicle.d.qpos[q],vehicle.d.qvel[vel]]
    path=Path(out)/'SETUP.json';setup=json.loads(path.read_text())
    setup.update(adapter_revision='V955_KINEMATIC_MOVING_LATCHED_DAMPED_STOP_ALIGNMENT',
        adapter_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),steering_qpos_addresses=q.tolist(),
        steering_qvel_addresses=vel.tolist(),initial_steering_position=initial[0].tolist(),initial_steering_velocity=initial[1].tolist())
    path.write_text(json.dumps(setup,indent=2)+'\n');return vehicle


replay=base.replay
