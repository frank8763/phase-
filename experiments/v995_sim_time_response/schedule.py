"""Deterministic diagnostic stimulus; no actor/reference truth or model API."""
def controls(index,task,initial_curvature):
    assert 0<=index<800 and task['maximum_new_native']==800
    if index>=600:return 0.,0.,True
    elapsed=index*.01;selected=task['schedule'][0][1]
    for start,value in task['schedule']:
        if elapsed>=start:selected=value
    curvature=initial_curvature if selected=='original'else float(selected)
    return task['speed_m_s'],task['speed_m_s']*curvature,False
