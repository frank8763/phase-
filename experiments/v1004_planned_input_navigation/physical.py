"""Exact intended physical factory, validated at true t0 before any native step."""
import hashlib,importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
SCIENCE_FILE=R/'experiments/v968_rpp_closed_loop_night/physical.py'
spec=importlib.util.spec_from_file_location('v974_exact_physical',SCIENCE_FILE);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
CONTROL=R/'experiments/v958_hold_steering_contract/vehicle_control.py'
def create_vehicle(out,task):
 v=base.create_vehicle(out,task);out=Path(out);setup=json.loads((out/'SETUP.json').read_text());sensor=json.loads((out/'EXACT_SENSOR_BINDING.json').read_text())
 expected=hashlib.sha256(CONTROL.read_bytes()).hexdigest()
 assert v.count==0 and v.d.time==0.,'BINDING_CHECK_AFTER_INTEGRATION'
 assert setup['adapter_revision']=='V958_KINEMATIC_MOVING_STEERING_HOLD_BRAKE'and setup['adapter_source_sha256']==expected,'WRONG_NATIVE_ADAPTER_BINDING'
 assert Path(v.adapter.compute.__func__.__code__.co_filename).resolve()==CONTROL,'WRONG_COMPUTE_IMPLEMENTATION'
 assert sensor['passed']and sensor['original_and_exact_true_t0_packets_bitwise_equal']and sensor['native_integrations_during_binding']==0,'WRONG_SENSOR_BINDING'
 assert callable(v.steering_sample),'STEERING_ENCODERS_NOT_BOUND'
 (out/'SELECTED_NATIVE_BINDING.json').write_text(json.dumps(dict(passed=True,native_tick=0,integrations=0,factory_source=str(SCIENCE_FILE.relative_to(R)),control_source=str(CONTROL.relative_to(R)),control_sha256=expected,adapter_revision=setup['adapter_revision'],exact_sensor_binding=True),indent=2)+'\n')
 return v
replay=base.replay
