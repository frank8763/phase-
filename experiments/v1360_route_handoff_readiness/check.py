"""Data-only handoff decision, no launch and no running-round mutations."""
import copy
import hashlib
import importlib.abc
import json
from pathlib import Path
import sys
import time

class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','factory','physical','rclpy'}:
            raise AssertionError('ZERO_MODEL_HANDOFF_ONLY '+name)
sys.meta_path.insert(0,NoModel())

R=Path(__file__).resolve().parents[2]
C=Path(__file__).resolve().parent
O=R/'runs'/C.name
SOURCE=R/'runs/v1359_reverse_restart_bridge'
TASKS=['reverse_restart_component_main','reverse_restart_component_repeat',
       'sweep_terminal_dynamic_main','sweep_terminal_dynamic_repeat']


def read(path):return json.loads(path.read_text())


def qualified(row):
    n=row.get('native') or {};a=row.get('audit') or {};p=n.get('physical') or {}
    if row.get('classification')!='PASSED' or not row.get('passed'):return False
    if not n.get('closed') or not n.get('passed') or n.get('error') or not n.get('source_unchanged'):return False
    count=n.get('new_actual_native')
    if type(count) is not int or count<=0 or count!=n.get('own_replay_native'):return False
    replay=n.get('replay') or {}
    if not replay.get('passed') or replay.get('maximum_qpos_qvel_ctrl_mocap_error',1.)>1e-8:return False
    if p.get('bad_contacts')!=0 or p.get('minimum_actual_clearance_m',0.)<.15-1e-8:return False
    if not a.get('passed') or not a.get('checks') or not all(a['checks'].values()):return False
    if row['stage']=='dynamic':
        s=row.get('ros') or {}
        if not s.get('closed') or not s.get('passed') or s.get('error') or s.get('evidence_write_errors'):return False
        if n.get('whole_goal_distance_m',1.)>.45:return False
    return True


def decision(summary,finalized):
    rows={row['task']:row for row in summary.get('results',[])}
    outcome={name:'UNEXECUTED' if name not in rows else 'PASSED' if qualified(rows[name]) else
             'PENDING' if rows[name].get('classification') is None else 'NOT_PASSED' for name in TASKS}
    passed=summary.get('closed') is True and summary.get('passed') is True and summary.get('source_unchanged') is True
    passed=passed and all(value=='PASSED' for value in outcome.values())
    archive=finalized.get('passed') is True and finalized.get('local_archive_all_member_and_reassembled_SHA_passed') is True
    return dict(exposed_WE_development_main_repeat_verified=bool(passed and archive),
        per_task=outcome,local_archive_verified=archive,
        state='WE_PAIR_VERIFIED' if passed and archive else 'CLOSED_NOT_READY' if summary.get('closed') else 'RUNNING_PENDING',
        new_physical_authorized=False,automatic_launch=False,new24_authorized=False)


def test_gate(component_rows):
    assert len(component_rows)==2 and all(qualified(row) for row in component_rows)
    rows=copy.deepcopy(component_rows)
    for name in TASKS[2:]:
        row=copy.deepcopy(component_rows[0]);row.update(task=name,stage='dynamic')
        row['native']['whole_goal_distance_m']=.4
        row['ros']=dict(passed=True,closed=True,evidence_write_errors=[])
        rows.append(row)
    fixture=dict(closed=True,passed=True,source_unchanged=True,results=rows)
    archive=dict(passed=True,local_archive_all_member_and_reassembled_SHA_passed=True)
    assert decision(fixture,archive)['exposed_WE_development_main_repeat_verified']
    negatives=0
    for label in ['audit_missing','goal_failed','replay_mismatch','unknown_native','repeat_unexecuted','archive_only']:
        changed=copy.deepcopy(fixture)
        row=changed['results'][-1]
        if label=='audit_missing':row['audit']={}
        if label=='goal_failed':row['native']['whole_goal_distance_m']=.451
        if label=='replay_mismatch':row['native']['replay']['maximum_qpos_qvel_ctrl_mocap_error']=1e-5
        if label=='unknown_native':row['native']['new_actual_native']=None
        if label=='repeat_unexecuted':changed['results'].pop()
        if label=='archive_only':changed['passed']=False
        assert not decision(changed,archive)['exposed_WE_development_main_repeat_verified'],label
        negatives+=1
    return dict(passed=True,synthetic_positive_not_counted_as_trial=True,negative_cases=negatives,
                real_component_receipts_rechecked=2,models=0,physical_native=0)


def main():
    start=time.monotonic();O.mkdir(exist_ok=True)
    summary=read(SOURCE/'COMPLETION.json') if (SOURCE/'COMPLETION.json').exists() else dict(closed=False,results=read(SOURCE/'PARTIAL_RESULTS.json'))
    finalized=read(SOURCE/'FINALIZED.json') if (SOURCE/'FINALIZED.json').exists() else {}
    result=decision(summary,finalized)
    result.update(checked_unix=time.time(),models=0,physical_native=0,
        task_success_scope='one exposed original WE development pair only',
        original_model_deadline_unix=1795078800.0,
        seconds_to_original_deadline=1795078800.0-time.time())
    validation=test_gate([row for row in summary['results'] if row['stage']=='component'])
    (O/'GATE_QUALIFICATION.json').write_text(json.dumps(validation,indent=2)+'\n')
    frozen=read(R/'experiments/v1359_reverse_restart_bridge/SOURCE_FREEZE.json')['files']
    hashes={}
    for name in ['experiments/v1359_reverse_restart_bridge/gear_handoff.py',
                 'experiments/v1359_reverse_restart_bridge/native_component.py',
                 'experiments/v1359_reverse_restart_bridge/causal_occupancy.py',
                 'runs/v1358_terminal_contract/libsearch.so']:
        actual=hashlib.sha256((R/name).read_bytes()).hexdigest();assert actual==frozen[name]
        hashes[name]=actual
    result.update(selected_frozen_sources_unchanged=True,selected_source_hashes=hashes,wall_s=time.monotonic()-start)
    assert result['wall_s']<15
    index=1+len(list(O.glob('READINESS_*.json')))
    (O/('READINESS_%03d.json'%index)).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
