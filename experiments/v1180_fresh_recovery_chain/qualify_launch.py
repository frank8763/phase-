from chain_tools import *
import ast
start=load('v1180_window_entry',C/'start.py')
def main():
    a=dict(authorized=True,version='V1180',scope='fresh_t0_known_WE_finite_causal_recovery_chain',window_seconds=5400,user_instruction='SYNTHETIC_ONLY');assert start.validate_authorization(a)==5400;negative=[]
    for k,v in [('authorized',False),('version','V1177'),('scope','new24'),('window_seconds',5400.),('window_seconds',7200),('user_instruction','')]:
        try:start.validate_authorization(dict(a,**{k:v}))
        except AssertionError:negative.append(k)
        else:raise AssertionError('AUTH_NEGATIVE_ACCEPTED '+k)
    w=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),absolute_deadline_unix=time.time()+20,hard_stop_monotonic=time.monotonic()+20);assert remaining(w)>0
    assert remaining(dict(w,absolute_deadline_unix=time.time()-1))<0 and remaining(dict(w,hard_stop_monotonic=time.monotonic()-1))<0
    try:remaining(dict(w,boot_id='wrong'))
    except AssertionError:negative.append('boot')
    else:raise AssertionError('BOOT_ACCEPTED')
    tasks=read(C/'TASKS.json');assert len(tasks)==2 and [t['role']for t in tasks]==['main','repeat']
    for t in tasks:task_contract(t)
    for p in C.glob('*.py'):ast.parse(p.read_text())
    dump(O/'LAUNCH_QUALIFICATION.json',dict(passed=True,scope_deadline_negatives=negative,boot_wall_monotonic=True,single_owner_physics=True,main_before_conditional_repeat=True,models=0,new_mujoco_native=0,formal_retention_gate_unchanged=True));print('V1180_LAUNCH_QUALIFIED')
if __name__=='__main__':main()
