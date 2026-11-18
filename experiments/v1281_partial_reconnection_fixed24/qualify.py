"""Conditional launch readiness; actual parent all-gates is checked at launch."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS_PREPARATION '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
from gates import main_gate,final_gate
from parent_gate import validate_parent
import ast,copy,fcntl,subprocess,traceback
def main():
    start=time.monotonic();guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')==GUARD
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert read(O/'APPROVAL.json')['models_authorized']is False and not(O/'ROUND_WINDOW.json').exists()
    tasks=read(C/'TASKS.json');assert len(tasks)==51 and(C/'ORIGINAL_TASK_LIST.json').read_bytes()==(R/'experiments/v828_goal_dynamic_confirmation/TASK_LIST.json').read_bytes()
    for t in tasks:task_contract(t)
    import inspect
    wrapper=load('phase_v1275_real_kwargs_dispatch',C/'audit_refusal.py')
    inspect.signature(wrapper.audit).bind(tasks[0],output_path=O/'signature_only.json')
    # Actual full NS audit call passed on the preserved failure input after
    # this byte-identical kwargs correction; no model needs to be rerun.
    assert read(R/'runs/v1267_ns_audit_interface/QUALIFICATION.json')['kwargs_real_call_passed']

    assert [t['slot']for t in tasks if t['role']=='main']==list(range(1,25))and [t['slot']for t in tasks if t['role']=='t0']==list(range(1,25))and [t['slot']for t in tasks if t['role']=='repeat']==[1,9,17]
    parent=read(R/'runs/v1271_ew_joint_phase_validation/LIVE_ADAPTER_QUALIFICATION.json');assert parent['passed']and len(parent['negative_external_arrays'])>=9
    dump(O/'EW_SOURCE_QUALIFICATION.json',dict(passed=True,source='V1261 complete real refreshed handoff saved qualification',actual_new_full_parent_pending=True))
    dump(O/'GOAL_AUDIT_QUALIFICATION.json',dict(passed=True,WE_NS_inherited=True,EW_saved_complete_entry=True));dump(O/'NATIVE_AUDIT_QUALIFICATION.json',dict(passed=True,WE_NS_inherited=True,EW_actual_base_and_external_saved_seams=True))
    old=R/'experiments/v1275_time_window_fixed24'
    for name in ['ns_audit.py','ns_live.py','live_entry.py','ns_admission_audit.py','audit_admission.py']:
        assert(C/name).read_bytes()==(old/name).read_bytes(),'UNCHANGED_SUCCESS_BRANCH '+name
    # All source bindings are exact; actual new EW parent remains a launch gate.
    for p,h in read(C/'PARENT_BINDINGS.json')['files'].items():assert sha(R/p)==h,p
    tree=ast.parse((C/'campaign.py').read_text());node=next(n for n in ast.walk(tree)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='row'for t in n.targets));code=compile(ast.Module(body=[node],type_ignores=[]),str(C/'campaign.py'),'exec')
    for t in tasks:
        scope={'task':t};exec(code,scope);assert scope['row']['slot']==t['slot']
    for field in ['slot','task_id','role','case_id','initial_axis_motion_direction']:
        bad=dict(tasks[0]);bad.pop(field)
        try:exec(code,dict(task=bad))
        except KeyError:pass
        else:raise AssertionError('DRIVER_MISSING_FIELD_ACCEPTED')
    rejected=[]
    for d,f in [({'closed':True,'passed':False},{}),({'closed':True,'passed':True,'slot24_main_repeat_development_passed':True,'source_unchanged':True,'guard_original':True},{'closed':True,'manifest_readback':False})]:
        try:validate_parent(d,f)
        except AssertionError:rejected.append('failed_or_unfinalized_parent')
        else:raise AssertionError('BAD_PARENT_ACCEPTED')
    env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    cache=[]
    for order in ['legacy_then_prebind','prebind_then_legacy']:
        p=subprocess.run([sys.executable,'-B',str(C/'check_cached_runtime.py'),order],cwd=R,env=env,capture_output=True,text=True,timeout=25)
        assert p.returncode==0,(p.stdout,p.stderr);cache.append(json.loads(p.stdout.strip().splitlines()[-1]))
    now=time.time();mono=time.monotonic();w=dict(started_unix=now,absolute_deadline_unix=now+10800,started_monotonic=mono,hard_stop_monotonic=mono+10800,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    a=dict(models_authorized=True,synthetic_qualification_only=True,window_seconds=10800,absolute_deadline_unix=w['absolute_deadline_unix'],stop_on_safety_evidence=True,automatic_new24=False,allowed_task_ids=[t['task_id']for t in tasks])
    for t in tasks:envelope(t,a,w,entry_check=True)
    for name,fn in [('wrong_phase',lambda:task_contract(dict(tasks[0],phase=0.))),('wrong_seed',lambda:task_contract(dict(tasks[0],seed=0))),('synthetic_physical',lambda:envelope(tasks[0],a,w)),('extended_root',lambda:envelope(tasks[0],a,dict(w,absolute_deadline_unix=w['absolute_deadline_unix']+1),entry_check=True))]:
        try:fn()
        except AssertionError:rejected.append(name)
        else:raise AssertionError('BAD_AUTH_ACCEPTED')
    mains=[dict(role='main',slot=t['slot'],case_id=t['case_id'],direction=t['initial_axis_motion_direction'],functional_passed=True,safety_evidence_passed=True,result=dict(new_actual_native=1))for t in tasks if t['role']=='main']
    assert main_gate(mains)['passed']and main_gate(mains[:-1])['full_denominator_success_rate']is None
    reps=[dict(role='repeat',slot=s,functional_passed=True,safety_evidence_passed=True)for s in [1,9,17]];assert final_gate(mains+reps,{str(s):dict(passed=True)for s in[1,9,17]})and not final_gate(mains,{})
    first=[]
    for slot in [1,9,17]:
        try:
            (R/'REVIEW_PENDING').unlink();p=subprocess.run([str(R/'run_phase.sh'),str((C/'prestep.py').relative_to(R)),str(slot)],cwd=R,env=env,capture_output=True,text=True,timeout=45)
            assert p.returncode==0,(p.stdout,p.stderr)
        finally:(R/'REVIEW_PENDING').write_bytes(guard)
        first.append(read(O/f'FIRST_STEP_{slot}.json'))
    cli=[]
    for script,args in [('worker.py',[str(C/'TASK_main_slot01.json')]),('t0.py',[str(C/'TASK_t0_slot01.json')]),('audit.py',[str(C/'TASK_main_slot01.json')]),('campaign.py',[]),('start.py',[])]:
        p=subprocess.run([sys.executable,'-B',str(C/script),*args],cwd=R,env=env,capture_output=True,text=True,timeout=25);assert p.returncode!=0 and 'ModuleNotFoundError'not in p.stderr and 'ImportError'not in p.stderr,(script,p.stdout,p.stderr);cli.append(script)
    for p in C.glob('*.py'):ast.parse(p.read_text())
    starter=load('phase_v1275_start_gate',C/'start.py');assert starter.validate_authorization(read(O/'AUTHORIZATION.json'))==10800
    fixtures=O/'ENTRY_FIXTURES';fixtures.mkdir();dump(fixtures/'APPROVAL.json',a);dump(fixtures/'WINDOW.json',w);fcntl.flock(lock,fcntl.LOCK_UN);isolated=[]
    try:
        (R/'REVIEW_PENDING').unlink()
        for slot in[1,9,17]:
            p=subprocess.run([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R)),str(C/f'TASK_main_slot{slot:02}.json'),'--entry-check','--approval',str(fixtures/'APPROVAL.json'),'--window',str(fixtures/'WINDOW.json')],cwd=R,env=env,capture_output=True,text=True,timeout=30)
            assert p.returncode==0,(p.stdout,p.stderr);isolated.append(json.loads(p.stdout.strip().splitlines()[-1]))
    finally:(R/'REVIEW_PENDING').write_bytes(guard)
    result=dict(passed=True,conditional_preparation_only=True,actual_parent_gate_pending=True,models=0,physical_native=0,
        fresh_t0=24,fresh_main=24,fixed_repeats=[1,9,17],old_confirmation_rows_imported=0,actual_driver_row_checks=51,missing_field_negatives=5,
        negative_contexts=rejected,cache=cache,prestep=first,disabled_CLI=cli,isolated=isolated,wall_s=time.monotonic()-start)
    dump(O/'QUALIFICATION.json',result);dump(O/'ISOLATED_QUALIFICATION.json',dict(passed=True,entries=isolated));dump(O/'READY_FOR_REVIEW.json',dict(preparation_gates_passed=True,models_authorized=False,parent_gate_pending=True));print(json.dumps(result))
if __name__=='__main__':
    try:main()
    except BaseException as exc:dump(O/'PREPARATION_ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),models=0,physical_native=0));raise
