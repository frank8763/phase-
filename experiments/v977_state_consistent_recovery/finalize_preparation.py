"""Audit and freeze the bounded source-only preparation; never grant models."""
import ast
import fcntl
import hashlib
import importlib.util
import json
import time
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
O=R/'runs/v977_state_consistent_recovery';REC=R/'records/nav2_v977_20261110'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def dump(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    auth=json.loads((REC/'AUTHORIZATION.json').read_text());assert auth['models_authorized'] is False
    assert not (C/'SOURCE_FREEZE.json').exists(),'PREPARATION_ALREADY_FROZEN'
    spec=importlib.util.spec_from_file_location('independent_saved_tracking',C/'independent_tracking.py')
    tracking=importlib.util.module_from_spec(spec);spec.loader.exec_module(tracking)
    with np.load(R/'runs/v976_saved_recovery_diagnosis/FIRST_SEGMENT_SAVED.npz')as data:
        original=tracking.check(data['reference'],data['body'][:,:3],.0005)
    assert original['passed'] is False,'ORIGINAL_TRACKING_FAILURE_NOT_REPRODUCED'
    checks={'original_actual_tracking_failure_red':True}
    qualifications={}
    for name in ['ZERO_MODEL_QUALIFICATION.json','CONTRACT_QUALIFICATION.json','SUPERVISOR_QUALIFICATION.json','NATIVE_AUTHORITY_QUALIFICATION.json','INDEPENDENT_AUDITOR_QUALIFICATION.json']:
        value=json.loads((O/name).read_text());assert value['passed'] and value['models']==value['integrations']==0
        qualifications[name]=value
        (REC/name).write_bytes((O/name).read_bytes());checks[name]=True
    source_result=json.loads((O/'SOFTWARE_RESULTS_attempt6.json').read_text());assert source_result['passed'] and source_result['completed']==2
    software=[]
    for index in [0,1]:
        path=O/f'SOFTWARE_CASE{index}_attempt6.json';value=json.loads(path.read_text())
        assert value['passed'] and value['shutdown']['passed'] and not value['shutdown']['callback_errors']
        assert 'The following exception was never retrieved' not in (O/f'software_case{index}_attempt6.console').read_text()
        with np.load(O/f'case{index}_attempt6/PEER_TRACE.npz')as data:
            audit=tracking.check(data['reference'],data['body'],.0125)
            assert audit['passed']
            assert abs(audit['maximum_heading_error_rad']-value['maximum_heading_error_rad'])<1e-12
            assert abs(audit['maximum_position_error_m']-value['maximum_position_error_m'])<1e-12
            assert np.all(np.diff(data['native_tick'])>=0),'NONMONOTONIC_PEER_TRACE'
        software.append(dict(index=index,report=value,independent_tracking=audit))
        (REC/f'SOFTWARE_CASE{index}.json').write_bytes(path.read_bytes())
    checks['real_installed_RPP_and_new_production_bridge_two_cases']=True
    checks['independent_saved_peer_tracking_and_shutdown']=True
    (REC/'BASELINE_RED.json').write_bytes((O/'BASELINE_RED.json').read_bytes())
    aliases=[]
    for path in C.iterdir():
        if path.suffix=='.py':ast.parse(path.read_text(),filename=str(path))
        if path.is_symlink():
            target=path.resolve();assert target.is_relative_to(R/'experiments')
            aliases.append(dict(alias=str(path.relative_to(R)),source=str(target.relative_to(R)),sha256=sha(path)))
    dump(C/'MODULE_BINDINGS.json',dict(aliases=aliases,models=0,integrations=0))
    # This inherited closure excludes evicted run caches; selected runtime binary
    # and pinned ROS executor source are explicitly included below.
    files={}
    for rel,digest in json.loads((R/'experiments/v974_daytime_binding_gate/SOURCE_FREEZE.json').read_text())['files'].items():
        if rel.startswith(('runs/','records/')):continue
        assert sha(R/rel)==digest,'OLD_FROZEN_SOURCE_CHANGED '+rel
        files[rel]=digest
    for path in C.iterdir():
        if path.is_file() and path.name!='SOURCE_FREEZE.json':files[str(path.relative_to(R))]=sha(path)
    for name in ['runs/v884_feasible_rpp/install/lib/libphase_feasible_rpp.so',
                 'runs/v856_nav2_foundation/rootfs/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/executors.py']:
        files[name]=sha(R/name)
    final=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,private_dynamics_predictions=0,
               training=0,hardware=0,new_navigation_trials=0,original_actual_failure=original,
               same_fixed_two_causal_states=True,qualified_analytical_references=2,real_RPP_software_peer_cases=2,
               physical_tracking_qualified=False,physical_ready=False,model_authority=False,
               scope='Source and zero-model qualification only; no new physical success or full dynamic acceptance',
               software=software,guard_restored=True,execution_lock_idle_before_finalization=True)
    dump(REC/'FINAL_ZERO_MODEL_AUDIT.json',final)
    dump(C/'SOURCE_FREEZE.json',dict(final=True,source_only=True,models_at_freeze=0,integrations_before_freeze=0,
                                  model_authority=False,frozen_unix=time.time(),files=files))
    dump(REC/'SOURCE_FREEZE_POINTER.json',dict(path=str((C/'SOURCE_FREEZE.json').relative_to(R)),sha256=sha(C/'SOURCE_FREEZE.json'),source_files=len(files),models=0))
    dump(REC/'COMPLETION.json',dict(closed=True,status='SOURCE_AND_ZERO_MODEL_QUALIFIED_ONLY',
         user_selected_source_only=True,physical_ready=False,models_authorized=False,new_models=0,actual_native=0,
         private_native=0,replay_native=0,training=0,hardware=0,automatic_next_stage=False))
    print(json.dumps(dict(passed=final['passed'],source_files=len(files),qualified_saved_states=2,
                          real_RPP_software_cases=2,models=0,integrations=0,physical_ready=False)),flush=True)


if __name__=='__main__':main()
