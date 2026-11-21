"""One current-input-bound finite method, shared by model and later runtime."""
import copy
import importlib.util
from pathlib import Path

R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v1406_frozen_finite_dispatch',Path(__file__).with_name('method_dispatch.py'));dispatch=importlib.util.module_from_spec(spec);spec.loader.exec_module(dispatch)


def expected_spec(current):
    identity_path=Path(__file__).with_name('controller_identity.py');spec=importlib.util.spec_from_file_location('v1483_method_identity',identity_path);identity=importlib.util.module_from_spec(spec);spec.loader.exec_module(identity);identity.verify_current(current)
    request=dict(event=dict(body=current['origin']['body'],geometry=current['event_geometry']),next_segment=current['next_segment'],
                 actual=dict(feedback=dict(gear_memory=current['gear_memory'])))
    expected=dispatch.choose(request)
    assert expected==current['method_spec'], 'CURRENT_METHOD_SELECTION_OR_PARAMETERS_CHANGED'
    return expected


class Method:
    def __init__(self,current):
        self.spec=expected_spec(current);self.name=self.spec['method'];self.origin=current['origin']['native_tick']
        self.previous_tick=self.origin-1;self.capture=None;self.reverse=None;self.tail_start=None;self.segment=current['next_segment'];self.cached=None
        if self.name=='ORIGINAL_TWO_ARC_CAPTURE_THEN_ENGINEERING_COHERENT_MPPI':self.capture=dispatch.capture.Capture(self.spec['task']);self.phase='CAPTURE'
        elif self.name=='ORIGINAL_BOUNDED_STEERING_THEN_GEAR_RELEASE_TIMED_REVERSE':self.reverse=dispatch.ReverseBridge(self.spec['task']);self.phase='FINITE_REVERSE'
        else:assert self.name=='ENGINEERING_COHERENT_MPPI_CURRENT_RESPONSE';self.phase='MPPI'

    def select(self,body,tick,encoders,last_ctrl):
        assert type(tick)is int and tick==self.previous_tick+1, 'CURRENT_METHOD_NATIVE_GAP'
        self.previous_tick=tick
        # The qualified component controllers sample feedback every5native;
        # the gear guard and braking alternatives still execute every native.
        if self.cached is None or (tick-self.origin)%5==0:self.cached=self.refresh(body,tick,encoders,last_ctrl)
        return copy.deepcopy(self.cached)

    def refresh(self,body,tick,encoders,last_ctrl):
        target=None;requested=None;metadata={}
        if self.phase=='CAPTURE':
            v,w,metadata=self.capture.select(body,tick,encoders,last_ctrl);requested=[v,w];target=metadata['parked_target']
            if metadata['phase']=='CAPTURE_COMPLETE':self.phase='CAPTURE_TAIL';self.tail_start=tick;requested=[0.,0.];target=None
        elif self.phase=='CAPTURE_TAIL':
            requested=[0.,0.]
            if tick-self.tail_start>=200:
                position,heading=dispatch.capture.errors(body,self.segment)
                assert position<=.12 and heading<=.20, 'CAPTURED_CURRENT_START_OUTSIDE_ORIGINAL_SEGMENT_BOUND'
                assert max(abs(x)for x in body[3:])<=.003 and max(abs(x)for x in encoders[2:])<=.03 and max(abs(x)for x in last_ctrl[2:])<=1e-10
                self.phase='MPPI';requested=None
        elif self.phase=='FINITE_REVERSE':
            v,w,metadata=self.reverse.select(body,tick,encoders,last_ctrl);requested=[v,w];target=metadata['parked_target']
            if metadata['phase']=='RESPONSE_COMPLETE':self.phase='FINAL_TAIL';self.tail_start=tick;requested=[0.,0.];target=None
        if self.phase=='FINAL_TAIL':requested=[0.,0.];target=None
        return dict(phase=self.phase,requested=requested,parked_target=target,metadata=metadata,
                    mppi_required=self.phase=='MPPI',final_tail_start=self.tail_start if self.phase=='FINAL_TAIL'else None,
                    control_owner='ENGINEERING_COHERENT_MPPI'if self.phase=='MPPI'else'DISCLOSED_SHARED_EXECUTION_BRIDGE')

    def mppi_done(self,tick):
        assert self.phase=='MPPI'and tick==self.previous_tick
        self.phase='FINAL_TAIL';self.tail_start=tick
        self.cached=dict(phase=self.phase,requested=[0.,0.],parked_target=None,metadata={},mppi_required=False,final_tail_start=tick,control_owner='DISCLOSED_SHARED_EXECUTION_BRIDGE')

    def observe_gear(self,tick,proof):
        if self.reverse is not None:self.reverse.observe_gear(tick,proof)
