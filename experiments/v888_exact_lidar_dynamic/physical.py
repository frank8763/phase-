"""Same dynamic factory/replay; bind exact batch rays only after authorized creation."""
import hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
engine=module('v888_original_dynamic_adapter',R/'experiments/v882_runtime_evidence_repair/physical.py')
exact=module('v888_exact_sampled_lidar',R/'experiments/v887_exact_lidar_software/exact_lidar.py')
def create_vehicle(out,task):
 instance=engine.create_vehicle(out,task)
 import vehicle
 assert instance.count==0 and instance.d.time==0.,'SENSOR_BIND_AFTER_PHYSICS'
 reference=instance.scan();original=vehicle.get_lidar_features
 vehicle.get_lidar_features=exact.get_lidar_features
 try:
  candidate=instance.scan()
  assert reference==candidate,'TRUE_T0_SENSOR_VALUES_CHANGED'
  assert instance.count==0 and instance.d.time==0.,'SENSOR_BIND_ADVANCED_MODEL'
 except BaseException:
  vehicle.get_lidar_features=original;raise
 proof=dict(passed=True,original_and_exact_true_t0_packets_bitwise_equal=True,native_integrations_during_binding=0,only_function_binding_changed=True,original_vehicle_scan_source_sha256=hashlib.sha256((R/'experiments/v858_nav2_verified/vehicle.py').read_bytes()).hexdigest(),exact_lidar_sha256=hashlib.sha256((R/'experiments/v887_exact_lidar_software/exact_lidar.py').read_bytes()).hexdigest())
 (Path(out)/'EXACT_SENSOR_BINDING.json').write_text(json.dumps(proof,indent=2)+'\n')
 return instance
replay=engine.replay
