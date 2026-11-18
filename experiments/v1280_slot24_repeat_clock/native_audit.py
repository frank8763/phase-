from campaign_context import *
def audit(task):
    assert task['slot']==24 and task['case_id']=='EAST_WEST'
    result=load('phase_v1278_complete_ew_auditor',C/'ew_audit.py').audit(task)
    out=Path(task['output']);events=read(out/'PARTIAL_STATIC_RENEWALS.json');assert events
    owner=load('phase_v1278_independent_transition',C/'transition_audit.py')
    proof=owner.verify(task,events)
    result['partial_static_reconnections']=proof;dump(out/'FINAL_INDEPENDENT_AUDIT.json',result)
    return result
