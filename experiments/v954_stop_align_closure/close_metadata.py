"""Close only V953 operation authority after verified recorded failure; zero models."""
import fcntl
import hashlib
import json
from datetime import datetime,timedelta,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];OPS=ROOT/'runs/v953_stop_align_components'
OUT=ROOT/'runs/v954_stop_align_closure';REC=ROOT/'records/nav2_v952_v953_20261109'


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def main():
    lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    guard=hashlib.sha256((ROOT/'REVIEW_PENDING').read_bytes()).hexdigest()
    assert guard=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    done=json.loads((OPS/'COMPLETION.json').read_text());assert done['closed']and not done['passed']
    audit=json.loads((OUT/'FINAL_INDEPENDENT_AUDIT.json').read_text())
    assert audit['evidence_integrity_verified'] and not audit['passed']
    original=OPS/'AUTHORIZATION.before_close.json'
    if not original.exists():original.write_bytes((OPS/'AUTHORIZATION.json').read_bytes())
    auth=json.loads(original.read_text())
    assert done['deadline_unix']==auth['deadline_unix'] and done['started_unix']==auth['started_unix']
    auth.update(models_authorized=False,closed=True,closed_unix=done['closed_unix'],
        stop_reason='FIRST_RESPONSE_FAILURE_INDEX1_MEASURED_STEERING_NOT_NEUTRAL')
    dump(OPS/'AUTHORIZATION.json',auth)
    report='docs/RPCCR_STOP_ALIGN_V952_V953_REPORT.md'
    current=json.loads((ROOT/'CURRENT_EXPERIMENT.json').read_text())
    current.update(status='REVIEW_PENDING',current_experiment='v953_stop_align_components',
        active_entrypoint=None,active_run=None,active_window=None,execution_window_closed=True,
        source_revision='V952_STOP_THEN_ALIGNMENT_COMPONENT_NOT_PASSED',
        decision_freeze='experiments/v953_stop_align_components/SOURCE_FREEZE.json',
        protocol='experiments/v953_stop_align_components/PROTOCOL.md',report=report,
        next_physical_authorized=False,requires_user_review_before_next_experiment=True,
        last_observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat())
    current['v953_component'].update(closed=True,status='NOT_PASSED',models=2,actual_native=840,replay_native=840,
        private_native=0,navigation=0,new24=0,passed_response_cases=1,failed_response_cases=1,
        unexecuted_response_cases=16,unexecuted_handoff_cases=1,report=report,
        stop_reason=auth['stop_reason'],models_authorized=False)
    dump(ROOT/'CURRENT_EXPERIMENT.json',current)
    REC.mkdir(exist_ok=True)
    for folder,names in [(OPS,['USER_WINDOW_APPROVAL.json','AUTHORIZATION.before_close.json','AUTHORIZATION.json',
            'COMPLETION.json','ZERO_MODEL_QUALIFICATION.json']),
        (OUT,['FINAL_INDEPENDENT_AUDIT.json','FAILURE_DIAGNOSIS.json']),
        (ROOT/'runs/v952_stopped_steering_alignment',['RESTORE_RECEIPT.json','PREPARATION_ERRORS.json','ZERO_MODEL_QUALIFICATION.json'])]:
        for name in names:
            target=REC/((folder.name+'_')+name)
            target.write_bytes((folder/name).read_bytes())
    result=dict(closed=True,scientific_outcome='NOT_PASSED',new_models_during_close=0,new_integrations=0,
        actual_native=840,replay_native=840,private_native=0,navigation=0,new24=0,
        execution_lock_idle=True,review_pending_sha256=guard,original_deadline_unix=auth['deadline_unix'],
        frozen_scientific_sources_unchanged=audit['all_sources_unchanged'],
        component_qualification_passed=False,evidence_integrity_verified=True)
    dump(REC/'LOCAL_CLOSURE.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
