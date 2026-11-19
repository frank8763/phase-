"""Actual new worker, all-period evaluator and unchanged static closure."""
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import numpy as np
from component_context import *
from planning_job import PlanningJob


def module(name,path):
    s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    saved=read(O/'SAVED_TAIL_QUALIFICATION.json');early=read(O/'EARLY_SWEEP_QUALIFICATION.json')
    selected=[p for p in saved['rows'] if p['kind']=='HORIZON' and p['request_id']==10]
    selected.append(dict(request=early['request'],path=early['path'],report=early['report'],geometry=early['geometry'],kind='NESTED_SWEEP',branch='early',geometry_passed=early['passed']))
    assert len(selected)==3 and all(p['geometry_passed'] for p in selected)
    worker_rows=[]
    for index,row in enumerate(selected):
        request=dict(row['request'],planner_mode=1);job=PlanningJob(O/('worker_%02d'%index),worker=C/'route_worker.py',timeout_s=5.)
        job.start(request);begin=time.monotonic()
        try:
            while True:
                value=job.poll()
                if value is not None:break
                time.sleep(.005)
        finally:job.cancel()
        assert value['passed'] and not value.get('error') and value['path']==row['path']
        assert value['report']['status']!='GLOBAL_GOAL_PATH' or value['report']['body_goal_distance_m']<=.32+1e-8
        worker_rows.append(dict(passed=True,case=index,kind=row['kind'],same_path=True,wall_s=time.monotonic()-begin,report=value['report']))
    dump(O/'ACTUAL_WORKER_QUALIFICATION.json',dict(passed=True,cases=worker_rows,models=0,physical_native=0))
    # Ground truth is loaded only by this separate evaluator after policy
    # forecasts were saved. It never enters the online predictor or search.
    evaluate=module('separate_saved_forecast_evaluator','experiments/v1358_terminal_contract/evaluate_coverage.py').evaluate
    rows=read(O/'SAVED_FORECASTS.json');coverage=[]
    for branch in ['periodic_mode0','periodic_mode1']:
        raw=R/'runs/v858_nav2_verified/v1357'/(branch+'_dynamic_main')
        for kind in ['HORIZON','NESTED_SWEEP']:
            chosen=[dict(row,invariant_for_all_future_under_declared_class=kind=='NESTED_SWEEP') for row in rows if row['branch']==branch and row['kind']==kind]
            coverage.append(dict(branch=branch,kind=kind,proof=evaluate(raw,chosen)))
    dump(O/'INDEPENDENT_PREDICTION_COVERAGE.json',dict(passed=True,cases=coverage,
        future_samples=sum(row['proof']['future_samples'] for row in coverage),models=0,physical_native=0))
    # The changed guard only runs after dynamic discovery. Preserve exact static
    # behavior, native/command boundaries, installed params and reference inputs.
    B=R/'experiments/v1357_expiry_evidence_relay';old=read(B/'SOURCE_FREEZE.json')['files']
    assert all(sha(R/p)==h for p,h in old.items()),'PREVIOUS_CLOSURE_CHANGED'
    equal=['native_component.py','stamped_contract.py','evidence_io.py','worker_monitor.py','rpp_params.json','gear_handoff.py','segments.py','transport.py','planning_job.py']
    assert all((C/n).read_bytes()==(B/n).read_bytes() for n in equal)
    ros=(C/'ros_component.py').read_text().replace(",forecast_kind=task['forecast_kind']",'')
    assert ros==(B/'ros_component.py').read_text(),'ROS_CHANGE_OUTSIDE_DYNAMIC_PREDICTOR_CONSTRUCTOR'
    oldtasks=read(B/'TASKS.json');newtasks=read(C/'TASKS.json')
    static=next(t for t in oldtasks if t['stage']=='static' and t['role']=='main')
    for task in newtasks:
        for k in ['case_id','seed','phase','start_xy','start_yaw','goal_xy','controller_plugin','reference_path','center_reference_path']:
            assert task[k]==static[k]
    receipts=[]
    for role in ['main','repeat']:
        out=R/('runs/v858_nav2_verified/v1357/entry_static_static_'+role)
        result=read(out/'RESULT.json');audit=read(out/'FINAL_INDEPENDENT_AUDIT.json')
        assert result['passed'] and audit['passed']
        receipts.append(dict(role=role,source=str(out.relative_to(R)),result_sha256=sha(out/'RESULT.json'),
            audit_sha256=sha(out/'FINAL_INDEPENDENT_AUDIT.json'),counted_as_new_sample=False))
    dump(O/'REUSED_QUALIFICATIONS.json',dict(passed=True,old_full_dependency_closure_unchanged=True,exact_unchanged_dependencies=equal,
        dynamic_only_predictor_guard_and_search_changes=True,static_pair=receipts,new_static_trials=0,models=0))
    dump(O/'CHANGED_BOUNDARY_QUALIFICATION.json',dict(passed=True,actual_worker_cases=3,
        all_body_goal_labels_independently_checked=True,nested_prior_saved_future_coverage=True,
        original_geometric_monitor_floor_unchanged=.22,original_native_floor_unchanged=.15,models=0,physical_native=0))
    print(json.dumps(dict(passed=True,actual_workers=3,future_samples=sum(row['proof']['future_samples'] for row in coverage),static_reused=2,models=0)))


if __name__=='__main__':main()
