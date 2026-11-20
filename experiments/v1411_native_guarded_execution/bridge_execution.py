"""Execute live finite feedback; never replay the modeled control array."""
import copy
import importlib.util
import math
from pathlib import Path
import time
import sys

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1397_event_handoff_integration'))


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


Method=exact('v1411_exact_live_finite_method',R/'experiments/v1406_complete_finite_witness/method.py').Method
Reference=exact('v1411_original_fixed_response',R/'experiments/v1397_event_handoff_integration/response_reference.py').ResponseReference
Commands=exact('v1411_actual_route_commands',Path(__file__).with_name('route_command.py')).Commands


class BridgeExecution:
    def __init__(self,request,native,states):
        assert request.committed and not request.closed
        assert native.vehicle.count==request.start_native and native.applied==request.start_native
        assert native.mode_memory.snapshot(request.start_native)==request.mode_history
        assert native.physical_guard.checked==request.start_native
        assert native.reserve.snapshot_sha256==request.current['causal_snapshot_sha256']
        self.request=request;self.native=native;self.method=Method(request.current)
        self.reference=Reference(request.session.packet['request'],states)
        self.commands=Commands(native.run_id);self.pending=None;self.local=None;self.rpp_ready=False
        self.start=native.applied;self.initial_plugin=native.plugin_native;self.initial_bridge=native.bridge_native
        self.rpp_command=None;native.bridge_started=True
        self.initial_stop=native.stop_native;self.complete=False;self.done_source=None

    def notice(self,kind,**extra):
        r=self.request
        return dict(kind=kind,run_id=self.native.run_id,event_index=r.session.event_index,
                    request_sha256=r.session.request_sha256,input_sha256=r.current['input_sha256'],certificate_sha256=r.certificate_sha256,**extra)

    def advance(self,*,rpp_packet=None,action_done=None):
        assert not self.complete
        n=self.native;v=n.vehicle;tick=v.count
        if self.pending is None:
            self.pending=self.method.select(list(v.body()),tick,v.steering_sample().tolist(),v.adapter.last)
        d=self.pending;phase=d['phase'];requested=d['requested'];target=d['parked_target']
        if phase=='RPP':
            if not self.rpp_ready:
                self.rpp_ready=True
                return self.notice('BRIDGE_RPP_READY')
            if action_done is not None:
                for k,value in self.notice('BRIDGE_RPP_ACTION_DONE').items():assert action_done[k]==value,'BRIDGE_ACTION_DONE_IDENTITY'
                assert action_done['status']==4 and action_done['error_code']==0,'ORIGINAL_RPP_ACTION_REFUSED'
                assert self.done_source is None
                self.done_source=copy.deepcopy(dict(action_done,received_native=tick,received_monotonic=time.monotonic()))
                self.method.rpp_done(tick);phase='FINAL_TAIL';requested=[0.,0.];target=None
            else:
                refresh=self.rpp_command is None or (tick-self.method.origin)%5==0
                if refresh:
                    if rpp_packet is None:return dict(kind='WAIT_ORIGINAL_RPP',native_tick=tick)
                    command=self.commands.accept(rpp_packet,n.sent,current_native=tick,now=time.monotonic())
                    if command is None:return dict(kind='RETIRED_ROUTE_COMMAND',native_tick=tick)
                    if command['control_owner']=='ORIGINAL_RPP':assert command['delivery']['command_source']=='ORIGINAL_RPP_WITH_SHARED_BRIDGE','WRONG_PATH_STAGE_RPP_SOURCE'
                    self.rpp_command=command
                else:assert rpp_packet is None,'UNCONSUMED_COMMAND_DURING_ORIGINAL5_NATIVE_HOLD'
                command=self.rpp_command
                requested=[command['v'],command['w']];delivery=command['delivery'];owner=command['control_owner']
        elif action_done is not None or rpp_packet is not None:
            raise AssertionError('RPP_PACKET_OUTSIDE_CURRENT_RPP_STAGE')
        if phase!='RPP':
            assert requested is not None
            # Fixed 5native control feedback cadence, with fresh actual wire
            # supplied by the outer producer. No scan is acquired here.
            if self.local is None or (tick-self.method.origin)%5==0 or phase=='FINAL_TAIL':
                wire=max(n.sent.values(),key=lambda x:x['sequence']);assert 0<=tick-wire['native_tick']<5
                self.local=dict(source_kind='ACTUAL_FRAME',run_id=n.run_id,origin=dict(kind='LOCAL_SHARED_ACTUAL_FEEDBACK',generated_monotonic=time.monotonic()),
                                observation_sequence=wire['sequence'],observation_native_tick=wire['native_tick'],observation_sampled_at=wire['sampled_at'],
                                method=self.method.name,request_sha256=self.request.session.request_sha256)
            delivery=self.local;owner='DISCLOSED_SHARED_EXECUTION_BRIDGE'
        tail=phase=='FINAL_TAIL'
        proof=n.apply(*requested,phase=phase,control_owner='APPLIED_STOP_TAIL' if tail else owner,delivery=delivery,
                      parked_target=target,monitor=self.reference,stop_tail=tail)
        self.method.observe_gear(tick,proof);self.pending=None
        if tail and self.method.tail_start is not None and v.count-self.method.tail_start==200:
            body=list(v.body());goal=self.request.current['next_segment']['poses'][-1]
            rear=[body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2])]
            position=math.dist(rear,goal[:2]);heading=abs(math.atan2(math.sin(body[2]-goal[2]),math.cos(body[2]-goal[2])))
            assert position<=.12 and heading<=.20
            assert max(abs(x)for x in body[3:])<=.003 and max(abs(x)for x in v.steering_sample()[2:])<=.03
            assert max(abs(x)for x in v.adapter.last[2:])<=1e-10 and n.last_zero_count==200
            self.complete=True;self.request.closed=True
            return self.notice('BRIDGE_COMPLETE',complete_actual_native_coverage=True,complete200_applied_zero_tail=True,
                               source_control_state_gates_passed=True,endpoint_position_m=position,endpoint_heading_rad=heading,
                               final_native_tick=v.count,original_RPP_native=n.plugin_native-self.initial_plugin,
                               shared_bridge_native=n.bridge_native-self.initial_bridge,applied_stop_tail_native=n.stop_native-self.initial_stop)
        return dict(kind='ACTUAL_NATIVE_APPLIED',before_native=tick,phase=phase)
