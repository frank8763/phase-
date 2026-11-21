"""Fixed finite bridge methods; no plant access and no driving permission."""
import importlib.util
import math
from pathlib import Path

R=Path(__file__).resolve().parents[2]


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


prepared=exact('v1404_original_bounded_steering',R/'experiments/v1378_steering_response_32210/controller.py')
timed=exact('v1404_original_timed_reverse',R/'experiments/v1383_exact_timed_handoff/controller.py')
capture=exact('v1404_original_two_arc_capture',R/'experiments/v1376_prepared_capture_component/controller.py')


def choose(request):
    body=request['event']['body'];segment=request['next_segment'];geometry=request['event']['geometry']
    assert len(body)==5 and max(abs(x)for x in body[3:])<=.003, 'BRIDGE_REQUIRES_CURRENT_MEASURED_REST'
    distance=geometry['start_distance_m'];yaw=geometry['start_heading_rad'];gear=segment['gear']
    assert gear in(-1,1)and all(math.isfinite(x)and x>=0. for x in(distance,yaw))
    if distance>.12 or yaw>.20:
        assert gear==1, 'REVERSE_POSE_CAPTURE_OUTSIDE_QUALIFIED_METHOD'
        method='ORIGINAL_TWO_ARC_CAPTURE_THEN_ENGINEERING_COHERENT_MPPI'
        task=dict(reverse_curvature=.5,reverse_distance=.25,forward_curvature=-.5,forward_distance=.15,speed=.1)
    elif geometry.get('minimum_clearance_m',-math.inf)<.22 and gear==-1:
        assert request['actual']['feedback']['gear_memory']['gear']==1, 'TIMED_REVERSE_REQUIRES_ORIGINAL_FORWARD_TO_REVERSE_RELEASE'
        method='ORIGINAL_BOUNDED_STEERING_THEN_GEAR_RELEASE_TIMED_REVERSE'
        task=dict(forward_curvature=-.5,ready_hold_native=20,target_segment=segment,
                  length_source='CURRENT_REAR_TO_GOAL_AFTER_PREPARATION_AND_FULL200_TAIL')
    else:method='ENGINEERING_COHERENT_MPPI_CURRENT_RESPONSE';task={}
    return dict(method=method,task=task,physical_admission=False,control_emitted=False,current_complete_witness_required=True)


class ReverseBridge:
    """Exact original steering and release-driven profile, with no saved tick."""
    def __init__(self,task):
        self.task=task;self.preparation=prepared.Capture(task);self.drive=None;self.phase='PREPARE';self.last_tick=None;self.tail_start=None

    def select(self,body,tick,encoders,last_ctrl):
        assert self.last_tick is None or tick>self.last_tick, 'BRIDGE_CLOCK_NOT_ADVANCING'
        self.last_tick=tick
        if self.phase=='PREPARE':
            v,w,proof=self.preparation.select(body,tick,encoders,last_ctrl)
            if proof['phase']=='RESPONSE_COMPLETE':self.phase='PREPARATION_TAIL';self.tail_start=tick
            else:return v,w,dict(proof,bridge_phase='PREPARE')
        if self.phase=='PREPARATION_TAIL':
            if tick-self.tail_start<200:return 0.,0.,dict(phase='PREPARATION_COMPLETE_STOP_TAIL',parked_target=None,bridge_phase='PREPARATION_TAIL')
            assert max(abs(x)for x in body[3:])<=.003 and max(abs(x)for x in encoders[2:])<=.03 and max(abs(x)for x in last_ctrl[2:])<=1e-10
            rear=[body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2])]
            length=math.dist(rear,self.task['target_segment']['poses'][-1][:2])
            assert math.isfinite(length)and .15<=length<=.3996434672909046+1e-8, 'TIMED_REVERSE_LENGTH_OUTSIDE_SAVED_FINITE_SCOPE'
            self.drive=timed.Capture(dict(reference_length_m=length));self.phase='TIMED'
        v,w,proof=self.drive.select(body,tick,encoders,last_ctrl)
        return v,w,dict(proof,bridge_phase='TIMED',control_owner='DISCLOSED_SHARED_EXECUTION_BRIDGE')

    def observe_gear(self,tick,proof):
        if self.phase=='TIMED':self.drive.observe_gear(tick,proof)
