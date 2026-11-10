"""Execute frozen worker AST against mock clock/vehicle, with no physics imports."""
import ast,fcntl,hashlib,json,os,signal,sys,time,traceback,types
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[2];O=R/'runs/v994_diagnostic_timing_postmortem'
SOURCE=R/'experiments/v993_steering_transient_diagnosis/worker.py'
class Clock:
    def __init__(self):self.t=100.
    def time(self):return 1794294300.+self.t-100.
    def monotonic(self):return self.t
    def sleep(self,seconds):self.t+=max(0.,seconds)
class MockVehicle:
    def __init__(self,clock,out,stall):self.clock=clock;self.out=out;self.count=6083;self.probe_initial_curvature=-.494234;self.stall=stall
    def step(self,*args):
        self.clock.t+=.175514589 if self.count==6383 and self.stall else .001
        self.count+=1
    def body(self):return [0.,0.,0.,0.,0.]
    def scan(self):pass
    def finish(self):return dict(actual_native=self.count,fully_recorded_native=self.count)

def run(name,stall):
    clock=Clock();out=R/'runs/v858_nav2_verified/v993'/('v994_mock_'+name)
    assert not out.exists();task=dict(output=str(out),maximum_new_native=800,task_wall_limit_s=300,origin_native_tick=6083)
    path=O/(name+'.TASK.json');path.write_text(json.dumps(task))
    fake=types.ModuleType('physical')
    def create(path,task,guard,progress,callback):
        path.mkdir(parents=True);v=MockVehicle(clock,out,stall);callback(v);return v
    fake.create_vehicle=create;fake.replay=lambda v,*args:dict(replay_native=v.count,passed=True)
    tree=ast.parse(SOURCE.read_text());nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef)]
    namespace=dict(Path=Path,R=R,C=SOURCE.parent,fcntl=fcntl,json=json,os=os,signal=signal,sys=sys,time=clock,traceback=traceback,np=np,
                   authorized=lambda task:1794312000.,controls=lambda *args:(0.,0.,False))
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(SOURCE),'exec'),namespace)
    prior=sys.modules.get('physical');argv=sys.argv;affinity=os.sched_getaffinity(0);term=signal.getsignal(signal.SIGTERM);alarm=signal.getsignal(signal.SIGALRM)
    try:
        sys.modules['physical']=fake;sys.argv=[str(SOURCE),str(path)];rc=namespace['main']()
    finally:
        sys.argv=argv;os.sched_setaffinity(0,affinity);signal.signal(signal.SIGTERM,term);signal.signal(signal.SIGALRM,alarm)
        if prior is None:sys.modules.pop('physical',None)
        else:sys.modules['physical']=prior
    result=json.loads((out/'RESULT.json').read_text());result['exit_code']=rc;return result

if __name__=='__main__':
    healthy=run('healthy',False);red=run('observed_gap_injected',True)
    assert healthy['passed']and healthy['new_actual_native']==800 and healthy['replay_native']==6883
    assert red['error']=="AssertionError('NATIVE_WALL_LAG')"and red['new_actual_native']==301 and red['replay_native']==0
    assert 'maximum_wall_lag_s'not in red,'Expected actual frozen-worker failure metadata omission'
    result=dict(passed=True,models=0,integrations=0,physical_replay=0,
        frozen_worker_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        fixed_stall_reproduces_same_assertion_and_exact_completed_count=True,
        red_error=red['error'],red_new_actual_mock_count=301,healthy_mock_count=800,
        exposes_missing_failure_lag_value=True,unique_physical_stall_cause_identified=False,
        test_injection_is_not_a_measurement_of_original_failure=True)
    (O/'FROZEN_FAILURE_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
