"""MPPI event session, preserving original250 CUSP and distinct200 plan gates."""
import copy
import importlib.util
import math
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
original=exact('v1483_original_ordered_requests',R/'experiments/v1422_ordered_route_event/session.py')
event=original.event;digest=event.digest
controller=exact('v1483_session_controller',C/'controller_identity.py')

def prepare_request(*args,controller_binding,verified_controller_sha256,**kwargs):
 identity=controller.verify_prepared(controller_binding,expected_sha256=verified_controller_sha256)
 packet=original.prepare_request(*args,**kwargs)
 # Outer identity binds the plugin without changing the original request hash,
 # measured envelope, stop requirement or ordered queue contract.
 return dict(packet,controller_binding=copy.deepcopy(controller_binding),controller_identity_sha256=identity)

class Session:
    def __init__(self,packet,*,controller_identity_sha256):
        assert packet['kind']=='BRIDGE_CERTIFICATE_REQUEST'
        event.validate_request(packet['request'])
        self.controller_identity_sha256=controller.verify_prepared(packet['controller_binding'],expected_sha256=controller_identity_sha256)
        assert packet['controller_identity_sha256']==self.controller_identity_sha256,'EVENT_CONTROLLER_CHANGED'
        request=packet['request'];value=dict(request);identity=value.pop('request_sha256')
        assert digest(value)==identity and digest(packet['causal_snapshot'])==packet['coefficient_snapshot_sha256']==request['causal_forecast']['coefficient_snapshot_sha256']
        self.packet=copy.deepcopy(packet);self.request_sha256=identity
        self.run_id=request['run_id'];self.event_index=request['event_index'];self.phase='WAIT_CERTIFICATE'
        self.input_sha256=None;self.certificate_sha256=None;self.consumed=False

    def accept(self,value):
        assert value['controller_identity_sha256']==self.controller_identity_sha256,'BRIDGE_NOTICE_CONTROLLER_CHANGED'
        assert value['run_id']==self.run_id and value['event_index']==self.event_index and value['request_sha256']==self.request_sha256, 'BRIDGE_TRANSACTION_IDENTITY_CHANGED'
        assert value['kind']in {'BRIDGE_CERTIFICATE_READY','BRIDGE_MPPI_READY','BRIDGE_COMPLETE','BRIDGE_FAILED'}
        if value['kind']=='BRIDGE_FAILED':
            assert not self.consumed;self.phase='FAILED';return dict(close_round=True,consume_segment=False)
        if self.phase=='WAIT_CERTIFICATE':
            assert value['kind']=='BRIDGE_CERTIFICATE_READY' and value['model_generation_passed']is True and value['independent_model_audit_passed']is True, 'BRIDGE_CERTIFICATE_NOT_COMPLETE'
            for key in ['input_sha256','certificate_sha256']:
                assert isinstance(value[key],str)and len(value[key])==64 and set(value[key])<=set('0123456789abcdef')
            self.input_sha256=value['input_sha256'];self.certificate_sha256=value['certificate_sha256'];self.phase='EXECUTING_PREPARATION'
            return dict(close_round=False,consume_segment=False)
        assert value['input_sha256']==self.input_sha256 and value['certificate_sha256']==self.certificate_sha256, 'BRIDGE_COMMITTED_WITNESS_CHANGED'
        if value['kind']=='BRIDGE_MPPI_READY':
            assert self.phase=='EXECUTING_PREPARATION';self.phase='EXECUTING_ENGINEERING_MPPI'
            return dict(install_engineering_MPPI_path=True,consume_segment=False)
        assert value['kind']=='BRIDGE_COMPLETE' and self.phase in {'EXECUTING_PREPARATION','EXECUTING_ENGINEERING_MPPI'}and not self.consumed
        assert all(value[k]is True for k in ['complete_actual_native_coverage','complete200_applied_zero_tail','source_control_state_gates_passed']), 'BRIDGE_ACTUAL_EVIDENCE_INCOMPLETE'
        assert math.isfinite(value['endpoint_position_m'])and 0<=value['endpoint_position_m']<=.12
        assert math.isfinite(value['endpoint_heading_rad'])and 0<=value['endpoint_heading_rad']<=.20
        self.consumed=True;self.phase='COMPLETE'
        return dict(consume_segment=True,close_round=False)
