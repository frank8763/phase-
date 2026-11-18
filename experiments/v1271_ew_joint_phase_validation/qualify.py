"""Actual startup metadata, normal call site, disabled CLIs and isolated entry."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS_PREPARATION '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
import ast,copy,fcntl,subprocess,types,traceback
def main():
    begin=time.monotonic();guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')==GUARD
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not read(O/'APPROVAL.json')['models_authorized']and not(O/'ROUND_WINDOW.json').exists()and source_ok()
    live=read(O/'LIVE_ADAPTER_QUALIFICATION.json');assert live['passed']and live['missing_actual_future_evidence_rejected']and live['no_onward_steps_after_missing_evidence']and len(live['negative_external_arrays'])>=8
    assert live['joint_saved_inputs']==[17,18,19]and live['records'][0]['original_success_arrays_unchanged']
    tasks=read(C/'TASKS.json');assert len(tasks)==4 and [t['task_id']for t in tasks]==['slot18_main','slot18_repeat','slot19_main','slot19_repeat']
    for task in tasks:task_contract(task)
    for p in C.glob('*.py'):ast.parse(p.read_text())
    tree=ast.parse((C/'campaign.py').read_text());node=next(n for n in ast.walk(tree)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='row'for t in n.targets))
    code=compile(ast.Module(body=[node],type_ignores=[]),str(C/'campaign.py'),'exec')
    for task in tasks:
        scope={'task':task};exec(code,scope);assert scope['row']['slot']in[18,19] and scope['row']['case_id']=='EAST_WEST'
    env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    cached=[]
    for order in ['legacy_then_prebind','prebind_then_legacy']:
        proc=subprocess.run([sys.executable,'-B',str(C/'check_cached_runtime.py'),order],cwd=R,env=env,capture_output=True,text=True,timeout=25)
        assert proc.returncode==0,(proc.stdout,proc.stderr);cached.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    now=time.time();mono=time.monotonic();w=dict(started_unix=now,absolute_deadline_unix=now+5400,started_monotonic=mono,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    a=dict(models_authorized=True,synthetic_qualification_only=True,window_seconds=5400,absolute_deadline_unix=w['absolute_deadline_unix'],stop_on_safety_evidence=True,automatic_new24=False,allowed_task_ids=[t['task_id']for t in tasks])
    for task in tasks:envelope(task,a,w,entry_check=True)
    start=load('phase_v1271_authority_validator',C/'start.py');assert start.validate_authorization(read(O/'AUTHORIZATION.json'))==5400
    negative=[]
    for label,fn in [('wrong_seed',lambda:task_contract(dict(tasks[0],seed=0))),('wrong_phase',lambda:task_contract(dict(tasks[0],phase=0.))),('synthetic_physical',lambda:envelope(tasks[0],a,w)),('extended_root',lambda:envelope(tasks[0],a,dict(w,absolute_deadline_unix=w['absolute_deadline_unix']+1),entry_check=True)),('extended_authority',lambda:start.validate_authorization(dict(read(O/'AUTHORIZATION.json'),window_seconds=7200)))]:
        try:fn()
        except AssertionError:negative.append(label)
        else:raise AssertionError('BAD_AUTHORITY_OR_TASK_ACCEPTED '+label)
    try:
        (R/'REVIEW_PENDING').unlink()
        proc=subprocess.run([str(R/'run_phase.sh'),str((C/'prestep.py').relative_to(R))],cwd=R,env=env,capture_output=True,text=True,timeout=45)
        assert proc.returncode==0,(proc.stdout,proc.stderr)
    finally:(R/'REVIEW_PENDING').write_bytes(guard)
    first=read(O/'NORMAL_FIRST_COMMAND_QUALIFICATION.json');assert first['passed']
    cli=[]
    for script,args in [('worker.py',[str(C/'TASK_slot18_main.json')]),('audit.py',[str(C/'TASK_slot18_main.json')]),('campaign.py',[]),('start.py',[])]:
        proc=subprocess.run([sys.executable,'-B',str(C/script),*args],cwd=R,env=env,capture_output=True,text=True,timeout=25)
        assert proc.returncode!=0 and 'ModuleNotFoundError'not in proc.stderr and 'ImportError'not in proc.stderr,(script,proc.stdout,proc.stderr);cli.append(script)
    fixtures=O/'ENTRY_FIXTURES';fixtures.mkdir();dump(fixtures/'APPROVAL.json',a);dump(fixtures/'WINDOW.json',w)
    fcntl.flock(lock,fcntl.LOCK_UN);isolated=[]
    try:
        (R/'REVIEW_PENDING').unlink()
        for task in tasks:
            proc=subprocess.run([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R)),str(C/('TASK_'+task['task_id']+'.json')),'--entry-check','--approval',str(fixtures/'APPROVAL.json'),'--window',str(fixtures/'WINDOW.json')],cwd=R,env=env,capture_output=True,text=True,timeout=30)
            assert proc.returncode==0,(proc.stdout,proc.stderr);isolated.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    finally:(R/'REVIEW_PENDING').write_bytes(guard)
    result=dict(passed=True,models=0,physical_native=0,real_driver_rows=4,normal_first_command=first['request'],negative_contexts=negative,
        cache=cached,CLI_disabled=cli,isolated_worker_entry_checks=isolated,actual_live_seams_qualified=True,composite_actual_goal_not_yet_executed=True,wall_s=time.monotonic()-begin)
    dump(O/'QUALIFICATION.json',result);dump(O/'ISOLATED_QUALIFICATION.json',dict(passed=True,entries=isolated));dump(O/'READY_FOR_REVIEW.json',dict(preparation_gates_passed=True,models_authorized=False));print(json.dumps(result))
if __name__=='__main__':
    try:main()
    except BaseException as exc:dump(O/'PREPARATION_ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),models=0,physical_native=0));raise
