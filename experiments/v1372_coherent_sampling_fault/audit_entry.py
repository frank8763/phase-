"""Independent audit uses the exact producer Python and NumPy; models forbidden."""
import importlib.abc
import sys
from component_context import *
class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('AUDIT_MODEL_IMPORT '+name)
sys.meta_path.insert(0,NoPhysical())
def main():
    from sampling_audit import audit
    proof=audit(read(sys.argv[1]));proof.update(python=sys.version,numpy=__import__('numpy').__version__)
    print(json.dumps(proof));return 0 if proof['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
