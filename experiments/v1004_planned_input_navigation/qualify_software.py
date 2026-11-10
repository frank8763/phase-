"""Production supervisor/ingress handoff using an explicitly nonphysical peer."""
import ast,copy,importlib.abc,importlib.util,json,math,sys,time
from pathlib import Path
from types import SimpleNamespace as S
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1004_planned_input_navigation'
sys.path[:0]=[str(C),str(R/'experiments/v1003_causal_recovery_execution')]
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','rclpy','physical','vehicle'}:raise AssertionError('NO_MODEL_SOFTWARE_QUALIFICATION '+name)
sys.meta_path.insert(0,NoModel())
from predictor import fixture,law,virtual,virtual_rate
import native_contract as native
import supervise as supervisor
from authority import read
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
class Future:
    def __init__(self,value=None,done=True):self.value=value;self.is_done=done
    def done(self):return self.is_done
    def result(self):return self.value
class Handle:
    def __init__(self,complete):self.accepted=True;self.future=Future(S(status=4,result=S(error_code=0)),complete)
    def get_result_async(self):return self.future
    def cancel_goal_async(self):self.future.value=S(status=5);self.future.is_done=True;return Future()
class Action:
    def __init__(self):self.count=0
    def send_goal_async(self,g):self.count+=1;return Future(Handle(self.count>1))
class Watchdog:
    def __init__(self,*a):self.sent=False
    def poll(self,*args):
        if self.sent:return None
        self.sent=True;return dict(reason='FIXED_SAVED_REFERENCE_LOSS')
class Vehicle:
    def __init__(self,packet,initial,setup):
        self.count=packet['native_tick'];self.initial_packet=copy.deepcopy(packet);self.state=np.array(initial['state']);self.origin=self.count
        self.adapter=fixture.make(law.base.Adapter,setup);self.adapter.last=np.array(initial['last_ctrl']);self.adapter.integral=initial['integral'];self.session=None
    def body(self):return [*self.state[:4],self.state[5]]
    def steering_sample(self):return np.r_[law.steering(math.tan(self.state[6])/.6,.6,.27),[0.,0.]]
    def step(self,v,w,stale=False):
        self.adapter.compute(v,w,self.state[3],self.state[5],stale);self.count+=1
        if self.session.profile is not None and self.session.phase=='RUNNING':self.state=np.array(self.session.profile['plan']['state_path'][self.session.profile_index+1])
    def packet(self):
        p=copy.deepcopy(self.initial_packet);p.update(body=self.body(),native_tick=self.count,body_measured_at=time.monotonic(),sent_at=time.monotonic())
        enc=self.steering_sample();p['steering']=dict(native_tick=self.count,measured_at=p['body_measured_at'],position=enc[:2].tolist(),velocity=enc[2:].tolist())
        p['controller_memory']=dict(last_ctrl=self.adapter.last.tolist(),integral=self.adapter.integral);p['profile_status']=copy.deepcopy(self.profile_status)
        return p
def metadata_switch(v,cls):
    assert abs(np.array(v.body()[3:])).max()<=.03 and abs(v.adapter.last[2:]).max()<=1e-10
    old=v.adapter;new=fixture.make(cls,setup);new.last=old.last.copy();new.integral=old.integral;new.virtual_rate=.6;v.adapter=new
    return dict(native_tick=v.count,adapter='V993'if cls is law.Adapter else'V958',last_ctrl=new.last.tolist(),integral=new.integral,physical_state_unchanged=True)
def require(test,message):
    if not test:raise AssertionError(message)
def spin(node,timeout_sec):
    node.session.step(node.vehicle,time.monotonic());node.latest=node.vehicle.packet()
def wait(node,done,until,message):
    while not done():spin(node,.005);require(time.monotonic()<until,message)
def flow(index):
    original=read(R/'experiments/v1003_causal_recovery_execution'/('PLAN_'+str(index)+'.json'));packet=saved['rows'][index]['search_packet'];source=copy.deepcopy(saved['rows'][index]['search_source'])
    folder=O/('software_state_'+str(index));folder.mkdir(exist_ok=False);(folder/'physics').mkdir();dump(folder/'physics/SETUP.json',setup)
    v=Vehicle(packet,original['plan']['initial'],setup);session=native.Startup('software-'+str(index));session.bind_vehicle(v,folder);v.session=session;session.phase='RUNNING';session.armed_at=time.monotonic()
    node=S(vehicle=v,session=session,latest=v.packet(),guard_failure=None,profile_owner=False,retained_proof=None,supervision_events=[],tube_decisions=[])
    node.forward=S(replan_requested=False,replan_count=0,resume=lambda goal:None)
    node.planner_proxy=S(known=known,rows=[]);node.action=Action()
    def snapshot():
        p=v.packet();node.latest=p;s=copy.deepcopy(source);s['body_native_tick']=p['native_tick'];s['source_age_s']=.01;return p,s
    node.motion=S(out=folder,decision_snapshot=snapshot)
    node.get_clock=lambda:S(now=lambda:S(to_msg=lambda:None))
    def send(p):session.receive(dict(p,run_id=session.run_id),time.monotonic(),v.count,float(v.count*.01));node.latest=v.packet()
    node.send=send
    goal=S(pose=S(header=S(stamp=None),pose=S(position=S(x=4.,y=-2.))))
    response,rows=supervisor.supervise(node,goal,time.monotonic()+60.,time.time()+120.,spin,wait,require,lambda:None)
    assert response.status==4 and len(rows)==1 and rows[0]['passed']and not node.profile_owner
    assert node.action.count==2 and len(session.switches)==2 and session.profiles[0]['completed']and session.vehicle.profile_status['released_id']==1
    assert all(x['owner']=='COMMITTED_RECOVERY'for x in session.execution if x.get('profile_id')==1 and x.get('profile_index',10**9)<len(original['plan']['planned_body_requests']))
    session.save(folder);dump(folder/'INGRESS.json',dict(receipts=session.receipts,execution=session.execution))
    return dict(state=index,passed=True,normal_actions=2,completed_profiles=1,exact_native_profile_inputs=len(session.profile['plan']['planned_body_requests'])if session.profile is not None else session.profile_index,models=0,physical_integrations=0,peer_is_nonphysical=True)
if __name__=='__main__':
    for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    setup=read(R/'runs/v1003_causal_recovery_execution/prior_v974/physics/SETUP.json');known=read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json');saved=read(R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json')
    prior_switch=native.switch;prior_watchdog=supervisor.ReferenceWatchdog;native.switch=metadata_switch;supervisor.ReferenceWatchdog=Watchdog
    try:rows=[flow(0),flow(1)]
    finally:native.switch=prior_switch;supervisor.ReferenceWatchdog=prior_watchdog
    result=dict(passed=all(x['passed']for x in rows),rows=rows,models=0,physical_integrations=0,real_nav2_servers_started=False,
        scope='Production supervisor and native owner protocol with nonphysical exact-reference peer; not a new vehicle or Nav2 arrival test')
    dump(O/'SOFTWARE_QUALIFICATION.json',result);print(json.dumps(result))
