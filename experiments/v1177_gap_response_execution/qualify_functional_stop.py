"""Production functional stop at a sensor boundary; saved data only."""
from gap_tools import *
import math,types,importlib.abc
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('NO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
import gap_execution as ex
def main():
    fixture=read(R/'experiments/v1139_afternoon_observer/STATIC_T0_SOURCE_FIXTURE.json');setup=fixture['setup'];plan=plan_for(read(C/'TASK_rate_main.json'))
    class Vehicle:
        def __init__(self):
            self.count=0;self.adapter=q.model.Predictor(setup,dict(q.initial(fixture['packet']),steering_load_episode=False)).adapter;self.d=types.SimpleNamespace(qvel=np.zeros(19),time=0.);self.sensor_ticks=[0,0]
        def body(self):
            b=list(fixture['packet']['body']);b[0]+=.05 if self.count>=5 else 0.;return b
        def steering_sample(self):return np.zeros(4)
        def scan(self):self.sensor_ticks.append(self.count)
        def step(self,v,w,stale):
            assert v==w==0. and not stale;self.adapter.compute(v,w,0.,0.,False);self.count+=1;self.d.time=.01*self.count
    v=Vehicle();certs=[]
    def cert(p):certs.append(p['native_tick']);return dict(passed=True,synthetic_only=True)
    r=ex.run_component(v,plan,cert,lambda *_:True,lambda *_:None)
    assert not r['passed']and r['functional_failure']['native']==5 and v.count==2205
    assert len(v._gap_journal)==2205 and all(z['applied']for z in v._gap_journal)
    assert all(z['phase']=='functional_stop'and z['request']==[0.,0.,False]for z in v._gap_journal[-2200:])
    assert v.sensor_ticks==[0,0]+list(range(0,2206,5)),'REFUSAL_BOUNDARY_SENSOR_MISSING'
    assert 5 in certs and set(range(0,2205,8)).issubset(certs)
    dump(O/'FUNCTIONAL_STOP_QUALIFICATION.json',dict(passed=True,functional_refusal_native=5,complete_stop_native=2200,production_substitute_calls=2205,boundary_sensor_saved=True,models=0,physical_native=0,new_state_prediction=0))
    print('FUNCTIONAL_STOP_RECORDING_PASS')
if __name__=='__main__':main()
