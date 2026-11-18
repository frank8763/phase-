from gap_tools import *
import ast,copy
start=load('v1177_new_window_entry',C/'start.py')
def main():
    a=dict(authorized=True,version='V1177',scope='fixed_three_static_response_components_and_conditional_repeats',window_seconds=5400,user_instruction='SYNTHETIC_QUALIFICATION_ONLY');assert start.validate_authorization(a)==5400
    negatives=[]
    for k,v in [('authorized',False),('version','V1157'),('scope','new24'),('window_seconds',5400.),('window_seconds',7200),('user_instruction','')]:
        try:start.validate_authorization(dict(a,**{k:v}))
        except AssertionError:negatives.append(k)
        else:raise AssertionError('AUTH_NEGATIVE_ACCEPTED '+k)
    w=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),absolute_deadline_unix=time.time()+20,hard_stop_monotonic=time.monotonic()+20);assert remaining(w)>0
    assert remaining(dict(w,absolute_deadline_unix=time.time()-1))<0 and remaining(dict(w,hard_stop_monotonic=time.monotonic()-1))<0
    try:remaining(dict(w,boot_id='wrong'))
    except AssertionError:negatives.append('boot')
    else:raise AssertionError('BOOT_ACCEPTED')
    tasks=read(C/'TASKS.json');assert len(tasks)==6
    assert [(t['component'],t['role'])for t in tasks]==[(c,r)for c in ['rate','lateral','low']for r in ['main','repeat']]
    assert sum(t['planned_native']for t in tasks)==35200
    for t in tasks:task_contract(t);plan_for(t)
    for file in C.glob('*.py'):ast.parse(file.read_text())
    dump(O/'LAUNCH_QUALIFICATION.json',dict(passed=True,authorization_negatives=negatives,boot_wall_monotonic=True,task_order_main_before_repeat=True,full_success_actual_native=35200,physical_control_instances=1,offline_audit_workers=4,models=0,physical_native=0,new_window_opened=False));print('LAUNCH_SCOPE_DEADLINE_QUALIFIED')
if __name__=='__main__':main()
