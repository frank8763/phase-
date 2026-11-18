from route_tools import *
import importlib.abc
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ISOLATED_IMPORT_MODEL '+name)
sys.meta_path.insert(0,NoModels())
for file in ['worker.py','audit.py','route_policy.py','start.py','finish.py','watchdog.py']:load('v1184_isolated_'+file.replace('.','_'),C/file)
for task in read(C/'TASKS.json'):task_contract(task)
assert read(O/'ANALYTICAL_ENTRY_QUALIFICATION.json')['passed'] and read(O/'QUALIFICATION.json')['passed'] and not read(O/'APPROVAL.json')['models_authorized'] and source_ok() and sha(R/'REVIEW_PENDING')==GUARD
dump(O/'ISOLATED_QUALIFICATION.json',dict(passed=True,models=0,new_mujoco_native=0,scope='software imports and task contracts; no new MJB or physical audit'))
print('V1184_ISOLATED_ENTRY_PASS')
