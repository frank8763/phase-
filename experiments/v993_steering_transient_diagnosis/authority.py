"""One new user-owned absolute20:00 root; four preregistered diagnostic tasks."""
import hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
O=R/'runs/v993_steering_transient_diagnosis';ROOT=R/'runs/daytime_20261110_until20'
END=1794312000.
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def authorized(task=None):
    a=read(ROOT/'USER_AUTHORIZATION.json')
    assert a['absolute_model_deadline_unix']==END and time.time()<END-320,'ABSOLUTE_DAYTIME_END_OR_INSUFFICIENT_TIME'
    assert not(O/'COMPLETION.json').exists(),'DIAGNOSTIC_ALREADY_CLOSED'
    assert read(O/'QUALIFICATION.json')['passed']and read(C/'SOURCE_FREEZE.json')['final']
    for n,h in read(C/'SOURCE_FREEZE.json')['files'].items():assert sha(R/n)==h,'FROZEN_SOURCE_CHANGED '+n
    receipt=read(O/'RESTORE_RECEIPT.json');required=read(C/'RESTORE_REQUIREMENTS.json')
    assert receipt['passed']and receipt['files']==required['files']
    for row in receipt['files']:assert sha(R/row['path'])==row['sha256'],'SAVED_INPUT_CHANGED'
    tasks=read(C/'TASKS.json')
    if task is not None:
        assert task in tasks and task['slot']in [0,1,2,3],'UNREGISTERED_PROBE'
        prior=read(O/'RESULTS.json')if(O/'RESULTS.json').exists()else[]
        assert len(prior)==task['slot']and all(x['passed']for x in prior),'PRIOR_DIAGNOSTIC_EVIDENCE_FAILURE'
    return END
