"""Build the next causal input from the completed actual stop, zero physics."""
import sys,json,copy,math,gzip,importlib.abc,time,signal,traceback
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];O=R/'runs/v1092_stopped_replan_preparation'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));sys.path.insert(0,str(R/'experiments/v1090_active_corridor'))
import numpy as np,corridor
from kernel import load,PARAMETERS
from prediction import Predictor,initial
from braking_reserve import signed
def main():
    def halt(*_):raise TimeoutError('120_SECOND_STOPPED_INPUT_PROBE')
    signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,120)
    started=time.monotonic();O.mkdir(exist_ok=True);assert not(O/'PROBE.json').exists()
    try:
        P=R/'runs/v858_nav2_verified/v1091/exit_saved_we'
        assert json.loads((R/'runs/v1091_certified_exit/FINALIZED.json').read_text())['passed']
        x=json.loads((P/'ACTUAL_EXIT_INPUT.json').read_text());setup=x['setup'];packet=copy.deepcopy(x['packet'])
        commands=np.array(json.loads((P/'physics/BODY_COMMANDS.json').read_text()))
        meta=json.loads((R/'runs/v858_nav2_verified/v1090/main_west_east/INITIAL_METADATA.json').read_text())
        engine=Predictor(setup,initial(meta['packet']),PARAMETERS);engine.adapter.__class__=signed.Adapter;engine.adapter.last=np.zeros(4);engine.adapter.integral=0.
        with np.load(P/'physics/NATIVE_TRACE.npz')as trace:
            controls=trace['ctrl'][:,setup['actuator_ids']];q=trace['qpos'][-1];v=trace['qvel'][-1];t=float(trace['time'][-1])
        error=0.
        for r,u in zip(commands,controls):error=max(error,float(abs(engine.adapter.compute(*r[[1,2,3,4,5]])-u).max()))
        assert error<=1e-8
        angle=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
        packet.update(body=[float(q[0]),float(q[1]),angle,float(v[0]*math.cos(angle)+v[1]*math.sin(angle)),float(v[5])],native_tick=len(commands),sim_time=t,speed_episode=False)
        packet['steering'].update(position=q[setup['steering_qpos_addresses']].tolist(),velocity=v[setup['steering_qvel_addresses']].tolist(),native_tick=len(commands))
        packet['controller_memory'].update(last_ctrl=engine.adapter.last.tolist(),integral=float(engine.adapter.integral))
        causal=load('stopped_actual_evidence',R/'experiments/v1024_full_route_execution/causal.py');evidence=causal.Evidence(setup['known']);last=None;duplicates=0
        with gzip.open(P/'physics/SENSORS.json.gz','rt')as file:
            for row in json.load(file):
                scan={k:row[k]for k in ['native_tick','time','xy','yaw','ranges']}
                if last is not None and scan['native_tick']==last['native_tick']:
                    assert scan==last,'DUPLICATE_PUBLIC_SCAN_DIFFERED';duplicates+=1;continue
                evidence.update(scan);last=scan
        source=evidence.source(SimpleNamespace(d=SimpleNamespace(time=t)))
        inp=dict(setup=setup,packet=packet,source=source,goal=setup['case']['goal_xy'],control_reconstruction_error=error,identical_duplicate_scans=duplicates)
        (O/'ACTUAL_STOPPED_INPUT.json').write_text(json.dumps(inp,indent=2)+'\n')
        try:
            proposal=corridor.live.produce(setup,packet,source,O,inp['goal']);answer=dict(complete_goal_proposal=True,proof=proposal['proof'])
        except AssertionError as rejection:
            answer=dict(complete_goal_proposal=False,rejection=str(rejection))
            try:
                proposal=corridor.construct(setup,packet,source,O,inp['goal'])
                answer.update(finite_corridor=True,proof=proposal['proof'],candidates=proposal['candidates'])
                np.savez_compressed(O/'PROPOSAL.npz',requests=proposal['requests'],states=proposal['states'],controls=proposal['controls'])
            except AssertionError as error:answer.update(finite_corridor=False,error=repr(error))
        answer.update(actual_root_native=26735,identical_duplicate_scans=duplicates)
    except BaseException as error:answer=dict(error=repr(error),traceback=traceback.format_exc(),preparation_failed=True)
    signal.setitimer(signal.ITIMER_REAL,0);answer.update(wall_s=time.monotonic()-started,models=0,integrations=0)
    (O/'PROBE.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
