"""Public full-route planner API. Source qualification, NEVER vehicle authority.

A complete goal path and its exact body-input schedule are returned together.
An empty result means STOP/hold, never permission to execute a shorter prefix.
Actual integration must retain the native physical guards, discovery handling,
source revalidation and independent complete-state replay; it is not ready here.
"""
import copy,time
import numpy as np
from input_route import construct as search
from certificate import audit
from whole_input import public_setup

def construct(packet,source,goal,known,setup,last_ctrl,integral,deadline):
    assert setup['known']==known,'CAUSAL_KNOWN_MAP_MISMATCH'
    assert np.array_equal(np.asarray(packet['controller_memory']['last_ctrl']),np.asarray(last_ctrl)),'INITIAL_CONTROL_MEMORY_MISMATCH'
    assert packet['controller_memory']['integral']==integral,'INITIAL_INTEGRAL_MEMORY_MISMATCH'
    assert time.time()<deadline,'SOURCE_SEARCH_DEADLINE_EXPIRED'
    setup=public_setup(setup)
    scope='pre_detection_static'if source is None else'post_detection_full_cycle'
    plan=search(copy.deepcopy(packet),copy.deepcopy(source),goal,copy.deepcopy(setup),deadline,scope)
    if not plan['passed']:
        assert 'planned_body_requests'not in plan and 'path'not in plan
        return dict(plan,next_action='HOLD_NO_QUALIFIED_COMPLETE_ROUTE')
    result=audit(plan,packet,source,setup,goal)
    assert result['passed'],'FULL_ROUTE_INDEPENDENT_ADMISSION_REJECTED'
    return dict(plan,full_input_admission=result,next_action='SOURCE_QUALIFIED_AWAIT_EXECUTION_INTEGRATION',
        partial_execution_not_authorized=True,physical_tracking_qualified=False)
