"""Complete saved-native CLI; print the already-normalized canonical JSON."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('SAVED_AUDIT_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from worker_context import *
import fcntl,signal,traceback
import native_audit
def main():
    task=read(sys.argv[1]);task_contract(task);out=Path(task['output']);assert out.exists()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SAVED_FULL_AUDIT_300S')));signal.alarm(300)
    f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    try:
        native_audit.audit(task);print((out/'FINAL_INDEPENDENT_AUDIT.json').read_text());return 0
    except BaseException as exc:
        dump(out/'AUDIT_ERROR.json',dict(passed=False,error=repr(exc),traceback=traceback.format_exc(),analytical_incomplete_work_unknown=True));return 1
if __name__=='__main__':sys.exit(main())
