"""Disclosed fixed signed rear-path tracker. No plant/model access or imports.

Shared bridge contribution, not the original RPP controller. Targets come only
from the actual original ordered segment. No saved controls or native labels.
"""
import copy
import hashlib
import json
import math
CAP=.42722137342572125
LOOKAHEAD=.6
MAX_CURVATURE=math.tan(CAP)/.6
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def angle(value):return math.atan2(math.sin(value),math.cos(value))


def rear(body):
    assert len(body)==5 and all(type(v)in(int,float)and math.isfinite(v)for v in body)
    return (body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2])


class SegmentTracker:
    def __init__(self,segment,*,origin_body,origin_native,origin_sim_time):
        assert set(segment)=={'gear','poses'}and type(segment['gear'])is int and segment['gear']in (-1,1)
        poses=segment['poses'];assert isinstance(poses,list)and len(poses)>=2
        assert all(isinstance(p,list)and len(p)==3 and all(type(v)in(int,float)and math.isfinite(v)for v in p)for p in poses)
        self.poses=tuple(tuple(p)for p in poses);self.gear=segment['gear'];self.segment_sha256=digest(segment)
        self.arc=[0.]
        for a,b in zip(self.poses,self.poses[1:]):
            length=math.dist(a[:2],b[:2]);assert length>1e-10,'SEGMENT_ZERO_LENGTH_EDGE'
            self.arc.append(self.arc[-1]+length)
        assert type(origin_native)is int and origin_native>=0 and abs(origin_sim_time-.01*origin_native)<=1e-8
        actual=rear(origin_body)
        assert math.dist(actual[:2],self.poses[0][:2])<=.12+1e-8,'CURRENT_ENTRY_POSE_REQUIRES_SEPARATE_CAPTURE'
        assert abs(angle(actual[2]-self.poses[0][2]))<=.20+1e-8,'CURRENT_ENTRY_HEADING_REQUIRES_SEPARATE_CAPTURE'
        self.origin=origin_native;self.sim_origin=origin_sim_time;self.previous_native=origin_native-5
        self.progress=0.;self.pending=None;self.failed=False

    def fork(self):
        assert not self.failed and self.pending is None
        return copy.deepcopy(self)

    def point(self,s):
        assert 0<=s<=self.arc[-1]+1e-10
        for index,(lo,hi)in enumerate(zip(self.arc,self.arc[1:])):
            if s<=hi or index==len(self.poses)-2:
                u=max(0.,min(1.,(s-lo)/(hi-lo)));a=self.poses[index];b=self.poses[index+1]
                return (a[0]+u*(b[0]-a[0]),a[1]+u*(b[1]-a[1]),angle(a[2]+u*angle(b[2]-a[2])))
        raise AssertionError('ORDERED_SEGMENT_ARC_OUTSIDE')

    def select(self,body,*,native_tick,sim_time):
        assert not self.failed and self.pending is None
        assert type(native_tick)is int and native_tick>=self.origin
        assert native_tick-self.origin<=6000 and native_tick-self.previous_native>=5
        assert (native_tick-self.origin)%5==0
        assert abs(sim_time-(self.sim_origin+.01*(native_tick-self.origin)))<=1e-8
        actual=rear(body);options=[]
        for index,(a,b)in enumerate(zip(self.poses,self.poses[1:])):
            lo,hi=self.arc[index:index+2]
            if hi<self.progress:continue
            dx,dy=b[0]-a[0],b[1]-a[1];norm=dx*dx+dy*dy
            u=max(0.,min(1.,((actual[0]-a[0])*dx+(actual[1]-a[1])*dy)/norm))
            s=max(self.progress,lo+u*(hi-lo))
            if s>hi:continue
            p=self.point(s);options.append((math.dist(actual[:2],p[:2]),s))
        assert options
        _,s=min(options)
        target=self.point(min(self.arc[-1],s+LOOKAHEAD));end=self.poses[-1]
        distance=math.dist(actual[:2],end[:2]);yaw=abs(angle(actual[2]-end[2]))
        terminal=distance<=.10 and yaw<=.15
        if terminal:
            raw=(0.,0.,0);v=w=0.;curvature=0.
        else:
            travel_yaw=actual[2]+(math.pi if self.gear<0 else 0.)
            dx,dy=target[0]-actual[0],target[1]-actual[1]
            lateral=-math.sin(travel_yaw)*dx+math.cos(travel_yaw)*dy
            norm=dx*dx+dy*dy
            assert norm>1e-12,'NONTERMINAL_CARROT_AT_CURRENT_REAR'
            # Signed geometric curvature; bound steering as explicitly
            # registered for this bridge, before original canonical gear.
            travel_curvature=max(-MAX_CURVATURE,min(MAX_CURVATURE,2*lateral/norm))
            v=.08 if self.gear>0 else -.03
            curvature=travel_curvature*self.gear;w=v*curvature
            raw=(math.atan(.6*curvature),v,0)
        decision=dict(before_native=native_tick,sim_time=sim_time,progress_before_m=self.progress,
            proposed_progress_m=s,segment_sha256=self.segment_sha256,carrot=list(target),
            raw_row=list(raw),body_request=[v,w],terminal_requested=terminal,
            endpoint_rear_error_m=distance,endpoint_heading_error_rad=yaw,
            shared_policy='DISCLOSED_GOAL_BOUND_SIGNED_REAR_SEGMENT_TRACKER',
            feedback_hold_native=5,control_owner='DISCLOSED_SHARED_EXECUTION_BRIDGE')
        decision['decision_sha256']=digest(decision)
        self.pending=copy.deepcopy(decision)
        return copy.deepcopy(decision)

    def commit(self,decision,*,applied_native,applied_request_receipts_sha256):
        assert not self.failed and self.pending==decision
        try:
            assert applied_native==5 and isinstance(applied_request_receipts_sha256,str)and len(applied_request_receipts_sha256)==64
            self.progress=decision['proposed_progress_m'];self.previous_native=decision['before_native']
            self.pending=None
        except BaseException:
            self.failed=True;raise
