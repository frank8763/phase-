"""Real normal-navigation first-command qualification inside run_phase only."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('FIRST_COMMAND_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
import copy,types
def main():
    # The orchestrator owns the Phase lock for this controlled child.
    prior=R/'runs/v858_nav2_verified/v1248/t0_slot17';p0=read(prior/'RESULT.json')['canonical_initial_packet'];setup=read(prior/'physics/SETUP.json');scan=read(prior/'INITIAL_SENSOR.json');requests=[]
    class FirstStep(BaseException):pass
    class Interface:
        count=0;d=types.SimpleNamespace(time=0.);adapter=types.SimpleNamespace(last=np.asarray(p0['controller_memory']['last_ctrl']),integral=p0['controller_memory']['integral'])
        def body(self):return p0['body']
        def steering_sample(self):return np.asarray(p0['steering']['position']+p0['steering']['velocity'])
        def scan(self):return copy.deepcopy(scan)
        def step(self,*args):requests.append(args);raise FirstStep()
    now=time.time();mono=time.monotonic();w=dict(started_unix=now,absolute_deadline_unix=now+5400,started_monotonic=mono,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    out=O/'PRESTEP';out.mkdir();owner=configure_owner(O,time.time()+300,w);task=read(C/'TASKS.json')[0]
    try:owner.navigate(Interface(),setup,task,time.time()+300,out,{})
    except FirstStep:pass
    else:raise AssertionError('NORMAL_FIRST_COMMAND_NOT_REACHED')
    assert len(requests)==1 and read(out/'00_STATIC_00_PLAN.json')['passed']
    result=dict(passed=True,request=list(requests[0]),models=0,physical_native=0,actual_normal_call_site=True,stopped_before_first_step=True)
    dump(O/'NORMAL_FIRST_COMMAND_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()
