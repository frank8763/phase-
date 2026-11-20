"""Identity-bound cusp transaction; never infer a certificate from geometry."""
import copy
import importlib.util
import math
from pathlib import Path
import sys

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1397_event_handoff_integration'))
from route_event import make_request,digest
from causal_bridge_field import all_future
assert Path(make_request.__code__.co_filename).resolve()==R/'experiments/v1397_event_handoff_integration/route_event.py'


def prepare_request(envelope,segment,geometry,tracker,*,run_id,event_index,brake_start,now):
    snapshot=tracker.snapshot()
    forecast=all_future(snapshot,current_native=envelope['wire']['native_tick'],current_sim_time=envelope['wire']['sim_time'])
    request=make_request(envelope,segment,geometry,forecast,run_id=run_id,event_index=event_index,brake_start=brake_start,now=now)
    return dict(kind='BRIDGE_CERTIFICATE_REQUEST',request=request,causal_snapshot=snapshot,
                coefficient_snapshot_sha256=digest(snapshot),physical_admission=False)


class Session:
    def __init__(self,packet):
        assert packet['kind']=='BRIDGE_CERTIFICATE_REQUEST'
        request=packet['request'];value=dict(request);identity=value.pop('request_sha256')
        assert digest(value)==identity and digest(packet['causal_snapshot'])==packet['coefficient_snapshot_sha256']==request['causal_forecast']['coefficient_snapshot_sha256']
        self.packet=copy.deepcopy(packet);self.request_sha256=identity
        self.run_id=request['run_id'];self.event_index=request['event_index'];self.phase='WAIT_CERTIFICATE'
        self.input_sha256=None;self.certificate_sha256=None;self.consumed=False

    def accept(self,value):
        assert value['run_id']==self.run_id and value['event_index']==self.event_index and value['request_sha256']==self.request_sha256, 'BRIDGE_TRANSACTION_IDENTITY_CHANGED'
        assert value['kind']in {'BRIDGE_CERTIFICATE_READY','BRIDGE_RPP_READY','BRIDGE_COMPLETE','BRIDGE_FAILED'}
        if value['kind']=='BRIDGE_FAILED':
            assert not self.consumed;self.phase='FAILED';return dict(close_round=True,consume_segment=False)
        if self.phase=='WAIT_CERTIFICATE':
            assert value['kind']=='BRIDGE_CERTIFICATE_READY' and value['model_generation_passed']is True and value['independent_model_audit_passed']is True, 'BRIDGE_CERTIFICATE_NOT_COMPLETE'
            for key in ['input_sha256','certificate_sha256']:
                assert isinstance(value[key],str)and len(value[key])==64 and set(value[key])<=set('0123456789abcdef')
            self.input_sha256=value['input_sha256'];self.certificate_sha256=value['certificate_sha256'];self.phase='EXECUTING_PREPARATION'
            return dict(close_round=False,consume_segment=False)
        assert value['input_sha256']==self.input_sha256 and value['certificate_sha256']==self.certificate_sha256, 'BRIDGE_COMMITTED_WITNESS_CHANGED'
        if value['kind']=='BRIDGE_RPP_READY':
            assert self.phase=='EXECUTING_PREPARATION';self.phase='EXECUTING_ORIGINAL_RPP'
            return dict(install_original_RPP_path=True,consume_segment=False)
        assert value['kind']=='BRIDGE_COMPLETE' and self.phase in {'EXECUTING_PREPARATION','EXECUTING_ORIGINAL_RPP'}and not self.consumed
        assert all(value[k]is True for k in ['complete_actual_native_coverage','complete200_applied_zero_tail','source_control_state_gates_passed']), 'BRIDGE_ACTUAL_EVIDENCE_INCOMPLETE'
        assert math.isfinite(value['endpoint_position_m'])and 0<=value['endpoint_position_m']<=.12
        assert math.isfinite(value['endpoint_heading_rad'])and 0<=value['endpoint_heading_rad']<=.20
        self.consumed=True;self.phase='COMPLETE'
        return dict(consume_segment=True,close_round=False)
