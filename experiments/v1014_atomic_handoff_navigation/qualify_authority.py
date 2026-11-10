"""Exercise actual authority functions against isolated small data fixtures."""
import copy,hashlib,importlib.abc,json,sys,tempfile
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1014_atomic_handoff_navigation'
sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','rclpy','physical','vehicle'}:raise AssertionError('NO_MODEL_AUTHORITY_TEST '+name)
sys.meta_path.insert(0,NoModel())
import authority as a
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x)+'\n')
def main():
    tasks=a.read(C/'TASKS.json');old=(a.R,a.C,a.O,a.ROOT);cases=[]
    with tempfile.TemporaryDirectory(prefix='authority-',dir=O)as td:
        f=Path(td);a.R=f;a.C=f/'C';a.O=f/'O';a.ROOT=f/'ROOT';now=1794313000.
        dump(a.C/'SOURCE_FREEZE.json',dict(files={}));freeze=a.sha(a.C/'SOURCE_FREEZE.json');dump(a.C/'TASKS.json',tasks)
        dump(f/'records/nav2_v1003_20261110/FINAL_INDEPENDENT_AUDIT.json',dict(component_passed=True))
        dump(f/'records/nav2_v1010_20261110/FINAL_INDEPENDENT_AUDIT.json',dict(passed=True));dump(a.O/'ZERO_MODEL_QUALIFICATION.json',dict(passed=True));dump(a.O/'SAVED_AUDIT_QUALIFICATION.json',dict(passed=True));dump(f/'records/nav2_v1013_20261110/HANDOFF_QUALIFICATION.json',dict(passed=True))
        approval=dict(models_authorized=True,source_freeze_sha256=freeze,conditional_overnight=False)
        window=dict(started_unix=now-1,deadline_unix=now-1+5400.)
        dump(a.ROOT/'APPROVAL.json',approval);dump(a.ROOT/'ROUND_WINDOW.json',window)
        def receipt(t):return dict(a.root_authorized(now,freeze),run_id=t['run_id'],task_sha256=a.digest(t))
        def reject(label,call):
            try:call()
            except (AssertionError,FileNotFoundError):cases.append(dict(case=label,passed=True));return
            raise AssertionError('INVALID_AUTHORITY_ACCEPTED '+label)
        assert a.authorized(tasks[0],receipt(tasks[0]),now,freeze)==window['deadline_unix'];cases.append(dict(case='new_bounded_WE_main',passed=True))
        reject('overnight_without_approval',lambda:a.authorized(tasks[2],receipt(tasks[2]),now,freeze))
        reject('repeat_before_main',lambda:a.authorized(tasks[1],receipt(tasks[1]),now,freeze))
        dump(a.O/'RESULTS.json',[dict(passed=True)]);assert a.authorized(tasks[1],receipt(tasks[1]),now,freeze)==window['deadline_unix']
        cases.append(dict(case='repeat_after_success',passed=True))
        approval['models_authorized']=False;dump(a.ROOT/'APPROVAL.json',approval);reject('models_disabled',lambda:a.root_authorized(now,freeze))
        approval['models_authorized']=True;approval['conditional_overnight']=True;dump(a.ROOT/'APPROVAL.json',approval)
        dump(a.O/'RESULTS.json',[dict(passed=True),dict(passed=False)]);reject('night_after_failed_main',lambda:a.authorized(tasks[2],receipt(tasks[2]),now,freeze))
        dump(a.O/'RESULTS.json',[dict(passed=True),dict(passed=True)]);dump(a.O/'NIGHT_WINDOW.json',dict(deadline_unix=1794355200.,source_freeze_sha256=freeze))
        assert a.authorized(tasks[2],receipt(tasks[2]),now,freeze)==1794355200.;cases.append(dict(case='conditional_night_after_both_WE_gates',passed=True))
        reject('confirmation_before_all_three_routes',lambda:a.authorized(tasks[6],receipt(tasks[6]),now,freeze))
        wrong=copy.deepcopy(tasks[0]);wrong['phase']+=.01;reject('changed_registered_task',lambda:a.authorized(wrong,receipt(wrong),now,freeze))
        changed=dict(window,deadline_unix=window['deadline_unix']+1);dump(a.ROOT/'ROUND_WINDOW.json',changed);reject('extended_deadline',lambda:a.root_authorized(now,freeze))
        dump(a.ROOT/'ROUND_WINDOW.json',window);dump(a.ROOT/'COMPLETION.json',dict(closed=True));reject('closed_batch',lambda:a.root_authorized(now,freeze))
    a.R,a.C,a.O,a.ROOT=old
    result=dict(passed=True,cases=cases,models=0,integrations=0,actual_authority_functions_exercised=True)
    dump(O/'AUTHORITY_QUALIFICATION.json',result);print(json.dumps(dict(passed=True,authority_cases=len(cases),models=0)))
if __name__=='__main__':main()
