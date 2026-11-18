"""Fail-closed sequencing for four registered tasks; no launch capability."""


def decision(tasks,finished,repeats,remaining,*,source_ok=True,active=False):
    if not source_ok:return dict(action='STOP',reason='SOURCE_CHANGED')
    if active:return dict(action='WAIT',reason='ONE_WORKER_ACTIVE')
    if len(finished)>len(tasks):return dict(action='STOP',reason='EXTRA_RESULT')
    for index,item in enumerate(finished):
        task=tasks[index]
        if item.get('task_id')!=task['task_id']:return dict(action='STOP',reason='TASK_ORDER')
        r=item.get('result')
        if not r or not r.get('passed') or r.get('error')is not None:return dict(action='STOP',reason='FIRST_WORKER_FAILURE')
        if r.get('own_replay_native')!=r.get('new_actual_native') or not (r.get('replay')or{}).get('passed'):
            return dict(action='STOP',reason='INCOMPLETE_ACTUAL_REPLAY')
        audit=item.get('audit')
        if audit is None:return dict(action='WAIT',reason='INDEPENDENT_AUDIT_REQUIRED')
        if not audit.get('passed') or not audit.get('physical_audit_complete') or not audit.get('actual_replay_verified'):
            return dict(action='STOP',reason='INDEPENDENT_AUDIT_FAILED')
        if task['role']=='repeat':
            comparison=repeats.get(str(task['slot']))
            if comparison is None:return dict(action='WAIT',reason='FULL_REPEAT_COMPARISON_REQUIRED')
            if not comparison.get('passed'):return dict(action='STOP',reason='FULL_REPEAT_MISMATCH')
    if len(finished)==len(tasks):return dict(action='COMPLETE',reason='TWO_EXPOSED_SLOTS_MAIN_REPEAT_AUDITED')
    if remaining<=1700:return dict(action='STOP',reason='INSUFFICIENT_ROOT_TIME_NO_EXTENSION')
    return dict(action='RUN',task_id=tasks[len(finished)]['task_id'])
