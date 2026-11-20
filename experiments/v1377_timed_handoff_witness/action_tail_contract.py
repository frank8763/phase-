"""Separate applied transitions from final observation; no physical admission."""
from response_membership_contract import audit


def audit_with_actions(samples,reference,actions,**kwargs):
    assert len(samples)==len(actions)+1,'STATE_ACTION_CARDINALITY'
    assert len(actions)>=200,'INCOMPLETE_ACTION_TAIL'
    for state,next_state,action in zip(samples,samples[1:],actions):
        assert action['before_native']==state['native_tick'],'ACTION_STATE_TICK_MISMATCH'
        assert next_state['native_tick']==action['before_native']+1,'ACTION_NEXT_STATE_TICK_MISMATCH'
        assert action['applied'] is True,'ACTION_NOT_APPLIED'
        assert action['request']==state['command'],'ACTION_REQUEST_BINDING'
    assert all(action['request']==[0.,0.] for action in actions[-200:]),'INCOMPLETE_200_APPLIED_ZERO_ACTIONS'
    result=audit(samples,reference,**kwargs)
    return dict(result,applied_transition_count=len(actions),complete_applied_zero_tail_native=200,
        final_state_not_counted_as_action=True,
        action_metadata_not_proof_of_physical_provenance=True,
        physical_admission=False,actual_moving_response_qualified=False)
