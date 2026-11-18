from gap_tools import *
import importlib.abc
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODEL_ISOLATED_IMPORT '+name)
sys.meta_path.insert(0,NoModels())
def main():
    for file in ['worker.py','gap_execution.py','audit.py']:load('v1177_isolated_'+file.replace('.','_'),C/file)
    factory=load('v1177_lazy_original_factory',R/'experiments/v1114_coupled_steering_mode/physical.py')
    for task in read(C/'TASKS.json'):task_contract(task);plan_for(task)
    assert all(n not in sys.modules for n in ['mujoco','vehicle','torch','rclpy'])and not read(O/'APPROVAL.json')['models_authorized']
    assert source_ok()and sha(R/'REVIEW_PENDING')==GUARD
    dump(O/'ISOLATED_QUALIFICATION.json',dict(passed=True,scope='isolated software import/task metadata, not a new MJB audit',models=0,physical_native=0,new_state_prediction=0,original_root_hidden=True,gpu_hidden=True))
    print('V1177_ISOLATED_SOFTWARE_PASS')
if __name__=='__main__':main()
