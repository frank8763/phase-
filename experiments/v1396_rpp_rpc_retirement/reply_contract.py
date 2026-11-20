"""Retire valid superseded RPC replies; never admit a stale or changed source."""
def assess(reply,wire,*,run_id,current_native,previous_accepted,now):
    assert reply['run_id']==wire['run_id']==run_id,'FOREIGN_RPC_RUN'
    assert reply['sequence']==wire['sequence'] and type(reply['sequence']) is int,'UNBOUND_RPC_SEQUENCE'
    assert wire['native_tick']<=current_native,'RPC_SOURCE_FROM_FUTURE_STATE'
    assert reply['kind'] in ('RPP_ACTION_DONE','ORIGINAL_RPP_ACTUAL_COMMAND'),'UNKNOWN_RPC_REPLY_KIND'
    observation_age=now-wire['sampled_at'];assert observation_age>=0.,'RPC_OBSERVATION_FROM_FUTURE'
    if reply['kind']=='ORIGINAL_RPP_ACTUAL_COMMAND':
        assert reply['actual_frame_bound'] and reply['body']==wire['body'],'RPC_BODY_CHANGED'
        assert reply['native_tick']==reply['observation_native_tick']==wire['native_tick'],'RPC_TICK_CHANGED'
        assert reply['observation_sequence']==wire['sequence'] and reply['observation_sampled_at']==wire['sampled_at'],'RPC_ACQUISITION_CHANGED'
        generation_age=now-reply['origin']['generated_monotonic'];assert generation_age>=0.,'RPC_COMMAND_FROM_FUTURE'
    else:generation_age=None
    if wire['native_tick']<current_native:reason='SUPERSEDED_ACTUAL_STATE'
    elif reply['sequence']<=previous_accepted:reason='ALREADY_CONSUMED_SEQUENCE'
    elif observation_age>.2:reason='EXPIRED_OBSERVATION'
    elif generation_age is not None and generation_age>.2:reason='EXPIRED_GENERATION'
    else:reason='CURRENT_FRESH_SOURCE'
    return dict(accepted=reason=='CURRENT_FRESH_SOURCE',reason=reason,source_native_tick=wire['native_tick'],current_native_tick=current_native,sequence=wire['sequence'],previous_accepted=previous_accepted,checked_monotonic=now,observation_age_s=observation_age,generation_age_s=generation_age)
