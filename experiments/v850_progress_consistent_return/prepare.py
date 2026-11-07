"""Finalize the one candidate only after all zero-model qualifications pass."""
import ast,hashlib,json,time
from pathlib import Path
from common import *


def main():
    assert not(C/'CANDIDATE_FREEZE.json').exists()and not(ROOT/'PREPARED.json').exists()
    assert read(ROOT/'AUTHORIZATION.json')['window_s']==5400
    legacy=read(ROOT/'LEGACY_AUDITOR_QUALIFICATION.json');progress=read(ROOT/'progress_auditor_qualification/RESULT.json');operations=read(ROOT/'OPERATIONS_CHECK.json');saved=read(ROOT/'saved_qualification/RESULT.json')
    assert legacy['passed']and progress['passed']and operations['passed']and saved['status']=='SAVED_PROGRESS_POLICY_QUALIFICATION_PASS'
    assert len(legacy['actual_saved18_auditors'])==18 and len(saved['saved_returns'])==14 and len(saved['negative_cases'])==9
    assert (W/'progress_record_independent.py').read_bytes()==(C/'audit_progress_record.py').read_bytes()
    for row in legacy['actual_saved18_auditors']:assert row['sha256']==sha(W/row['script'])
    for p in [*C.glob('*.py'),*W.glob('*.py')]:ast.parse(p.read_text(),filename=str(p))
    original=read(ROOT/'ORIGINAL_SOURCE_SHA256.json');assert all(sha(R/p)==h for p,h in original.items())
    with(R/'runs/v648_static_unknown/execution.lock').open('rb')as stream:
        import fcntl
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert(R/'REVIEW_PENDING').exists()and read(R/'CURRENT_EXPERIMENT.json')['status']=='REVIEW_PENDING'
    # The prior freeze supplies all historical imported implementation inputs;
    # the new worker/ops, fixed saved physical task and new authority are added.
    files=read(R/'experiments/v848_goal_first_certified/CANDIDATE_FREEZE.json')['files'].copy()
    assert all(sha(R/p)==h for p,h in files.items()),'HISTORICAL_FROZEN_INPUT_CHANGED'
    for directory in [C,W]:
        for p in directory.iterdir():
            if p.is_file()and p.suffix in ['.py','.md','.json']:files[str(p.relative_to(R))]=sha(p)
    for directory in [ROOT/'saved_qualification',ROOT/'progress_auditor_qualification']:
        for p in directory.iterdir():
            if p.is_file()and p.suffix=='.json':files[str(p.relative_to(R))]=sha(p)
    pair=R/'runs/v848_goal_first_worker/v848_main_slot01/paired';cell=pair/'geometry_memory'
    inputs=[pair/'scene_model.mjb',pair/'STATIC_PROTOCOL.json',pair/'DYNAMIC_PROTOCOL.json',pair/'INITIALIZATION_PROVENANCE.json',pair/'assets/isolated_indoor.xml',cell/'sensor_packets.jsonl.gz',cell/'dynamic_native.jsonl.gz',cell/'route_revalidation.jsonl',cell/'ACTUATOR_COMMAND_CONTRACT.json',cell/'handover_certificates/handover_0573.json.gz',cell/'recovery_contracts/contract_0569.json.gz',ROOT/'AUTHORIZATION.json',ROOT/'LEGACY_AUDITOR_QUALIFICATION.json',ROOT/'OPERATIONS_CHECK.json',R/'docs/RPCCR_REAL_ROBOT_AND_CONTRIBUTION_20261107.md']
    for p in inputs:files[str(p.relative_to(R))]=sha(p)
    freeze=dict(files=files,frozen_unix=time.time(),scientific_revisions=1,worker=str(W.relative_to(R)),model_window_s=5400,deadline_locked_at_first_launch=True,declared_change='Complete certified progress and retained terminal dominance, explicit finite recovery entry; original safety gates/control pool/model retained',new24=0,training=0)
    dump(C/'CANDIDATE_FREEZE.json',freeze)
    qualification=dict(passed=True,expected_audit_statuses=legacy['expected_audit_statuses'],actual_saved_original_auditors=18,new_progress_auditor_entry_cases=progress['cases'],saved14_return_and9negative_checks=True,actual_component_to_first_MJB_boundary=True,actual_engine_to_first_t0_Popen_boundary=True,models=0,integrations=0,metadata_proxy_is_import_only=True)
    dump(ROOT/'QUALIFICATION.json',qualification);dump(ROOT/'PREPARED.json',dict(passed=True,freeze_sha256=sha(C/'CANDIDATE_FREEZE.json'),inputs=len(files),models=0,integrations=0))
    unchanged()
    dump(ROOT/'STATUS.json',dict(status='FROZEN_PREPARED_FOR_ONE_90MIN_LAUNCH',model_window_s=5400,models_started=0,new_integrations=0,freeze=str((C/'CANDIDATE_FREEZE.json').relative_to(R)),no_duplicate_start=True))
    print(json.dumps(read(ROOT/'PREPARED.json')),flush=True)


if __name__=='__main__':main()
