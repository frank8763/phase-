"""Sole-owner complete-profile scheduling and native tracking, no model imports.

Simulation-time development only: source preparation never advances the plant.
The caller must use run_phase.sh for every actual Vehicle.step. A static source
is revoked at the FIRST causal discovery callback and cannot resume its suffix.
"""
import math,time
import numpy as np
MAX_NATIVE=60000
class Owner:
    def __init__(self,vehicle,deadline,observe,progress=lambda *_:None):
        self.vehicle=vehicle;self.deadline=deadline;self.observe=observe;self.progress=progress;self.phase='STOPPED';self.events=[];self.maximum_position=0.;self.maximum_heading=0.;self.inside_native=False
    def execute(self,plan,interrupt_on_discovery=False):
        assert self.phase=='STOPPED','MULTIPLE_CONTROL_OWNERS'
        requests=np.asarray(plan['planned_body_requests'],float);states=np.asarray(plan['state_path'],float)
        assert plan['passed']and 200<=len(requests)<=MAX_NATIVE and requests.shape==(len(requests),3)and states.shape==(len(requests)+1,8),'INVALID_WHOLE_PROFILE'
        assert np.isfinite(requests).all()and np.isfinite(states).all()and np.all(requests[-200:]==0.),'PROFILE_TAIL_OR_FINITE'
        assert np.isin(requests[:,0],[0.,.03]).all()and np.all(requests[:,2]==0.),'INPUT_DOMAIN_CHANGED'
        assert np.all(abs(requests[:,1])<=.03*.758770385+1e-10),'STEERING_REQUEST_DOMAIN_CHANGED'
        origin=self.vehicle.count;body=np.asarray(self.vehicle.body());assert np.linalg.norm(body[:2]-states[0,:2])<=1e-8 and abs(body[2]-states[0,2])<=1e-8,'INITIAL_POSE_CHANGED'
        self.phase='PROFILE';interrupted=False
        try:
            for i,request in enumerate(requests):
                assert time.time()<self.deadline-120,'ABSOLUTE_MODEL_STOP_RESERVE'
                self.inside_native=True;self.vehicle.step(*request);self.inside_native=False
                body=self.vehicle.body();assert abs(body[3])<=.13 and abs(body[4])<=.16,'BODY_SPEED_OR_YAW_CAP'
                position=float(np.linalg.norm(np.asarray(body[:2])-states[i+1,:2]));d=body[2]-states[i+1,2];heading=abs(math.atan2(math.sin(d),math.cos(d)))
                self.maximum_position=max(self.maximum_position,position);self.maximum_heading=max(self.maximum_heading,heading)
                assert position<=.04 and heading<=.035,'NATIVE_TRACKING_FAILED'
                if self.vehicle.count%5==0:
                    discovered=bool(self.observe())
                    if interrupt_on_discovery and discovered:interrupted=True;break
                if self.vehicle.count%100==0:self.progress(self.vehicle,self)
            self.phase='BRAKE_REQUIRED'if interrupted else'STOPPED'
            if not interrupted:
                assert np.linalg.norm(np.asarray(self.vehicle.body()[3:]))<=.03,'PROFILE_NOT_STOPPED'
            result=dict(completed=not interrupted,interrupted_by_causal_discovery=interrupted,origin_native=origin,end_native=self.vehicle.count,
                new_native=self.vehicle.count-origin,maximum_position_error_m=self.maximum_position,maximum_heading_error_rad=self.maximum_heading)
            self.events.append(result);return result
        except BaseException:
            self.phase='FAILED';raise
    def authorize_brake(self):
        assert self.phase=='BRAKE_REQUIRED','BRAKE_WITHOUT_INTERRUPTION';self.phase='STOPPED'
