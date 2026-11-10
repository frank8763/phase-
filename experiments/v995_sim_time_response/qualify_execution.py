"""Actual new loop seam with no-model clock and step stubs; no sleep allowed."""
import gc,json
from pathlib import Path
from execution import execute
from schedule import controls
R=Path(__file__).resolve().parents[2];O=R/'runs/v995_sim_time_response'
class Clock:
    def __init__(self,mode):self.t=100.;self.cpu=0.;self.mode=mode
    def time(self):return self.t+1794295000.
    def monotonic(self):return self.t
    def thread_time(self):return self.cpu
    def sleep(self,*args):raise AssertionError('OFFLINE_MUST_NOT_SLEEP')
class Vehicle:
    def __init__(self,clock):self.clock=clock;self.count=6083;self.probe_initial_curvature=-.494234;self.commands=[]
    def step(self,*u):
        if self.clock.mode=='native_error'and self.count==6383:raise RuntimeError('INJECTED_NATIVE_ERROR')
        self.commands.append(list(u));self.clock.cpu+=.001;self.clock.t+=.001
        if self.count==6383 and self.clock.mode=='stall':self.clock.t+=.175514589
        if self.count==6282 and self.clock.mode=='deadline':self.clock.t+=300.
        self.count+=1
    def scan(self):
        if self.clock.mode=='scan_error'and self.count==6384:raise OSError('INJECTED_SCAN_ERROR')
    def body(self):return [0.,0.,0.,0.,0.]
if __name__=='__main__':
    task=json.loads((Path(__file__).parent/'TASKS.json').read_text())[0];rows=[];original=gc.isenabled();commands=[]
    for enabled in [True,False]:
        (gc.enable if enabled else gc.disable)()
        for mode in ['healthy','stall','deadline','native_error','scan_error']:
            clock=Clock(mode);v=Vehicle(clock);out=O/f'execution_fixture_{mode}_{enabled}'
            n=execute(v,task,controls,out,1794295300.,clock)
            assert gc.isenabled()==enabled and n['gc_prior_flag_restored']
            if mode in ['healthy','stall']:
                assert n['passed']and n['new_native_count']==800 and not n['real_time_qualified'];commands.append(v.commands)
            elif mode=='deadline':assert n['error']=="AssertionError('ROOT_OR_TASK_MODEL_RESERVE')"and n['new_native_count']==200
            elif mode=='native_error':assert n['new_native_count']is None and n['completed_new_native_lower_bound']==300
            else:assert n['new_native_count']==301 and n['error']=="OSError('INJECTED_SCAN_ERROR')"
            rows.append(dict(mode=mode,initial_gc_enabled=enabled,passed=True,new_mock_count=n['new_native_count']))
    assert all(x==commands[0]for x in commands),'WALLCLOCK_STALL_CHANGED_FIXED_CONTROL_SEQUENCE'
    (gc.enable if original else gc.disable)()
    result=dict(passed=True,models=0,integrations=0,physics_replay=0,cases=rows,wall_stall_preserves_registered_inputs=True,
        offline_sleep_forbidden=True,online_100ms_gate_not_changed=True,physical_equivalence_still_unproven=True)
    (O/'EXECUTION_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
