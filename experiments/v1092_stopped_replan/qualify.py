"""Saved roots, exact production finite prefixes and nominal composition only."""
import sys,json,time,signal,copy,importlib.abc,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1092_stopped_replan'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));sys.path.insert(0,str(C))
import numpy as np,corridor
from recovery_source import forecast_packet
def main():
    assert not(O/'QUALIFICATION.json').exists()
    def halt(*_):raise TimeoutError('BOUNDED120S_QUALIFICATION')
    signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,120);started=time.monotonic();rows=[]
    try:
        for root,path in [(20160,R/'runs/v1090_gear_prefix_reference/QUALIFICATION_INPUT.json'),(26735,R/'runs/v1092_stopped_replan_preparation/ACTUAL_STOPPED_INPUT.json')]:
            x=json.loads(path.read_text());q=corridor.construct(x['setup'],x['packet'],x['source'],O,x['goal']);assert q['proof']['passed']
            moving=q['requests'][abs(q['requests'][:,0])>.005,0];assert len(set(np.sign(moving)))==1
            assert np.array_equal(q['requests'][-2200:],np.zeros((2200,3)))
            checkpoints=[];engine=corridor.live.engine(x['setup'],x['packet'])
            points=sorted(set([125,len(q['requests'])-2200]))
            for i,r in enumerate(q['requests']):
                if i in points:
                    packet=forecast_packet(x['packet'],engine.state,np.r_[engine.adapter.last,engine.adapter.integral],i);packet['speed_episode']=False
                    proof,ss,uu=corridor.proof(x['setup'],packet,x['source'],q['requests'][i:]);assert proof['passed']
                    checkpoints.append(i)
                engine.step(*r)
            rows.append(dict(actual_root=root,proof=q['proof'],rolling_points=checkpoints,static_actions=q['static_actions']))
        answer=dict(passed=True,roots=rows,qualification_scope="saved real roots and rolling finite safety, not complete arrival",
                    whole_route_or_nominal_goal_qualified=False,models=0,integrations=0,wall_s=time.monotonic()-started)
    except BaseException as error:answer=dict(passed=False,roots=rows,error=repr(error),traceback=traceback.format_exc(),models=0,integrations=0,wall_s=time.monotonic()-started)
    signal.setitimer(signal.ITIMER_REAL,0);(O/'QUALIFICATION.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
