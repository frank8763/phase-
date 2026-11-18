"""Same corrected audit CLI, task-local saved JSON writes, parent bytes untouched."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODEL_FULL_AUDIT '+name)
sys.meta_path.insert(0,NoModels())
from worker_context import *
import fcntl
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    module=load('phase_v1264_corrected_main_auditor',C/'audit.py');old_dump=module.dump
    def save(path,value):
        if Path(path).name=='FINAL_INDEPENDENT_AUDIT.json':path=O/'ORIGINAL_MAIN_FULL_AUDIT.json'
        old_dump(path,value)
    module.dump=save
    # Base native checker also writes only the new audit view.
    original_load=module.load
    def checked_load(name,path):
        m=original_load(name,path)
        if Path(path).resolve()==C/'audit_refusal.py':
            previous=m.dump
            m.dump=lambda p,v:previous(O/'ORIGINAL_MAIN_BASE_AUDIT.json'if Path(p).name=='BASE_NATIVE_AUDIT.json'else p,v)
        return m
    module.load=checked_load
    module.audit(read(Path(sys.argv[1])))
    print((O/'ORIGINAL_MAIN_FULL_AUDIT.json').read_text())
if __name__=='__main__':main()
