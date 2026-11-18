"""Full saved chain for EW functional refusal, original base for other routes."""
from campaign_context import *
import fcntl,signal
def audit(task,*args,**kwargs):
    name='ew_audit.py'if task['case_id']=='EAST_WEST'else'base_safety.py'
    return load('phase_v1275_refusal_dispatch',C/name).audit(task,*args,**kwargs)
if __name__=='__main__':
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SAVED_REFUSAL_AUDIT_300S')));signal.alarm(300)
    f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    task=read(Path(sys.argv[1]));audit(task);print((Path(task['output'])/'FINAL_INDEPENDENT_AUDIT.json').read_text())
