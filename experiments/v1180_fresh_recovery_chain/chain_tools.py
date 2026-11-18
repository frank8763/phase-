from pathlib import Path
import sys,os,time,json,hashlib,importlib.util,math
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1180_fresh_recovery_chain'
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
RESOURCE=apply();sys.path.insert(0,str(R/'experiments/v1179_frozen_recovery_native'))
import recovery_tools as previous
q=previous.q;np=q.np;dump=q.dump;sha=q.sha;read=previous.read;GUARD=q.GUARD;packet=previous.packet;pin=previous.pin
def remaining(w=None):
    w=w or read(O/'ROUND_WINDOW.json');assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'];return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def source_ok():return all(sha(R/n)==h for n,h in read(C/'SOURCE_FREEZE.json')['files'].items())
def task_contract(t):
    assert t['case_id']=='WEST_EAST'and t['seed']==10010001 and t['phase']==.6573753567727383 and t['dynamic']is True
    assert t['start_xy']==[-4.,-2.]and t['goal_xy']==[4.,-2.]and t['start_yaw']==0. and t['historical_prefix_native']==0 and t['native_limit']==60000
    assert t['scope']=='fresh_t0_known_WE_finite_causal_recovery_chain'and t['task_id']==t['role']and t['role']in ['main','repeat']
    assert Path(t['output'])==R/'runs/v858_nav2_verified/v1180'/t['task_id']and t['run_root']==str(O)
    return True
def history_guard(output):
    output=Path(output).resolve()
    def hook(event,args):
        if event!='open'or not args or not isinstance(args[0],(str,bytes)):return
        p=Path(os.fsdecode(args[0])).resolve()
        if p.name in {'NATIVE_TRACE.npz','BODY_COMMANDS.json','SENSORS.json.gz','CONTACTS.json.gz','ACTUAL_CAUSAL_ENTRY_INPUT.json'}and not p.is_relative_to(output):raise AssertionError('FRESH_HISTORY_READ_FORBIDDEN '+p.name)
    sys.addaudithook(hook)
def configure_owner(output,end):
    import kernel
    kernel.O=Path(output);kernel.HARD_END=end
    sys.path.insert(0,str(R/'experiments/rpccr_execution_core'))
    sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
    import planner
    planner.O=Path(output)
    # The old recovery import is deliberately unused: this integration supplies
    # the new chain. Avoid its generic capture-module collision without touching
    # any normal-navigation statement or old scientific file.
    import types
    file=R/'experiments/v1067_causal_replan_brake_reserve/owner.py';source=file.read_text();assert source.count('from execute import execute')==1
    owner=types.ModuleType('v1180_original_normal_owner');owner.__file__=str(file);exec(compile(source.replace('from execute import execute','execute = None'),str(file),'exec'),owner.__dict__)
    import budget
    budget.O=Path(output);budget.RAW=R/'runs/v858_nav2_verified/v1180';budget.LIMIT=2*1024**3
    sys.path.insert(0,str(C));import chain
    owner.execute=lambda *args:chain.execute(*args,output=Path(output))
    return owner
