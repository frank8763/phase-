"""Prepared native adapter binding. Entry readiness remains CLOSED before models."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


old=module('v945_physical_frozen',ROOT/'experiments/v945_rpccr_observation_liveness/physical.py')
adapter_path=ROOT/'experiments/v949_steering_handoff/vehicle_control.py'
adapter=module('v949_prepared_adapter',adapter_path)


def create_vehicle(out,task):
    # This seam cannot be used to bypass the missing new response qualification.
    readiness=json.loads((Path(__file__).parent/'READINESS.json').read_text())
    assert readiness.get('physical_ready')is True,'CANDIDATE_PHYSICALLY_UNQUALIFIED'
    instance=old.create_vehicle(out,task)
    import mujoco as mj
    assert instance.count==0 and instance.d.time==0.,'ADAPTER_BIND_AFTER_INTEGRATION'
    instance.adapter=adapter.Adapter(instance.m,mj,instance.dt)
    setup=Path(out)/'SETUP.json';data=json.loads(setup.read_text())
    data['adapter_revision']='V949_NEUTRAL_STOP_ACKERMANN_FEEDFORWARD'
    data['adapter_source_sha256']=hashlib.sha256(adapter_path.read_bytes()).hexdigest()
    setup.write_text(json.dumps(data,indent=2)+'\n')
    return instance


replay=old.replay
