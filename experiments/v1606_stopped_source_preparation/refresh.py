"""One preparation -> one real current source transaction, no control rights."""
import copy
import hashlib
import json
import time
from pathlib import Path
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def anchor(request):
    # CUSP only is the existing method12 first-event domain. Ordered post-bridge
    # events remain outside this narrow first-event runtime authority.
    assert request['event']['kind']=='CUSP_NEXT_SEGMENT_CHECK'and request['event_index']==0
    actual=request['actual'];feedback=actual['feedback']
    return dict(run_id=request['run_id'],event_index=request['event_index'],
        event_kind=request['event']['kind'],brake_start=request['brake_start'],
        next_segment=copy.deepcopy(request['next_segment']),event_gear=request['event']['gear'],
        event_body=copy.deepcopy(request['event']['body']),
        native=actual['wire']['native_tick'],sim_time=actual['wire']['sim_time'],
        evidence_state_sha256=actual['evidence_state_sha256'],feedback=copy.deepcopy(feedback))

class Refresh:
    def __init__(self,history,*,initial_notice,prepared_monotonic):
        assert not history.poisoned and not history.refresh_consumed
        history.same_stopped_state()
        self.history=history;self.initial=copy.deepcopy(initial_notice)
        self.anchor=anchor(history.packet['request']);self.prepared_at=prepared_monotonic
        self.token=None;self.closed=False;self.failed=False;self.final_started=False

    def bind_one_fresh_envelope(self,envelope):
        assert not self.closed and not self.failed and self.token is None
        self.failed=True;h=self.history;h.same_stopped_state();wire=envelope['wire']
        assert wire==h.native.sent[wire['sequence']]
        assert wire['native_tick']==self.anchor['native']and wire['sim_time']==self.anchor['sim_time']
        assert wire['sequence']>h.sequence and wire['sampled_at']>self.prepared_at,'REFRESH_REQUIRES_NEW_REAL_ACQUISITION'
        assert envelope['evidence_state_sha256']==self.anchor['evidence_state_sha256']
        assert envelope['feedback']==self.anchor['feedback']
        self.token=dict(kind='SOURCE_HISTORY_PREPARED',run_id=self.anchor['run_id'],event_index=0,
            initial_request_sha256=h.packet['request']['request_sha256'],initial_notice_sha256=digest(self.initial),
            history_proof_sha256=h.proof_sha256,stopped_identity_sha256=digest(h.identity),
            expected_wire_sequence=wire['sequence'],expected_wire_sha256=digest(wire),
            native_tick=wire['native_tick'],sim_time=wire['sim_time'],prepared_monotonic=self.prepared_at,
            numerical_permission=False,physical_permission=False)
        self.failed=False;return copy.deepcopy(self.token)

    def accept_final(self,packet,notice):
        assert not self.closed and not self.failed and not self.final_started and self.token is not None
        self.failed=True;self.final_started=True;self.history.refresh_consumed=True
        assert notice['kind']=='CURRENT_SOURCE_REFRESH_REQUEST_FILE'
        assert notice['source_preparation_token_sha256']==digest(self.token)
        assert packet['source_preparation_token']==self.token
        request=packet['request'];wire=request['actual']['wire']
        assert anchor(request)==self.anchor,'REFRESH_CHANGED_STOPPED_EVENT_CONTRACT'
        assert wire['sequence']==self.token['expected_wire_sequence']and digest(wire)==self.token['expected_wire_sha256']
        self.history.same_stopped_state();self.failed=False
        return True

def refreshed_packet(initial_packet,token,envelope,*,tracker,geometry,prepare_request,now):
    """Actual ROS caller passes its one original tracker and real envelope."""
    request=initial_packet['request'];wire=envelope['wire']
    assert token['kind']=='SOURCE_HISTORY_PREPARED'and token['run_id']==request['run_id']
    assert token['initial_request_sha256']==request['request_sha256']
    assert wire['sequence']==token['expected_wire_sequence']and digest(wire)==token['expected_wire_sha256']
    assert wire['native_tick']==token['native_tick']and wire['sim_time']==token['sim_time']
    assert 0<=now-wire['sampled_at']<=.2
    packet=prepare_request(envelope,request['next_segment'],geometry,tracker,
        run_id=request['run_id'],event_index=request['event_index'],brake_start=request['brake_start'],now=now)
    assert anchor(packet['request'])==anchor(request),'ROS_REFRESH_CHANGED_EVENT_CONTRACT'
    packet['source_preparation_token']=copy.deepcopy(token)
    return packet
