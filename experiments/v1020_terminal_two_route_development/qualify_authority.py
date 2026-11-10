"""Real authorization and branch gates against isolated data; zero models."""
import copy,json,sys,tempfile
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1020_terminal_two_route_development'
sys.path.insert(0,str(C));import authority as a
from branch_policy import skip_repeat,can_confirm,failure_action

def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x)+'\n')
def main():
    tasks=a.read(C/'TASKS.json');old=(a.R,a.C,a.O,a.ROOT);cases=[]
    with tempfile.TemporaryDirectory(prefix='authority-',dir=O)as td:
        f=Path(td);a.R=f;a.C=f/'C';a.O=f/'O';a.ROOT=f/'ROOT';now=1794318000.
        dump(a.C/'SOURCE_FREEZE.json',dict(files={}));freeze=a.sha(a.C/'SOURCE_FREEZE.json');dump(a.C/'TASKS.json',tasks)
        dump(f/'records/nav2_v1003_20261110/FINAL_INDEPENDENT_AUDIT.json',dict(component_passed=True));dump(f/'records/nav2_v1010_20261110/FINAL_INDEPENDENT_AUDIT.json',dict(passed=True));dump(f/'records/nav2_v1019_20261110/ZERO_MODEL_QUALIFICATION.json',dict(passed=True));dump(f/'records/nav2_v1013_20261110/HANDOFF_QUALIFICATION.json',dict(passed=True))
        for name in ['ZERO_MODEL_QUALIFICATION.json','SAVED_AUDIT_QUALIFICATION.json','BACKEND_ENTRY_QUALIFICATION.json','AUTHORITY_QUALIFICATION.json','SCIENTIFIC_ENTRY_QUALIFICATION.json','INITIAL_ZERO_QUALIFICATION.json']:dump(a.O/name,dict(passed=True))
        dump(f/'runs/atomic_handoff_night_20261110/COMPLETION.json',dict(closed=True))
        approval=dict(models_authorized=True,source_freeze_sha256=freeze,new_night_authorized=True,independent_route_branches=True)
        window=dict(started_unix=now-1,deadline_unix=a.HARD_END)
        dump(a.ROOT/'APPROVAL.json',approval);dump(a.ROOT/'ROUND_WINDOW.json',window);dump(a.ROOT/'PARENT_WINDOW.json',window)
        def receipt(t):return dict(a.root_authorized(now,freeze),run_id=t['run_id'],task_sha256=a.digest(t))
        def reject(label,call):
            try:call()
            except(AssertionError,FileNotFoundError):cases.append(dict(case=label,passed=True));return
            raise AssertionError('INVALID_AUTHORITY_ACCEPTED '+label)
        assert a.authorized(tasks[0],receipt(tasks[0]),now,freeze)==a.HARD_END;cases.append(dict(case='new_night_original_main',passed=True))
        reject('repeat_before_main',lambda:a.authorized(tasks[1],receipt(tasks[1]),now,freeze))
        dump(a.O/'RESULTS.json',[dict(passed=True)]);assert a.authorized(tasks[1],receipt(tasks[1]),now,freeze)==a.HARD_END
        cases.append(dict(case='repeat_after_success',passed=True))
        dump(a.O/'RESULTS.json',[dict(passed=False),dict(passed=False,executed=False)])
        assert a.authorized(tasks[2],receipt(tasks[2]),now,freeze)==a.HARD_END;cases.append(dict(case='independent_NS_after_pure_WE_function_failure',passed=True))
        reject('confirmation_after_route_failure',lambda:a.authorized(tasks[4],receipt(tasks[4]),now,freeze))
        dump(a.O/'RESULTS.json',[dict(passed=True,executed=True)]*4);assert a.authorized(tasks[4],receipt(tasks[4]),now,freeze)==a.HARD_END
        cases.append(dict(case='confirmation_after_all_six',passed=True))
        wrong=copy.deepcopy(tasks[0]);wrong['phase']+=.01;reject('changed_task',lambda:a.authorized(wrong,receipt(wrong),now,freeze))
        approval['models_authorized']=False;dump(a.ROOT/'APPROVAL.json',approval);reject('disabled',lambda:a.root_authorized(now,freeze))
        approval['models_authorized']=True;dump(a.ROOT/'APPROVAL.json',approval)
        dump(a.ROOT/'ROUND_WINDOW.json',dict(window,deadline_unix=a.HARD_END+1));reject('deadline_extended',lambda:a.root_authorized(now,freeze))
        dump(a.ROOT/'ROUND_WINDOW.json',window);reject('after_absolute_deadline',lambda:a.root_authorized(a.HARD_END,freeze))
        dump(a.ROOT/'COMPLETION.json',dict(closed=True));reject('closed_root',lambda:a.root_authorized(now,freeze))
    a.R,a.C,a.O,a.ROOT=old
    failed=dict(passed=False,evidence_passed=True,stage='development')
    assert skip_repeat(tasks[1],[failed]);assert failure_action(tasks[0],failed,[failed])=='CONTINUE_INDEPENDENT_ROUTE'
    assert failure_action(tasks[0],dict(failed,evidence_passed=False),[failed])=='STOP_ALL_SAFETY_OR_EVIDENCE'
    assert not can_confirm([dict(passed=True)]*3+[failed]);assert can_confirm([dict(passed=True)]*4)
    mains=[dict(stage='development_sweep16',passed=False,evidence_passed=True)]*2
    assert failure_action(tasks[4],mains[0],mains[:1])=='CONTINUE';assert failure_action(tasks[5],mains[1],mains)=='STOP_SECOND_CONFIRMATION_FUNCTION'
    for name in ['skip_failed_main_repeat','pure_function_other_route_continues','safety_stops_all','no_confirmation_after_failed_route','confirmation_after_six','first_confirmation_function_continues','second_confirmation_function_stops']:cases.append(dict(case=name,passed=True))
    result=dict(passed=True,models=0,integrations=0,cases=cases,actual_functions_exercised=True)
    dump(O/'AUTHORITY_QUALIFICATION.json',result);print(json.dumps(dict(passed=True,cases=len(cases),models=0)))
if __name__=='__main__':main()
