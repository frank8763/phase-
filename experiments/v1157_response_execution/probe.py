"""Read-only isolation probe; model imports prohibited."""
from response_tools import *
import importlib.abc


class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:
            raise AssertionError('ZERO_MODEL_ISOLATED_ENTRY '+name)


sys.meta_path.insert(0,NoModels())
execution=load('v1157_isolated_execution',C/'response_execution.py')
worker=load('v1157_isolated_worker',C/'worker.py')
audit=load('v1157_isolated_audit',C/'audit.py')
factory=load('v1157_isolated_lazy_cpu_factory',R/'experiments/v1114_coupled_steering_mode/physical.py')
contract=load('v1157_isolated_static_contract',R/'experiments/v1114_coupled_steering_mode/fixture_contract.py')
fixture=read(R/'experiments/v1139_afternoon_observer/STATIC_T0_SOURCE_FIXTURE.json')
for task in read(C/'TASKS.json'):assert contract.validate_task(task,fixture)
assert all(name not in sys.modules for name in ['mujoco','vehicle','torch','rclpy'])
assert read(O/'APPROVAL.json')['models_authorized']is False
assert sha(R/'REVIEW_PENDING')==GUARD_SHA
assert source_ok(),'FROZEN_SOURCE_CHANGED'
print(encode(dict(passed=True,read_only_isolated_import=True,lazy_factory_only=True,
    canonical_metadata_proxy_only_not_new_MJB_check=True,task_fixture_scope=True,
    frozen_source_verified=True,models=0,physical_native=0,analytical_native=0,resource=RESOURCE)))
