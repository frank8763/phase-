"""Data-only exact dependency reuse and decision-audit adversarial checks."""
import copy
import hashlib
import json
from pathlib import Path
from dynamic_audit import review
from dynamic_reserve import check

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
OLD=R/'experiments/v1359_reverse_restart_bridge'


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')


def main():
    original=read(OLD/'SOURCE_FREEZE.json')
    assert all(sha(R/p)==h for p,h in original['files'].items()),'PARENT_DEPENDENCY_CHANGED'
    unchanged=['native_component.py','gear_handoff.py','recovery_guard.py','stamped_contract.py','evidence_io.py',
               'worker_monitor.py','planning_job.py','observed_route.py','segments.py','transport.py',
               'backend_check.py','causal_occupancy.py','route_worker.py','evaluate_coverage.py','rpp_params.json']
    assert all(sha(C/p)==sha(OLD/p) for p in unchanged)
    software_names=['common.py','probe.py','run_software.py','rpp_params.json','stamped_contract.py','SOFTWARE_TASKS.json','INPUT_00.json']
    snapshot=read(O/'SOFTWARE_SOURCE_FREEZE.json')['files']
    assert all(sha(C/p)==snapshot[str((C/p).relative_to(R))] for p in software_names)
    assert read(O/'software/COMPLETION.json')['passed'] and read(O/'software/INDEPENDENT_AUDIT.json')['passed']
    oldtasks=[t for t in read(OLD/'TASKS.json') if t['stage']=='dynamic'];newtasks=read(C/'TASKS.json')
    assert len(oldtasks)==len(newtasks)==2
    task_fields={'run_id','output','run_root','nav2_params','scope','dynamic_reserve_contract'}
    assert all({k:v for k,v in a.items() if k not in task_fields}=={k:v for k,v in b.items() if k not in task_fields} for a,b in zip(oldtasks,newtasks))
    parent=read(R/'runs/v1359_reverse_restart_bridge/COMPLETION.json')
    components=[x for x in parent['results'] if x['stage']=='component']
    assert len(components)==2 and all(x['passed'] and x['audit']['passed'] and x['native']['replay']['passed'] for x in components)
    static=[x for x in read(R/'runs/v1357_expiry_evidence_relay/COMPLETION.json')['results'] if x['stage']=='static']
    assert len(static)==2 and all(x['passed'] and x['audit']['passed'] for x in static)
    receipts=['runs/v1358_terminal_contract/INDEPENDENT_PREDICTION_COVERAGE.json',
              'runs/v1358_terminal_contract/ACTUAL_WORKER_QUALIFICATION.json',
              'runs/v1358_terminal_contract/BOUNDARY_QUALIFICATION.json',
              'runs/v1357_expiry_evidence_relay/COOPERATIVE_PRODUCTION_ROS_QUALIFICATION.json',
              'runs/v1357_expiry_evidence_relay/EXPIRY_AND_CLOSE_QUALIFICATION.json']
    assert all(read(R/p)['passed'] for p in receipts)
    dump(O/'REUSED_QUALIFICATIONS.json',dict(passed=True,original_frozen_dependency_closure_unchanged=True,
         original_dependency_files=len(original['files']),identical_scientific_and_execution_dependencies=unchanged,
         software_actual_dependencies_unchanged=software_names,original_task_fields_unchanged_except_declared_scope_and_paths=True,
         static_and_restart_pairs_reused=True,new_static_or_component_trials=0,
         receipts=[dict(path=p,sha256=sha(R/p),reused_only=True,new_trial_count=0) for p in receipts],models=0,physical_native=0))
    # Construct an audit fixture from actual saved pose/ball/RPP output, without
    # representing its stationary playback as a new integrated trajectory.
    saved=read(C/'INPUT_00.json');raw=R/'runs/v858_nav2_verified/v1359/sweep_terminal_dynamic_main'
    forecast=next(x for x in read(raw/'FORECAST_RECORDS.json') if x['native_tick']==saved['native_tick'])
    command=next(x for x in read(O/'software/saved_request10_reverse_escape/RAW_COMMANDS.json') if abs(x['v'])>.005)
    allowed,proof=check(saved['original_body'],saved['causal_ball'],command['v'],command['w'])
    event=dict(command_sequence=0,body=saved['original_body'],ball=saved['causal_ball'],requested=[command['v'],command['w']],
               allowed=allowed,proof=proof,native_tick=saved['native_tick'],sim_time=saved['original_sim_time'])
    sent=dict(sequence=0,v=command['v'],w=command['w'],source='CONTROLLER',observation_native_tick=saved['native_tick'])
    sensor=saved['source_sensor'];assert review([event],[sent],[forecast],[sensor])['passed']
    cases=[]
    for name in ['decision_flip','ball_source_tamper','sensor_pose_tamper','missing_decision','refused_command_still_nonzero','proof_margin_tamper']:
        e,s,f,p=copy.deepcopy(([event],[sent],[forecast],[sensor]))
        if name=='decision_flip':e[0]['allowed']=False
        elif name=='ball_source_tamper':f[0]['center'][0]+=.01
        elif name=='sensor_pose_tamper':p[0]['xy'][0]+=.01
        elif name=='missing_decision':e=[]
        elif name=='proof_margin_tamper':e[0]['proof']['unchanged_recovery_margin_m']=.21
        else:
            e[0]['requested']=[.08,0.];e[0]['allowed'],e[0]['proof']=check(e[0]['body'],e[0]['ball'],.08,0.)
        try:review(e,s,f,p)
        except (AssertionError,KeyError):cases.append(name)
        else:raise AssertionError('AUDIT_TAMPER_ACCEPTED '+name)
    dump(O/'DYNAMIC_AUDIT_QUALIFICATION.json',dict(passed=True,positive_saved_data_fixture=True,negative_cases=cases,
         fixture_not_physical_trial=True,models=0,physical_native=0))
    print(json.dumps(dict(passed=True,reused_files=len(original['files']),identical_new_dependencies=len(unchanged),audit_negatives=len(cases),models=0)))


if __name__=='__main__':main()
