"""Registered timed candidate's command/clock contract, SOFTWARE ONLY.

No plant, actuator prediction, physics imports or physical execution entrypoint.
The optional feedback used in qualification is a constant saved-data fixture;
its acceptance must never be described as a measured moving response.
"""
import math


class Timeline:
    def __init__(self, gate, length, *, origin_tick=32600):
        self.gate=gate
        self.origin_tick=origin_tick
        self.length=length
        self.cruise=(length-.15)/.1
        assert self.cruise>0
        self.nominal_end=3.+self.cruise
        self.release_tick=None
        self.last_tick=origin_tick-1
        self.last_command_tick=None
        self.request=(0.,0.)
        self.zero_tail_start=None
        self.zero_steps=0
        self.state='GEAR_WAIT'
        self.signed_arc=0.

    def profile(self,phase):
        if phase<=1.:speed=.1*phase
        elif phase<=1.+self.cruise:speed=.1
        elif phase<=self.nominal_end:speed=max(0.,.1-.05*(phase-1.-self.cruise))
        else:speed=0.
        # The original strict twist interface rejects curved subthreshold v.
        # This request-level cutoff is NOT a guarantee about physical braking.
        if speed<.005-1e-12:return 0.,0.
        speed=max(.005,speed)
        return -speed,.5*speed

    def step(self,tick,body,ctrl,encoders):
        assert type(tick) is int and tick==self.last_tick+1,'TIMELINE_NONCONTIGUOUS_TICK'
        self.last_tick=tick
        assert self.state!='DONE','TIMELINE_AFTER_DONE'
        callback=(tick-self.origin_tick)%5==0
        if callback:
            self.last_command_tick=tick
            if self.state=='GEAR_WAIT':self.request=(-.005,.0025)
            elif self.state in ['DRIVE','BRAKE']:
                phase=.05+(tick-self.release_tick)*.01
                self.request=self.profile(phase)
                self.state='DRIVE' if phase<=1.+self.cruise else 'BRAKE'
                if self.request==(0.,0.):
                    self.state='STOP_TAIL';self.zero_tail_start=tick
            else:self.request=(0.,0.)
        v,w,proof=self.gate.select(*self.request,native_tick=tick,body=body,last_ctrl=ctrl,encoders=encoders)
        if self.state=='GEAR_WAIT':
            if proof['released']:
                assert (v,w)==(-.005,.0025) and proof['braking_native']>=200
                self.release_tick=tick;self.state='DRIVE'
            else:assert v==w==0.,'PRE_RELEASE_NONZERO'
        before_arc=self.signed_arc
        # Scalar nominal arc arithmetic only. This is NOT vehicle integration.
        self.signed_arc+=v*.01
        if self.state=='STOP_TAIL':
            assert v==w==0.
            self.zero_steps+=1
            if self.zero_steps>=200 and proof['measured_rest']:self.state='DONE'
        return dict(before_native=tick,source_relative_time_s=(tick-32210)*.01,
            callback=callback,last_command_native_tick=self.last_command_tick,
            state=self.state,release_native=self.release_tick,
            profile_phase_s=None if self.release_tick is None else .05+(tick-self.release_tick)*.01,
            request=list(self.request),admitted=[v,w],gear_proof=proof,
            nominal_arc_before_m=before_arc,nominal_arc_after_m=self.signed_arc,
            zero_tail_native=self.zero_steps)
