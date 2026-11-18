import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('REPEAT_QUALIFICATION_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
from inherited_gate import verify_parent_main,inherited_main
import ast,fcntl,subprocess
def main():
    assert source_ok()and not read(O/'APPROVAL.json')['models_authorized']and not(O/'ROUND_WINDOW.json').exists()
    guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')==GUARD
    f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for p in C.glob('*.py'):ast.parse(p.read_text())
    gate=verify_parent_main();row=inherited_main();assert row['slot']==24 and row['result']['passed']
    tasks=read(C/'TASKS.json');assert len(tasks)==1 and tasks[0]['role']=='development_repeat'
    w=read(R/'runs/v1278_static_partial_reconnection/ROUND_WINDOW.json')
    a=dict(models_authorized=True,synthetic_qualification_only=True,window_seconds=5400,absolute_deadline_unix=w['absolute_deadline_unix'],stop_on_safety_evidence=True,automatic_new24=False,allowed_task_ids=[tasks[0]['task_id']])
    envelope(tasks[0],a,w,entry_check=True)
    negative=[]
    for name,fn in [('wrong_phase',lambda:task_contract(dict(tasks[0],phase=0.))),('main_not_authorized',lambda:task_contract(read(C/'INHERITED_MAIN_TASK.json'))),('synthetic_physical',lambda:envelope(tasks[0],a,w)),('extended_root',lambda:envelope(tasks[0],a,dict(w,absolute_deadline_unix=w['absolute_deadline_unix']+1),entry_check=True))]:
        try:fn()
        except AssertionError:negative.append(name)
        else:raise AssertionError('INVALID_REPEAT_CONTEXT '+name)
    owner=configure_owner(O,time.time()+300,w);assert callable(owner.complete_partial_ready)and callable(owner.execute)
    assert(C/'transition_audit.py').read_bytes()==(R/'experiments/v1279_same_frame_audit/transition_audit.py').read_bytes()
    fixtures=O/'ENTRY_FIXTURES';fixtures.mkdir();dump(fixtures/'APPROVAL.json',a);dump(fixtures/'WINDOW.json',w)
    fcntl.flock(f,fcntl.LOCK_UN)
    try:
        (R/'REVIEW_PENDING').unlink()
        p=subprocess.run([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R)),str(C/'TASK_slot24_repeat.json'),'--entry-check','--approval',str(fixtures/'APPROVAL.json'),'--window',str(fixtures/'WINDOW.json')],cwd=R,capture_output=True,text=True,timeout=30)
        assert p.returncode==0,(p.stdout,p.stderr);entry=json.loads(p.stdout.strip().splitlines()[-1])
    finally:(R/'REVIEW_PENDING').write_bytes(guard)
    cli=[]
    for script,args in [('worker.py',[str(C/'TASK_slot24_repeat.json')]),('audit.py',[str(C/'TASK_slot24_repeat.json')]),('campaign.py',[]),('start.py',[])]:
        p=subprocess.run([sys.executable,'-B',str(C/script),*args],cwd=R,capture_output=True,text=True,timeout=30)
        assert p.returncode!=0 and 'ModuleNotFoundError'not in p.stderr and 'ImportError'not in p.stderr,(script,p.stdout,p.stderr);cli.append(script)
    dump(O/'QUALIFICATION.json',dict(passed=True,models=0,physical_native=0,parent=gate,negative=negative,production_owner_bound=True,CLI_disabled=cli,entry=entry,original_normal_first_command_qualification_reused='runs/v1278_static_partial_reconnection/QUALIFICATION.json'))
    dump(O/'ISOLATED_QUALIFICATION.json',dict(passed=True,entries=[entry]));dump(O/'READY_FOR_REVIEW.json',dict(preparation_gates_passed=True,models_authorized=False));print(json.dumps(dict(passed=True,models=0,physical_native=0)))
if __name__=='__main__':main()
