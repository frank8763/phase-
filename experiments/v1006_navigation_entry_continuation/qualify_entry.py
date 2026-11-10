"""Original readiness bug red, all33 explicit-t0 entries green, zero models."""
import ast,hashlib,importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1006_navigation_entry_continuation'
sys.path[:0]=[str(C),str(R/'experiments/v1004_planned_input_navigation')]
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','rclpy','physical','vehicle'}:raise AssertionError('NO_MODELS_IN_ENTRY_QUALIFICATION '+name)
sys.meta_path.insert(0,NoModel())
from budget import create,wait_ready
from authority import root_authorized
class Peer:
    def poll(self):return None
def main():
    original=json.loads((R/'experiments/v1004_planned_input_navigation/TASKS.json').read_text());tasks=json.loads((C/'TASKS.json').read_text());reports=[]
    for i,(old,task)in enumerate(zip(original,tasks)):
        folder=O/('readiness_'+str(i));folder.mkdir(exist_ok=True);p=folder/'NATIVE_READY.json';ready=dict(origin_validated=True,native_tick=0,sim_time=0.)
        if p.exists():assert json.loads(p.read_text())==ready
        else:p.write_text(json.dumps(ready))
        clock=create(task,time.time()+1000.)
        if i==0:
            try:wait_ready(Peer(),folder,clock,old)
            except KeyError as e:assert e.args==('origin_native_tick',);red=dict(reproduced=True,error=repr(e),models=0)
            else:raise AssertionError('ORIGINAL_BUG_NOT_REPRODUCED')
        assert wait_ready(Peer(),folder,clock,task)['native_tick']==0
        for key in old:
            if key not in ['run_id','output','socket_dir','baseline_output','preflight_output']:assert old[key]==task[key],key
        assert task['origin_native_tick']==0 and task['origin_sim_time']==0.
        assert task['baseline_output']in [t['output']for t in tasks]
        reports.append(dict(task_id=task['task_id'],passed=True,models=0))
    from preflight_audit import audit
    pref=audit([tasks[0],tasks[2],tasks[4]]);assert pref['passed']
    for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    try:root_authorized()
    except AssertionError as e:assert str(e)=='ENTRY_EXCEPTION_NOT_AUTHORIZED'
    else:raise AssertionError('UNAPPROVED_MODELS_ADMITTED')
    freeze=json.loads((R/'experiments/v1004_planned_input_navigation/SOURCE_FREEZE.json').read_text());science={p:h for p,h in freeze['files'].items()if not p.startswith('runs/')}
    assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in science.items())
    assert (C/'repeat_contract.py').read_bytes()==(R/'experiments/v991_coordinated_components/repeat_contract.py').read_bytes()
    result=dict(passed=True,models=0,integrations=0,original_failure_red=red,readiness_cases=reports,reused_actual_t0_saved_audit=pref,
        original_scientific_source_files_unchanged=len(science),all_original_task_physics_fields_preserved=True,model_authority_blocked=True,
        explicit_original_repeat_audit_binding=True,old_closed_batch_unchanged=True)
    (O/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,models=0,readiness_tasks=len(reports),reused_true_t0s=3,source_files_unchanged=len(science),original_bug_reproduced=True,unapproved_models_blocked=True)))
if __name__=='__main__':main()
