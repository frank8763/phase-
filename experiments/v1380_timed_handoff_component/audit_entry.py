import importlib.abc
import sys
import fcntl
from component_context import *
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('AUDIT_MODEL_IMPORT '+name)
sys.meta_path.insert(0,NoModel())
def main():
    from audit import audit
    import numpy as np
    task=read(sys.argv[1]);native=read(Path(task['output'])/'RESULT.json')
    assert native['producer_python']==sys.version and native['producer_numpy']==np.__version__,'AUDIT_DIFFERS_FROM_ACTUAL_NATIVE_PRODUCER'
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);proof=audit(task)
    proof.update(audit_python=sys.version,audit_numpy=np.__version__);dump(Path(sys.argv[1]).parent/'FINAL_INDEPENDENT_AUDIT.json',proof)
    print(json.dumps(proof,allow_nan=False,default=lambda z:z.item()));return 0 if proof['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
