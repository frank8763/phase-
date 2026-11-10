"""Actual restore loop/progress/STOP seam on labeled array counters, no models."""
import importlib.abc,importlib.util,json,sys,time
from pathlib import Path
from types import SimpleNamespace as S
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v991_coordinated_components'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
spec=importlib.util.spec_from_file_location('v991_actual_restore_loop',C/'physical.py');physical=importlib.util.module_from_spec(spec);spec.loader.exec_module(physical)
from budget import create
from startup_progress import Progress
def exercise(label,step_delay=.01,stop_at=None,tamper=False):
    folder=O/('restore_'+label);folder.mkdir();epoch=time.time()
    class Clock:
        elapsed=0.
        def time(self):return epoch+self.elapsed
        def monotonic(self):return self.elapsed
    clock=Clock();origin=601;task=dict(run_id=label,origin_native_tick=origin,wall_limit_s=40.,brake_s=2.)
    record=create(task,epoch+5000,epoch,0.);progress=Progress(folder,task,record,clock)
    names=['qpos','qvel','ctrl','mocap_pos','mocap_quat'];expected={k:np.zeros((origin,4))for k in names}
    if tamper:expected['qpos'][3,0]=1e-6
    calls=[];scans=[]
    class Peer:
        count=0
        d=S(time=0.,**{n:np.zeros(4)for n in names})
        def scan(self):scans.append(self.count)
        def step(self,v,w,stale):
            calls.append((v,w,stale));self.count+=1;self.d.time=self.count*.01;clock.elapsed+=step_delay
            if self.count==stop_at:(folder/'PARENT_STOP_REQUEST.json').write_text(json.dumps(dict(run_id=label,reason='FIXTURE')))
    peer=Peer();commands=[[0.,.01,.002,0.,0.,False]for _ in range(origin)]
    try:answer=progress.stage('HISTORICAL_RESTORE',lambda:physical.restore_prefix(peer,task,expected,commands,epoch+350.,progress));error=None
    except (AssertionError,InterruptedError)as e:answer=None;error=str(e)
    if label=='complete':
        assert answer['passed']and peer.count==origin and calls==[(.01,.002,False)]*origin
        assert scans==[0]+list(range(1,origin+1,5));assert json.loads((folder/'STARTUP_PROGRESS.json').read_text())['native_tick']==origin
    elif stop_at is not None:assert peer.count==stop_at and error=='PARENT_STOP_DURING_CANONICAL_RESTORE'
    elif tamper:assert peer.count==4 and error=='HISTORICAL_PREFIX_STATE_OR_CONTROL_MISMATCH'
    else:assert clock.elapsed>=180. and clock.elapsed<=180.5 and error=='CANONICAL_STATE_RESTORE_TIMEOUT'
    assert all(np.array_equal(getattr(peer.d,n),np.zeros(4))for n in names)
    return dict(case=label,passed=True,counter_steps=peer.count,error=error,models=0,integrations=0,arrays_are_not_a_vehicle=True)
def main():
    cases=[exercise('complete'),exercise('stop',stop_at=8),exercise('mismatched_state',tamper=True),exercise('deadline',step_delay=.5)]
    result=dict(passed=True,cases=cases,models=0,integrations=0,actual_restore_function_executed=True,physical_history_not_executed=True)
    (O/'RESTORE_CONTROL_FLOW_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
