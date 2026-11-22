"""Bind both recorded actual measurement paths, without claiming ROS transport."""

def bind(event, *, sent, run_id, state_at, validate_wire, state_digest):
    kind=event['kind']
    if kind not in {'PUBLISHED_ACTUAL_ENVELOPE','CURRENT_SHARED_POLICY_DELIVERY'}:
        return None
    envelope=event['envelope'];wire=envelope['wire'];validate_wire(wire)
    assert wire['run_id']==run_id and wire['sequence'] not in sent
    assert state_digest(state_at(wire['native_tick']))==envelope['evidence_state_sha256'], 'MEASURED_ENVELOPE_FULLSTATE_CHANGED'
    sent[wire['sequence']]=wire
    return dict(sequence=wire['sequence'],native_tick=wire['native_tick'],
        measurement_path=kind,transported_to_ROS=kind=='PUBLISHED_ACTUAL_ENVELOPE')
