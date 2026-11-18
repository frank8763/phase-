from pathlib import Path
import sys,json,os,time,hashlib,importlib.util
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1177_gap_response_execution'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
RESOURCE=apply()
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
q=load('v1177_qualified_predictor_bindings',R/'experiments/v1160_safe_terminal_connection/search.py')
np=q.np;dump=q.dump;sha=q.sha;GUARD=q.GUARD
def read(p):return json.loads(Path(p).read_text())
def remaining(w=None):
    w=w or read(O/'ROUND_WINDOW.json');assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'BOOT_CHANGED'
    return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def source_ok():return all(sha(R/p)==h for p,h in read(C/'SOURCE_FREEZE.json')['files'].items())
def pin():
    for p in Path('/proc/self/task').iterdir():
        try:os.sched_setaffinity(int(p.name),{2});os.sched_setscheduler(int(p.name),os.SCHED_IDLE,os.sched_param(0))
        except ProcessLookupError:pass
def plan_for(task):
    p=R/task['plan'];assert sha(p)==task['plan_sha256'],'INPUT_PLAN_CHANGED'
    with np.load(p)as z:return {k:z[k].copy()for k in z.files}
def origin(packet):
    return dict(q.initial(packet),steering_load_episode=bool(packet['steering_load_episode']))
def task_contract(task):
    fixture=read(R/'experiments/v1139_afternoon_observer/STATIC_T0_SOURCE_FIXTURE.json')
    contract=load('v1177_static_contract',R/'experiments/v1114_coupled_steering_mode/fixture_contract.py');contract.validate_task(task,fixture)
    assert task in read(C/'TASKS.json')and task['component']in ['rate','lateral','low']
    assert Path(task['output']).is_relative_to(R/'runs/v858_nav2_verified/v1177')
    assert task['role']in ['main','repeat'];return fixture,contract
