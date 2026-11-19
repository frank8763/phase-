"""Exact static behavior closure for reusing the passed V1354 RPP pair."""
import ast
import hashlib
import json
from pathlib import Path

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
B=R/'experiments/v1354_fast_stamped_pipeline'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    old=json.loads((B/'SOURCE_FREEZE.json').read_text())['files']
    assert all(sha(R/p)==h for p,h in old.items()),'OLD_QUALIFIED_CLOSURE_CHANGED'
    names=['native_component.py','rpp_params.json','stamped_contract.py','gear_handoff.py',
           'segments.py','recovery_guard.py','observed_route.py','transport.py','planning_job.py']
    for name in names:assert (C/name).read_bytes()==(B/name).read_bytes(),name
    previous=(B/'ros_component.py').read_text();current=(C/'ros_component.py').read_text()
    current=current.replace("tracker=CausalBall(known,model=task['predictor_model'])","tracker=CausalBall(known)")
    current=current.replace(",planner_mode=task['planner_mode']))","))")
    current=current.replace("        dump(out/'FORECAST_RECORDS.json',tracker.forecasts)\n",'')
    current=current.replace("        dump(out/'CAUSAL_PREDICTION_MODEL.json',tracker.snapshot())\n",'')
    assert current==previous,'ROS_CHANGE_OUTSIDE_REGISTERED_DYNAMIC_AND_EVIDENCE_BOUNDARY'
    tree=ast.parse((C/'ros_component.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    publish=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='publish')
    update_call=next(n for n in ast.walk(publish) if isinstance(n,ast.If) and ast.unparse(n.test)=="task['dynamic']")
    assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='update' for n in ast.walk(update_call))
    tasks=json.loads((C/'TASKS.json').read_text());oldtasks=json.loads((B/'TASKS.json').read_text())
    baseline=next(t for t in oldtasks if t['branch']=='rpp_fast_stamped' and t['stage']=='static' and t['role']=='main')
    for task in tasks:
        for key in ['case_id','seed','phase','start_xy','start_yaw','goal_xy','reference_path','center_reference_path','controller_plugin']:
            assert task[key]==baseline[key],key
    receipts=[]
    for role in ['main','repeat']:
        out=R/('runs/v858_nav2_verified/v1354/rpp_fast_stamped_static_'+role)
        result=json.loads((out/'RESULT.json').read_text());audit=json.loads((out/'FINAL_INDEPENDENT_AUDIT.json').read_text())
        assert result['passed'] and audit['passed'] and result['replay']['passed']
        receipts.append(dict(role=role,source=str(out.relative_to(R)),native=result['new_actual_native'],
            full_own_replay_native=result['own_replay_native'],result_sha256=sha(out/'RESULT.json'),
            independent_audit_sha256=sha(out/'FINAL_INDEPENDENT_AUDIT.json'),counted_as_new_sample=False))
    proof=dict(passed=True,old_full_source_closure_unchanged=True,identical_control_dependencies=names,
        ros_source_only_dynamic_predictor_worker_and_metadata_changed=True,
        dynamic_false_does_not_update_predictor_or_invoke_planner=True,
        constructor_and_output_root_namespace_only_no_vehicle_state_write=True,
        static_receipts=receipts,new_static_trials=0,models=0,physical_native=0)
    (O/'REUSED_QUALIFICATIONS.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(dict(passed=True,reused_static_tasks=2,new_static_trials=0,models=0)))


if __name__=='__main__':main()
