"""Analytical interface qualification of the actual goal-phase entry."""
import copy
import fcntl
import importlib.abc
import json
from pathlib import Path
import signal
import sys
import time
import traceback


class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:
            raise AssertionError('SOFTWARE_ONLY '+name)


sys.meta_path.insert(0,NoModels())
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1203_goal_entry_handoff'
sys.path.insert(0,str(C))
import goal_entry
from goal_entry import q,np
from entry_gates import read_case

CASES=[('C1','v1195','recovery_main_slot01','nominal'),
       ('A2','v1191','recovery_main_slot02','nominal'),
       ('B1','v1194','recovery_main_slot01','nominal'),
       ('P1','v1189','recovery_main_slot01','nominal'),
       ('C1','v1195','recovery_main_slot01','yaw_plus'),
       ('B1','v1194','recovery_main_slot01','x_minus'),
       ('B1','v1194','recovery_main_slot01','y_plus'),
       ('P1','v1189','recovery_main_slot01','x_plus')]


class AnalyticalInterface:
    """No physical state, vehicle factory, scan evidence or model initialization."""
    def __init__(self,x):
        self.x=copy.deepcopy(x);self.count=x['packet']['native_tick'];self.begin=self.count
        self._live_load=False
        origin=dict(q.initial(x['packet']),steering_load_episode=False)
        self.predictor=q.model.Predictor(x['setup'],origin)
        self.adapter=self.predictor.adapter;self.adapter.parked_target=None
        self.scans=0

    def step(self,v,w,stale):
        assert stale is False
        self.predictor.step(float(v),float(w),False);self.count+=1

    def scan(self):
        self.scans+=1
        return dict(analytical_interface_only=True,no_generated_sensor_evidence=True)

    def packet(self):
        p=copy.deepcopy(self.x['packet']);s=self.predictor.state
        p['native_tick']=self.count
        p['sim_time']=self.x['packet']['sim_time']+.01*(self.count-self.begin)
        p['body']=[float(s[0]),float(s[1]),float(s[2]),float(s[3]),float(s[5])]
        p['body_lateral']=float(s[4])
        # Inverse Ackermann observation of this analytical virtual steering.
        t=np.tan(s[6]);d=np.array([1.-.45*t,1.+.45*t])
        p['steering'].update(position=np.arctan2(t,d).tolist(),
            velocity=((1.+t*t)/(d*d+t*t)*s[7]).tolist(),native_tick=self.count)
        p['controller_memory']=dict(last_ctrl=self.adapter.last.tolist(),integral=float(self.adapter.integral))
        p['coupled_episode']=False;p['steering_motion_active']=False
        return p


def negative_entries(x,table):
    cases=[]
    def reject(name,mutate_packet=None,mutate_input=None,mode=False,expired=False):
        v=AnalyticalInterface(x);one=copy.deepcopy(x);p=v.packet()
        if mutate_packet:mutate_packet(p)
        if mutate_input:mutate_input(one)
        if mode:v._live_load=None
        out=O/('NEGATIVE_'+name);out.mkdir()
        try:
            goal_entry.execute(v,one['setup'],one,table,time.monotonic()-1 if expired else time.monotonic()+10,
                lambda:True,lambda _:p,lambda _:None,out)
        except AssertionError as exc:
            assert v.count==v.begin,'NEGATIVE_ENTRY_TOOK_A_STEP'
            cases.append(dict(case=name,rejected=True,reason=str(exc),analytical_native=0))
        else:raise AssertionError('BAD_ENTRY_ACCEPTED '+name)
    reject('clock',lambda p:p.update(sim_time=p['sim_time']+.01))
    reject('stale_position',lambda p:p['body'].__setitem__(0,p['body'][0]+.01))
    reject('lateral_state',lambda p:p.update(body_lateral=p['body_lateral']+.001))
    reject('steering_state',lambda p:p['steering']['position'].__setitem__(0,p['steering']['position'][0]+.01))
    reject('last_ctrl',lambda p:p['controller_memory']['last_ctrl'].__setitem__(0,p['controller_memory']['last_ctrl'][0]+.001))
    reject('integral',lambda p:p['controller_memory'].update(integral=p['controller_memory']['integral']+.001))
    reject('coupled_mode',lambda p:p.update(coupled_episode=True))
    reject('active_mode',lambda p:p.update(steering_motion_active=True))
    reject('missing_load',mode=True)
    reject('future_source',mutate_input=lambda one:one['source'].update(source_native_tick=one['packet']['native_tick']+1))
    reject('expired_valid',expired=True)
    expired=json.loads((O/'NEGATIVE_expired_valid/INITIAL_SELECTION.json').read_text())
    assert not expired['passed'] and expired['analytical_cpp_native']==0
    q.dump(O/'ENTRY_NEGATIVES.json',dict(passed=True,cases=cases,models=0,new_mujoco_native=0))
    return cases


