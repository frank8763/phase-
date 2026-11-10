"""One task clock and bounded pre-ARM restore; no process/model construction."""
import hashlib,json,time
from pathlib import Path

RESTORE_S=180.
ROS_S=35.
DRIVE_S=40.
BRAKE_S=2.
SAVE_REPLAY_S=40.
CLOSURE_S=40.
MARGIN_S=13.
TASK_S=350.
CAMPAIGN_WAIT_S=360.
ROOT_RESERVE_S=375.
assert RESTORE_S+ROS_S+DRIVE_S+BRAKE_S+SAVE_REPLAY_S+CLOSURE_S+MARGIN_S==TASK_S
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def create(task,root_deadline,wall=None,monotonic=None):
    wall=time.time()if wall is None else wall;monotonic=time.monotonic()if monotonic is None else monotonic
    assert root_deadline-wall>=ROOT_RESERVE_S,'INSUFFICIENT_FIXED_TASK_RESERVE'
    assert task['wall_limit_s']==DRIVE_S and task['brake_s']==BRAKE_S
    return dict(run_id=task['run_id'],task_sha256=digest(task),root_deadline_unix=root_deadline,
        started_unix=wall,started_monotonic=monotonic,hard_deadline_unix=wall+TASK_S,hard_stop_monotonic=monotonic+TASK_S,
        restore_deadline_unix=wall+RESTORE_S,restore_stop_monotonic=monotonic+RESTORE_S,
        task_hard_s=TASK_S,restore_cap_s=RESTORE_S,drive_s=DRIVE_S,brake_s=BRAKE_S)
def validate(record,task,root_deadline):
    expected=create(task,root_deadline,record['started_unix'],record['started_monotonic'])
    assert record==expected,'TASK_CLOCK_OR_BUDGET_CHANGED'
    return record
def load(out,task,root_deadline):
    return validate(json.loads((Path(out)/'TASK_CLOCK.json').read_text()),task,root_deadline)
def model_deadline(record):return min(record['root_deadline_unix']-10.,record['hard_deadline_unix'])
def alarm_seconds(record,wall=None,monotonic=None):
    wall=time.time()if wall is None else wall;monotonic=time.monotonic()if monotonic is None else monotonic
    return max(.001,min(model_deadline(record)-wall,record['hard_stop_monotonic']-monotonic)-5.)
def check_restore(record,out,run_id,clock=time):
    assert clock.monotonic()<record['restore_stop_monotonic']and clock.time()<record['restore_deadline_unix'],'CANONICAL_STATE_RESTORE_TIMEOUT'
    path=Path(out)/'PARENT_STOP_REQUEST.json'
    if path.exists():
        message=json.loads(path.read_text());assert message['run_id']==run_id,'FOREIGN_PARENT_STOP_REQUEST'
        raise InterruptedError('PARENT_STOP_DURING_CANONICAL_RESTORE')
def wait_ready(job,out,record,task,clock=time):
    path=Path(out)/'NATIVE_READY.json'
    while not path.exists():
        assert job.poll()is None,'NATIVE_FAILED_BEFORE_CANONICAL_READY'
        check_restore(record,out,task['run_id'],clock);clock.sleep(.05)
    check_restore(record,out,task['run_id'],clock)
    assert job.poll()is None,'NATIVE_FAILED_BEFORE_CANONICAL_READY'
    ready=json.loads(path.read_text())
    assert ready['origin_validated']is True and ready['native_tick']==task['origin_native_tick'],'WRONG_CANONICAL_READY_ORIGIN'
    assert abs(ready['sim_time']-task['origin_sim_time'])<=1e-9,'WRONG_CANONICAL_READY_CLOCK'
    return ready
