"""Affected real call sites, immutable prefix reproduction, authority negatives."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('QUALIFICATION_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
import ast,copy,fcntl,subprocess,types
def main():
    guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')==GUARD
    assert not read(O/'APPROVAL.json')['models_authorized']and not(O/'ROUND_WINDOW.json').exists()
    assert source_ok()and read(O/'SAVED_STATE_QUALIFICATION.json')['passed']
    begin=time.monotonic();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for p in C.glob('*.py'):ast.parse(p.read_text())
    repro=load('phase_v1278_actual_recorded_repro',C/'reproduce.py')
    red=repro.run(R/'experiments/v1067_causal_replan_brake_reserve/owner.py');green=repro.run(C/'owner.py')
    assert red['error']=='REAL_SENSOR_DISCOVERY_REQUIRED'and not red['next_renewal_reached']
    assert green['next_renewal_reached']and green['recorded_native_checked']==16930
    dump(O/'ACTUAL_NAVIGATION_RED_GREEN.json',dict(passed=True,red=red,green=green))
    tasks=read(C/'TASKS.json');assert len(tasks)==2
    now=time.time();mono=time.monotonic();w=dict(started_unix=now,absolute_deadline_unix=now+5400,started_monotonic=mono,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    a=dict(models_authorized=True,synthetic_qualification_only=True,window_seconds=5400,absolute_deadline_unix=w['absolute_deadline_unix'],stop_on_safety_evidence=True,automatic_new24=False,allowed_task_ids=[t['task_id']for t in tasks])
    for task in tasks:envelope(task,a,w,entry_check=True)
    negative=[]
    for label,fn in [('wrong_seed',lambda:task_contract(dict(tasks[0],seed=0))),('wrong_phase',lambda:task_contract(dict(tasks[0],phase=0.))),('synthetic_physical',lambda:envelope(tasks[0],a,w)),('extended_root',lambda:envelope(tasks[0],a,dict(w,absolute_deadline_unix=w['absolute_deadline_unix']+1),entry_check=True))]:
        try:fn()
        except AssertionError:negative.append(label)
        else:raise AssertionError('INVALID_CONTEXT_ACCEPTED '+label)
    owner=configure_owner(O,time.time()+300,w);assert owner.complete_partial_ready.__module__=='phase_v1278_normal_owner'
    parent=R/'runs/v858_nav2_verified/v1275/main_slot24';setup=read(parent/'physics/SETUP.json');p0=read(parent/'CANONICAL_INITIAL_PACKET.json')
    import gzip
    with gzip.open(parent/'physics/SENSORS.json.gz','rt')as f:scan=json.load(f)[0]
    requests=[]
    class FirstStep(BaseException):pass
    class Interface:
        count=0;d=types.SimpleNamespace(time=0.);adapter=types.SimpleNamespace(last=np.asarray(p0['controller_memory']['last_ctrl']),integral=0.)
        def body(self):return p0['body']
        def steering_sample(self):return np.asarray(p0['steering']['position']+p0['steering']['velocity'])
        def scan(self):return copy.deepcopy(scan)
        def step(self,*args):requests.append(args);raise FirstStep()
    out=O/'FIRST_COMMAND';out.mkdir()
    try:owner.navigate(Interface(),setup,tasks[0],time.time()+300,out,{})
    except FirstStep:pass
    assert len(requests)==1 and read(out/'00_STATIC_00_PLAN.json')['passed']
    with np.load(parent/'physics/NATIVE_TRACE.npz')as z:assert len(z['time'])==16930
    # Actual audit call seam and normalized CLI are reused, not signature-only mocks.
    original=R/'experiments/v1275_time_window_fixed24'
    unchanged=[n for n in ['base_safety.py','ew_audit.py','audit_chain.py','audit_time.py','PROPOSAL.json']if sha(C/n)==sha(original/n)]
    assert len(unchanged)==5
    fixtures=O/'ENTRY_FIXTURES';fixtures.mkdir();dump(fixtures/'APPROVAL.json',a);dump(fixtures/'WINDOW.json',w)
    fcntl.flock(lock,fcntl.LOCK_UN);entries=[]
    try:
        (R/'REVIEW_PENDING').unlink()
        for task in tasks:
            p=subprocess.run([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R)),str(C/('TASK_'+task['task_id']+'.json')),'--entry-check','--approval',str(fixtures/'APPROVAL.json'),'--window',str(fixtures/'WINDOW.json')],cwd=R,capture_output=True,text=True,timeout=30)
            assert p.returncode==0,(p.stdout,p.stderr);entries.append(json.loads(p.stdout.strip().splitlines()[-1]))
    finally:(R/'REVIEW_PENDING').write_bytes(guard)
    cli=[]
    for script,args in [('worker.py',[str(C/'TASK_slot24_main.json')]),('audit.py',[str(C/'TASK_slot24_main.json')]),('campaign.py',[]),('start.py',[])]:
        p=subprocess.run([sys.executable,'-B',str(C/script),*args],cwd=R,capture_output=True,text=True,timeout=25)
        assert p.returncode!=0 and 'ModuleNotFoundError'not in p.stderr and 'ImportError'not in p.stderr,(script,p.stdout,p.stderr)
        cli.append(script)
    # No previous successful source changed. All23 never encounter new transition.
    rows=read(R/'runs/v1275_time_window_fixed24/RESULTS.json');prefix_untouched=[]
    for row in rows:
        if row['role']=='main'and row['slot']<24:
            segments=read(Path(next(t for t in read(original/'TASKS.json')if t['task_id']==row['stage'])['output'])/'DIRECT_SEGMENTS.json')
            assert not any(s['status']=='COMPLETE'and s['source_kind']=='SAFE_PROGRESS_NOT_ARRIVAL'for s in segments)
            prefix_untouched.append(row['slot'])
    assert len(prefix_untouched)==23
    dump(O/'QUALIFICATION.json',dict(passed=True,models=0,physical_native=0,negative_contexts=negative,
        actual_recorded_red_green=True,saved_static_next_plan=True,unchanged_success_branches=prefix_untouched,
        original_ew_audit_files_byte_identical=unchanged,normal_first_command=list(requests[0]),CLI_disabled=cli,
        isolated_entry_checks=entries,actual_goal_main_not_yet_executed=True,wall_s=time.monotonic()-begin))
    dump(O/'ISOLATED_QUALIFICATION.json',dict(passed=True,entries=entries));dump(O/'READY_FOR_REVIEW.json',dict(preparation_gates_passed=True,models_authorized=False))
    print(json.dumps(dict(passed=True,models=0,physical_native=0,wall_s=time.monotonic()-begin)))
if __name__=='__main__':main()
