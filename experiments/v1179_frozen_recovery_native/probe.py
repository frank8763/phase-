from recovery_tools import *
import importlib.abc
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODEL_ISOLATED_IMPORT '+name)
sys.meta_path.insert(0,NoModels())
def main():
    for file in ['worker.py','policy_execution.py','audit.py']:load('v1179_isolated_'+file.replace('.','_'),C/file)
    for t in read(C/'TASKS.json'):task_contract(t)
    assert not read(O/'APPROVAL.json')['models_authorized']and source_ok()and sha(R/'REVIEW_PENDING')==GUARD
    dump(O/'ISOLATED_QUALIFICATION.json',dict(passed=True,scope='isolated software import/task metadata only, no new MJB audit',models=0,new_mujoco_native=0,new_state_prediction=0))
    print('V1179_ISOLATED_SOFTWARE_QUALIFIED')
if __name__=='__main__':main()