def readback(x,result,trace):
    engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients'])
    origin=dict(q.initial(x['packet']),steering_load_episode=False)
    ss,uu,mm=engine.simulate(origin,[q.accelerator.row(float(v),float(w))for v,w,_ in trace['requests']])
    error=max(float(abs(ss-trace['states']).max()),float(abs(uu-trace['controls']).max()),
              float(abs(mm-trace['memory']).max()))
    assert error<=1e-8,'INDEPENDENT_FULL_ENTRY_REQUEST_REPLAY'
    for generation in result['generations']:
        k=generation['offset'];o=generation['origin']
        assert max(float(abs(np.asarray(o['state'])-trace['states'][k]).max()),
                   float(abs(np.asarray(o['last_ctrl'])-trace['memory'][k,:4]).max()),
                   abs(o['integral']-trace['memory'][k,4]))<=1e-8,'GENERATION_ORIGIN_NOT_CURRENT'
        if k:assert o['steering_load_episode']is True,'HANDOFF_RESET_LOAD_MEMORY'
    return dict(passed=True,independent_error=error,analytical_cpp_native=engine.native,
                generation_origins_bound_to_executed_state=True,
                handoff_load_memory_preserved=True)


def main():
    assert not O.exists(),'NO_OVERWRITE_OR_RETRY'
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert q.sha(R/'REVIEW_PENDING')==q.GUARD
    O.mkdir()
    # Import the actual new call site without constructing its physical owner.
    import live_chain
    assert live_chain.goal_entry is goal_entry
    loaded=[];frozen={}
    for label,version,task,case in CASES:
        root,x,table=read_case(version,task)
        _,dx,dy,yaw=next(c for c in q.CASES if c[0]==case)
        one=copy.deepcopy(x);one['packet']['body'][0]+=dx;one['packet']['body'][1]+=dy;one['packet']['body'][2]+=yaw
        loaded.append((label+'_'+case,one,table))
        for p in [root/'LIVE_GOAL_INPUT.json',root/'LIVE_GOAL_TABLE.npz']:
            frozen[str(p.relative_to(R))]=q.sha(p)
    for module in list(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name and Path(name).resolve().is_relative_to(R) and Path(name).suffix=='.py':
            p=Path(name).resolve();frozen[str(p.relative_to(R))]=q.sha(p)
    for p in [*C.glob('*.py'),C/'PROTOCOL.md',R/'experiments/v1159_bounded_steering_load/PARAMETERS.json',R/'runs/v1159_bounded_steering_load/profile.so']:
        frozen[str(p.relative_to(R))]=q.sha(p)
    q.dump(C/'SOURCE_FREEZE.json',dict(files=frozen,cases=CASES,models_authorized=False))
    started=time.monotonic();deadline=started+360
    q.dump(O/'ROUND_WINDOW.json',dict(software_only=True,models_authorized=False,started_unix=time.time(),hard_stop_monotonic=deadline,wall_cap_s=360))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SOFTWARE_ENTRY360')))
    signal.setitimer(signal.ITIMER_REAL,360)
    results=[];negatives=[];error=None
    try:
        negatives=negative_entries(loaded[0][1],loaded[0][2])
        for name,x,table in loaded:
            out=O/name;out.mkdir();q.dump(out/'INPUT.json',x)
            v=AnalyticalInterface(x)
            answer=goal_entry.execute(v,x['setup'],x,table,min(deadline-10,time.monotonic()+50),
                lambda:time.monotonic()<deadline-10,lambda owner:owner.packet(),
                lambda p:q.dump(O/'PROGRESS.json',dict(case=name,**p)),out)
            audit=readback(x,answer,v._goal_trace);q.dump(out/'READBACK.json',audit)
            results.append(dict(case=name,passed=True,native=answer['native'],
                raw_m=answer['proof']['minimum_raw_m'],generations=len(answer['generations']),
                scheduled_stops=len(answer['scheduled_stops']),
                generation_and_stop_cpp_native=answer['analytical_cpp_native'],
                replay_cpp_native=audit['analytical_cpp_native'],
                interface_python_native=v.count-v.begin,shadow_python_native=answer['analytical_shadow_python_native'],
                independent_error=audit['independent_error']))
            q.dump(O/'RESULTS.json',results)
    except BaseException as exc:
        error=dict(error=repr(exc),traceback=traceback.format_exc(),partial_work='unknown; completed evidence retained')
        q.dump(O/'ERROR.json',error)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        result=dict(closed=True,passed=len(results)==8 and error is None,
            cases=results,negative_entries=len(negatives),error=error,wall_s=time.monotonic()-started,
            source_unchanged=all(q.sha(R/p)==h for p,h in frozen.items()),
            guard_original=q.sha(R/'REVIEW_PENDING')==q.GUARD,
            models=0,new_mujoco_native=0,physical_eligible=False,
            scope='same entry with analytical interface; full native audit and isolated worker still pending')
        q.dump(O/'COMPLETION.json',result);print(json.dumps(result))


if __name__=='__main__':main()
