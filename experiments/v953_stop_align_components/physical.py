"""Original factory, sensor and native physics; bind V952 before any integration."""
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


old=module('v953_frozen_physical',ROOT/'experiments/v945_rpccr_observation_liveness/physical.py')
source=ROOT/'experiments/v952_stopped_steering_alignment/vehicle_control.py'
candidate=module('v953_stopped_alignment_adapter',source)


def create_vehicle(out,task):
    instance=old.create_vehicle(out,task)
    import mujoco as mj
    assert instance.count==0 and instance.d.time==0.,'BIND_AFTER_MODEL_INTEGRATION'
    ids=np.asarray(instance.adapter.commands.ids[:2]);joints=instance.m.actuator_trnid[ids,0]
    q=instance.m.jnt_qposadr[joints];v=instance.m.jnt_dofadr[joints]
    assert len(set(joints))==2 and np.all(q>=7)and np.all(v>=6),'INVALID_STEERING_ENCODER_MAPPING'
    def encoders():return instance.d.qpos[q].copy(),instance.d.qvel[v].copy()
    initial=encoders()
    assert abs(initial[0]).max()<=.01 and abs(initial[1]).max()<=.03,'INITIAL_STEERING_NOT_CANONICAL_NEUTRAL'
    instance.adapter=candidate.Adapter(instance.m,mj,instance.dt,encoders=encoders)
    path=Path(out)/'SETUP.json';setup=json.loads(path.read_text())
    setup.update(adapter_revision='V952_BRAKE_THEN_STOPPED_ENCODER_ALIGNMENT',
        adapter_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        steering_qpos_addresses=q.tolist(),steering_qvel_addresses=v.tolist(),
        initial_steering_position=initial[0].tolist(),initial_steering_velocity=initial[1].tolist())
    path.write_text(json.dumps(setup,indent=2)+'\n')
    return instance


replay=old.replay
