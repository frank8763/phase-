"""One unchanged route's normal first command, zero physical models."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('FIRST_STEP_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
import copy,types
def main(slot):
    task=next(t for t in read(C/'TASKS.json')if t['task_id']==f'main_slot{slot:02}')
    raw=R/f'runs/v858_nav2_verified/v1248/t0_slot{slot:02}';p0=read(raw/'RESULT.json')['canonical_initial_packet'];setup=read(raw/'physics/SETUP.json');scan=read(raw/'INITIAL_SENSOR.json');requests=[]
    class FirstStep(BaseException):pass
    class Interface:
        count=0;d=types.SimpleNamespace(time=0.);adapter=types.SimpleNamespace(last=np.asarray(p0['controller_memory']['last_ctrl']),integral=p0['controller_memory']['integral'])
        def body(self):return p0['body']
        def steering_sample(self):return np.asarray(p0['steering']['position']+p0['steering']['velocity'])
        def scan(self):return copy.deepcopy(scan)
        def step(self,*args):requests.append(args);raise FirstStep()
    now=time.time();mono=time.monotonic();w=dict(started_unix=now,absolute_deadline_unix=now+10800,started_monotonic=mono,hard_stop_monotonic=mono+10800,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    out=O/f'PRESTEP_{slot}';out.mkdir();owner=configure_owner(O,time.time()+300,w)
    try:owner.navigate(Interface(),setup,task,time.time()+300,out,{})
    except FirstStep:pass
    else:raise AssertionError('NORMAL_FIRST_STEP_NOT_REACHED')
    assert len(requests)==1 and read(out/'00_STATIC_00_PLAN.json')['passed']
    result=dict(passed=True,slot=slot,request=list(requests[0]),models=0,physical_native=0);dump(O/f'FIRST_STEP_{slot}.json',result);print(json.dumps(result))
if __name__=='__main__':main(int(sys.argv[1]))
