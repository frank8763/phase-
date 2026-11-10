"""Predeclared route branches; no runtime tuning or failure replacement."""
def skip_repeat(task,rows):
    return task['slot']<6 and task['slot']%2==1 and not rows[-1]['passed']
def can_confirm(rows):
    return len(rows)>=6 and all(x['passed']and x.get('executed',True)for x in rows[:6])
def failure_action(task,row,rows):
    if row['passed']:return 'CONTINUE'
    if row.get('evidence_passed')is not True:return 'STOP_ALL_SAFETY_OR_EVIDENCE'
    if task['slot']<6:return 'CONTINUE_INDEPENDENT_ROUTE'
    if task['stage']!='confirmation':return 'STOP_FIXED_REPEAT_FAILED'
    return 'STOP_SECOND_CONFIRMATION_FUNCTION'if sum(not x['passed']for x in rows if x['stage']=='confirmation')>=2 else'CONTINUE'
