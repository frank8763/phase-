"""Only new namespace, dispatch, window, full CLI and saved-audit boundaries."""
import importlib.abc
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('QUALIFICATION_ZERO_MODELS '+name)
import sys
sys.meta_path.insert(0,NoModels())
from worker_context import *
import copy,fcntl,gzip,subprocess,types,ast
import route_dispatch as dispatch
import native_audit
from sequence import decision

def main():
    assert not(O/'QUALIFICATION.json').exists()and not read(O/'APPROVAL.json')['models_authorized']
    assert read(R/'runs/v1213_fixed_work_shadow/FIXED_QUALIFICATION/COMPLETION.json')['passed']and read(O/'GOAL_INTEGRATION_QUALIFICATION.json')['passed']
    begin=time.monotonic();guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for t in read(C/'TASKS.json'):task_contract(t)
    for p in C.glob('*.py'):ast.parse(p.read_text())
    # Explicit window binding, including both separate expiration clocks.
    seconds=5400;now=time.time();mono=time.monotonic();w=dict(started_unix=now,absolute_deadline_unix=now+seconds,started_monotonic=mono,hard_stop_monotonic=mono+seconds,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    assert remaining(w)>5000
    assert remaining(dict(w,started_unix=now-6000,absolute_deadline_unix=now-1))<0
    assert remaining(dict(w,started_monotonic=mono-6000,hard_stop_monotonic=mono-1))<0
    policy=dispatch.legacy_policy(lambda:321.)
    assert policy.remaining()==321.
    try:policy.remaining(w)
    except AssertionError:pass
    else:raise AssertionError('LEGACY_WINDOW_OVERRIDE_ACCEPTED')
    try:dispatch.execute(None,{'case':{'id':'NORTH_SOUTH'}},None,0,None,None,None,None,remaining_fn=lambda:-1.)
    except AssertionError as e:assert str(e)=='CURRENT_WINDOW_EXPIRED'
    else:raise AssertionError('EXPIRED_EXECUTION_ACCEPTED')
    assert [dispatch.branch(t)for t in ['NORTH_SOUTH','EAST_WEST','WEST_EAST']]==['legacy_route','legacy_route','current_goal']
    try:dispatch.branch('OTHER')
    except AssertionError:pass
    else:raise AssertionError('UNKNOWN_ROUTE_ACCEPTED')
    assert dispatch.current_executor().__file__.endswith('v1214_shadow_route_integration/live_entry.py')
    # Exercise original normal-owner startup, with each actual saved canonical t0.
    old=science();np=old.np
    checks=[];cpp=py=0
    class BeforeStep(BaseException):pass
    for case in ['NORTH_SOUTH','EAST_WEST','WEST_EAST']:
        prior=R/'runs/v858_nav2_verified/v1184'/('main_'+case)
        setup=read(prior/'physics/SETUP.json');p=read(prior/'CANONICAL_INITIAL_PACKET.json')
        with gzip.open(prior/'physics/SENSORS.json.gz','rt')as f:scan=next(s for s in json.load(f)if s['native_tick']==0)
        owner=configure_owner(O,time.time()+1000,w);requests=[]
        class Interface:
            count=0;d=types.SimpleNamespace(time=p['sim_time'])
            adapter=types.SimpleNamespace(last=np.asarray(p['controller_memory']['last_ctrl']),integral=p['controller_memory']['integral'])
            def body(self):return p['body']
            def steering_sample(self):return np.asarray(p['steering']['position']+p['steering']['velocity'])
            def scan(self):return copy.deepcopy(scan)
            def step(self,*row):requests.append(row);raise BeforeStep()
        output=O/('OWNER_PRE_STEP_'+case);output.mkdir()
        try:owner.navigate(Interface(),setup,next(t for t in read(C/'TASKS.json')if t['case_id']==case and t['role']=='main'),time.time()+1000,output,{})
        except BeforeStep:pass
        else:raise AssertionError('REAL_FIRST_STEP_NOT_REACHED '+case)
        plan=read(output/'00_STATIC_00_PLAN.json');assert len(requests)==1 and plan['passed']and all(plan['checks'].values())
        py+=len(plan['planned_body_requests']);cpp+=4405
        checks.append(dict(case=case,first_request=requests[0],real_saved_initial_state=True,model_steps=0))
    # Full unchanged NS/EW real native audit, writing only a separate qualification output.
    audit_checks=[]
    parent_tasks=read(R/'experiments/v1184_three_route_entry/TASKS.json')
    for case in ['NORTH_SOUTH','EAST_WEST']:
        task=next(t for t in parent_tasks if t['role']=='main'and t['case_id']==case)
        target=O/('SAVED_AUDIT_'+case);target.mkdir()
        before=sha(Path(task['output'])/'FINAL_INDEPENDENT_AUDIT.json')
        result=native_audit.audit(task,qualification_output=target)
        assert result['passed']and result['physical_audit_complete']and sha(Path(task['output'])/'FINAL_INDEPENDENT_AUDIT.json')==before
        cpp+=result['analytical_cpp_native'];audit_checks.append(dict(case=case,native_reviewed=result['native_reviewed'],analytical_cpp_native=result['analytical_cpp_native'],historical_witness_only=True))
    tasks=read(C/'TASKS.json');finished=[];pairs={}
    fake=[dict(task_id=tasks[0]['task_id'],worker_returncode=0,audit_returncode=1,result=dict(passed=True,error=None,own_replay_native=1,new_actual_native=1,replay=dict(passed=True)),audit=dict(passed=True,physical_audit_complete=True,actual_replay_verified=True))]
    assert decision(tasks,fake,{},5400)['reason']=='AUDIT_EXIT_FAILURE'
    assert decision(tasks,finished,pairs,5400)['task_id']==tasks[0]['task_id']
    for task in tasks:
        assert decision(tasks,finished,pairs,5400)['task_id']==task['task_id']
        finished.append(dict(task_id=task['task_id'],result=dict(passed=True,error=None,own_replay_native=1,new_actual_native=1,replay=dict(passed=True)),audit=dict(passed=True,physical_audit_complete=True,actual_replay_verified=True)))
        if task['role']=='repeat':
            assert decision(tasks,finished,pairs,5400)['action']=='WAIT';pairs[task['case_id']]=dict(passed=True)
    assert decision(tasks,finished,pairs,5400)['reason']=='THREE_ROUTES_SIX_NAVIGATIONS_AUDITED'
    assert decision(tasks,[],{},1700)['action']=='STOP'
    assert decision(tasks,[],{},5400,source_ok=False)['action']=='STOP'
    bad=copy.deepcopy(finished);bad[0]['result']['passed']=False;assert decision(tasks,bad,pairs,5400)['action']=='STOP'
    # Actual command imports and disabled admission paths, under exact launch environment.
    env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),PYOPENGL_PLATFORM='osmesa',MUJOCO_GL='osmesa',CUDA_VISIBLE_DEVICES='')
    cli=[]
    for entry,args,rc,expect in [('campaign',[],2,'NEW_USER_WINDOW_REQUIRED'),('worker',[str(C/'TASK_main_NORTH_SOUTH.json')],2,'NO_NEW_MODEL_AUTHORITY'),('native_audit_cli',[str(C/'TASK_main_NORTH_SOUTH.json')],1,'AssertionError'),('launch',[],1,'NO_NEW_ENTRY_AUTHORIZATION')]:
        p=subprocess.run([sys.executable,'-B',str(C/(entry+'.py')),*args],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=15)
        assert p.returncode==rc and expect in p.stdout+p.stderr and 'ModuleNotFoundError'not in p.stderr and 'ImportError'not in p.stderr,(entry,p.stdout,p.stderr)
        cli.append(dict(entry=entry,returncode=p.returncode,expected_refusal=expect,models=0,native_steps=0))
    fixture=O/'ENTRY_FIXTURES';fixture.mkdir();approval=dict(models_authorized=True,synthetic_qualification_only=True,stop_on_first_failure=True,automatic_new24=False,allowed_task_ids=[t['task_id']for t in tasks],window_seconds=5400,absolute_deadline_unix=w['absolute_deadline_unix']);dump(fixture/'APPROVAL.json',approval);dump(fixture/'WINDOW.json',w)
    isolated=[]
    try:
        (R/'REVIEW_PENDING').unlink()
        for case,extra,rc in [('blocked',[],2),('positive',['--entry-check','--approval',str(fixture/'APPROVAL.json'),'--window',str(fixture/'WINDOW.json')],0)]:
            fcntl.flock(lock,fcntl.LOCK_UN)
            try:p=subprocess.run([str(R/'run_phase.sh'),str(C/'worker.py'),str(C/'TASK_main_NORTH_SOUTH.json'),*extra],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=15)
            finally:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            assert p.returncode==rc,(case,p.stdout,p.stderr)
            receipt=json.loads(p.stdout.strip().splitlines()[-1]);assert receipt['models']==receipt['new_mujoco_native']==0 and receipt['physical_started']is False
            isolated.append(dict(case=case,receipt=receipt))
    finally:(R/'REVIEW_PENDING').write_bytes(guard)
    assert not RAW.exists()and not(O/'ROUND_WINDOW.json').exists()
    assert all(sha(R/n)==h for n,h in read(C/'WORKER_FREEZE.json')['files'].items())
    result=dict(closed=True,passed=True,normal_first_step_checks=checks,saved_native_audit_checks=audit_checks,source_math_unchanged=True,full_cli_checks=cli,isolated_entries=isolated,sequence_six_task_gate_passed=True,explicit_window_binding_passed=True,analytical_cpp_native=cpp,analytical_python_native=py,models=0,new_mujoco_native=0,physical_authorized=False,wall_s=time.monotonic()-begin)
    dump(O/'QUALIFICATION.json',result);dump(O/'FULL_CLI_QUALIFICATION.json',dict(passed=True,checks=cli,models=0,native_steps=0));dump(O/'READY_FOR_REVIEW.json',dict(preparation_gates_passed=True,physical_authorized=False,scope='three_known_routes_main_repeat_only'))
    print(json.dumps(result))
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        import traceback
        dump(O/'PREPARATION_ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),models=0,new_mujoco_native=0,analytical_incomplete_counts_unknown=True));raise
