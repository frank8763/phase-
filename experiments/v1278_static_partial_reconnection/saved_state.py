"""Saved real state: real renewed static plan and complete braking checks."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('SAVED_STATE_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from worker_context import *
import ast,copy,fcntl,signal
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SAVED_STATE_120S')));signal.alarm(120)
    old=science();q=old.q;np=q.np
    window=dict(started_unix=time.time(),absolute_deadline_unix=time.time()+5400,started_monotonic=time.monotonic(),hard_stop_monotonic=time.monotonic()+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    owner=configure_owner(O,time.time()+300,window)
    parent=R/'runs/v858_nav2_verified/v1275/main_slot24';p=read(parent/'ACTUAL_FINAL_PACKET.json');setup=read(parent/'physics/SETUP.json');plan=read(parent/'02_STATIC_01_PLAN.json')
    assert owner.complete_partial_ready(plan,p)
    negative=[]
    for label in ['moving_body','moving_steering','drive_not_zero','fake_discovery','wrong_kind','goal_alias','short_tail','failed_safety']:
        pp=copy.deepcopy(p);ss=copy.deepcopy(plan)
        if label=='moving_body':pp['body'][3]=.04
        elif label=='moving_steering':pp['steering']['velocity'][0]=.04
        elif label=='drive_not_zero':pp['controller_memory']['last_ctrl'][-1]=.1
        elif label=='fake_discovery':pp['dynamic_discovered']=True
        elif label=='wrong_kind':ss['source_kind']='UNKNOWN'
        elif label=='goal_alias':ss['functional_goal_source']=True
        elif label=='short_tail':ss['planned_body_requests']=ss['planned_body_requests'][-199:]
        else:ss['checks']['legal_ctrl']=False
        try:owner.complete_partial_ready(ss,pp)
        except AssertionError:negative.append(label)
        else:raise AssertionError('PARTIAL_TRANSITION_NEGATIVE_ACCEPTED '+label)
    # Reuse the completed fixed10 probe; no more blind search budgets.
    renewed=read(O/'TWO_STAGE_SAVED_PLAN.json');records=read(O/'TWO_STAGE_FIXED_RECORDS.json')
    assert renewed['passed']and len(records)==10 and [r['index']for r in records]==list(range(10))
    assert renewed['static_reconnection']['record']['index']==next(r['index']for r in records if r['passed'])
    from fresh import finite_plan
    from recovery_source import forecast_packet
    task=read(C/'TASK_slot24_main.json');begin=time.monotonic()
    check=finite_plan(setup,p,None,renewed['planned_body_requests'],'INDEPENDENT_SAVED_STATIC_RENEWAL')
    dump(O/'SAVED_RENEWED_FINITE_CHECK.json',check);assert check['passed']and all(check['checks'].values())
    assert abs(np.asarray(renewed['state_path'])-np.asarray(check['state_path'])).max()<=1e-8
    # A separate complete recurrence also checks state/control/stop/goal contracts.
    ss=np.asarray(check['state_path']);uu=np.asarray(check['predicted_actuator_controls']);rr=np.asarray(check['planned_body_requests'])
    import kernel
    cc,upper=kernel.checks(ss,uu,rr,p,setup,np.asarray(task['goal_xy']),check['minimum_raw_m'],kernel.REQUIRED)
    safety=dict(cc);safety.pop('goal_upper');assert all(safety.values())
    assert cc['goal_upper']==renewed['functional_goal_source']
    dump(O/'INDEPENDENT_SAVED_RECONNECTION_CHECK.json',dict(passed=True,checks=cc,goal_upper_m=upper,models=0,physical_native=0))
    report=dict(passed=True,models=0,physical_native=0,actual_navigation_not_yet_executed=True,
        negative_rejections=negative,saved_state_native=p['native_tick'],renewed_native=len(renewed['planned_body_requests']),
        functional_goal_source=renewed['functional_goal_source'],static_renewal_wall_s=time.monotonic()-begin,
        analytical_cpp_native=None,analytical_python_native=None,analytical_counts_unknown=True)
    dump(O/'SAVED_STATE_QUALIFICATION.json',report);print(json.dumps(report))
if __name__=='__main__':main()
