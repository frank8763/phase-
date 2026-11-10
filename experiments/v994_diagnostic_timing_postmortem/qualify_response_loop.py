"""Deterministic timing faults at the actual proposed loop seam, zero models."""
import gc,json
from pathlib import Path
from response_loop import run_fixed_response

R=Path(__file__).resolve().parents[2];O=R/'runs/v994_diagnostic_timing_postmortem'
class Clock:
    def __init__(self,mode):self.t=100.;self.calls=0;self.mode=mode
    def monotonic(self):return self.t
    def thread_time(self):return self.t
    def time(self):return 1794294300.+self.t-100.
    def sleep(self,delay):
        self.t+=delay
        if self.mode=='scheduler'and self.calls==301:self.t+=.175
        self.calls+=1
class Vehicle:
    def __init__(self,clock):self.clock=clock;self.count=6083;self.probe_initial_curvature=-.494234
    def step(self,*args):
        if self.clock.mode=='native_exception'and self.count==6383:raise RuntimeError('INJECTED_NATIVE_EXCEPTION')
        self.clock.t+=.175 if self.clock.mode=='native'and self.count==6383 else .001
        if self.clock.mode=='deadline'and self.count==6282:self.clock.t+=300.
        self.count+=1
    def scan(self):
        if self.clock.mode=='scan'and self.count==6384:self.clock.t+=.175
    def body(self):return [0.,0.,0.,0.,0.]

if __name__=='__main__':
    cases=[];before=gc.isenabled()
    for prior_enabled in [True,False]:
        (gc.enable if prior_enabled else gc.disable)()
        for mode in ['healthy','native','scan','partial','scheduler','deadline','partial_exception','native_exception']:
            clock=Clock(mode);v=Vehicle(clock)
            def partial(data):
                if data['new_actual_native']==301:
                    if mode=='partial':clock.t+=.175
                    if mode=='partial_exception':raise OSError('INJECTED_PARTIAL_WRITE_ERROR')
            out=O/('seam_'+mode+'_'+str(prior_enabled))
            result=run_fixed_response(v,dict(maximum_new_native=800),lambda *args:(0.,0.,False),out,1794294600.,clock,partial)
            assert result['gc_prior_flag_restored']and gc.isenabled()==prior_enabled
            if mode=='healthy':assert result['passed']and result['new_native_count']==800
            elif mode in ['native','scan','partial','scheduler']:
                assert result['error']=="AssertionError('NATIVE_WALL_LAG')"and result['new_native_count']==301
                assert result['overrun']['lag_s']>.1 and result['maximum_wall_lag_s']>.1
                assert result['overrun']['native_tick_completed']==6384
            elif mode=='deadline':assert result['error']=="AssertionError('ROOT_OR_TASK_MODEL_RESERVE')"and result['new_native_count']==200
            elif mode=='partial_exception':assert result['error']=="OSError('INJECTED_PARTIAL_WRITE_ERROR')"and result['new_native_count']==301
            else:assert result['error']=="RuntimeError('INJECTED_NATIVE_EXCEPTION')"and result['new_native_count']is None and result['completed_new_native_lower_bound']==300
            cases.append(dict(mode=mode,prior_gc_enabled=prior_enabled,expected_verdict_observed=True,
                              count=result['new_native_count'],error=result['error'],actual_lag_recorded=result['overrun']))
    (gc.enable if before else gc.disable)()
    receipt=dict(passed=True,models=0,integrations=0,physical_replay=0,cases=cases,
        gc_flag_restored=True,original_100ms_gate_unchanged=True,actual_frozen_worker_unchanged=True,
        physical_cause_unresolved=True,physical_authority=False)
    (O/'RESPONSE_LOOP_QUALIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(passed=True,nonphysical_fault_cases=len(cases),models=0,integrations=0,physical_authority=False)))
