from pathlib import Path
import sys,json,math,os,time,hashlib,importlib.util
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1179_frozen_recovery_native'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
RESOURCE=apply()
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
q=load('v1179_unchanged_science',R/'experiments/v1160_safe_terminal_connection/search.py');np=q.np;dump=q.dump;sha=q.sha;GUARD=q.GUARD
PARENT=R/'runs/v858_nav2_verified/v1148/component_main';HISTORY=34723
def read(p):return json.loads(Path(p).read_text())
def remaining(w=None):
    w=w or read(O/'ROUND_WINDOW.json');assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'];return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def source_ok():return all(sha(R/n)==h for n,h in read(C/'SOURCE_FREEZE.json')['files'].items())
def pin():
    for p in Path('/proc/self/task').iterdir():
        try:os.sched_setaffinity(int(p.name),{2});os.sched_setscheduler(int(p.name),os.SCHED_IDLE,os.sched_param(0))
        except ProcessLookupError:pass
def packet(v):
    b=list(v.body());e=v.steering_sample();now=time.monotonic()
    return dict(body=b,body_lateral=float(-v.d.qvel[0]*math.sin(b[2])+v.d.qvel[1]*math.cos(b[2])),native_tick=v.count,sim_time=float(v.d.time),body_measured_at=now,sent_at=now,dynamic_discovered=bool(v.first_detection is not None),steering=dict(position=e[:2].tolist(),velocity=e[2:].tolist(),native_tick=v.count,measured_at=now),controller_memory=dict(last_ctrl=v.adapter.last.tolist(),integral=float(v.adapter.integral)),coupled_episode=False,steering_motion_active=False)
def body_gate(p):
    b=p['body'];assert np.isfinite([*b,p['body_lateral'],*p['steering']['position'],*p['steering']['velocity']]).all()
    assert abs(b[3])<=.13 and abs(b[4])<=.16 and abs(p['body_lateral'])<=.03,'ACTUAL_BODY_CAP'
def stopped(p):return abs(np.array(p['body'][3:])).max()<=.003 and abs(np.array(p['steering']['velocity'])).max()<=.015
def load_reference():
    with np.load(R/'runs/v1163_joint_timing_repair/REFERENCE.npz')as z:ref={k:z[k].copy()for k in z.files}
    rows=read(R/'experiments/v1163_joint_timing_repair/TASKS.json')['rows'];schedule=[(float(t),float(v))for t,v,n,mode in rows for _ in range(n)];assert len(schedule)==5885
    return ref,schedule
def task_contract(t):
    assert t['case_id']=='WEST_EAST'and t['seed']==10010001 and t['phase']==.6573753567727383 and t['dynamic']is True
    assert t['start_xy']==[-4.,-2.]and t['goal_xy']==[4.,-2.]and t['start_yaw']==0.
    assert t['task_id']==t['role']and t['role']in ['main','repeat']and t['native_limit']==43408
    assert t['scope']=='fixed_original_saved_recovery_native_qualification'and t['historical_prefix_native']==HISTORY
    assert Path(t['output'])==R/'runs/v858_nav2_verified/v1179'/t['task_id']and t['run_root']==str(O)
    return True
