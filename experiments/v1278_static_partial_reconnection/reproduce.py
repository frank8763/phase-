"""Execute the actual navigation function against immutable recorded interfaces.

No new dynamics: every step checks the original applied request and reads its
saved next state. Planning and reserve returns are the recorded call results.
The red/green seam is the *next* renewal call after the completed partial path.
"""
from pathlib import Path
import ast,copy,importlib.util,json,math,sys,time,types
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
P=R/'runs/v858_nav2_verified/v1275/main_slot24'
def read(p):return json.loads(Path(p).read_text())
class NextRenewal(BaseException):pass
def run(path):
    setup=read(P/'physics/SETUP.json');p0=read(P/'CANONICAL_INITIAL_PACKET.json');endpacket=read(P/'ACTUAL_FINAL_PACKET.json')
    plans=[read(P/n)for n in ['00_STATIC_00_PLAN.json','01_PREEMPTIVE_STOP_00_PLAN.json','02_STATIC_01_PLAN.json']]
    commands=np.asarray(read(P/'physics/BODY_COMMANDS.json'))
    with np.load(P/'physics/NATIVE_TRACE.npz')as z:tr={k:z[k].copy()for k in z.files}
    class Vehicle:
        count=0;d=types.SimpleNamespace(time=0.);adapter=types.SimpleNamespace(last=np.asarray(p0['controller_memory']['last_ctrl']),integral=0.)
        def body(self):
            if self.count==0:return p0['body']
            qp=tr['qpos'][self.count-1];qv=tr['qvel'][self.count-1];yaw=math.atan2(2*(qp[3]*qp[6]+qp[4]*qp[5]),1-2*(qp[5]**2+qp[6]**2))
            return [*qp[:2],yaw,qv[0]*math.cos(yaw)+qv[1]*math.sin(yaw),qv[5]]
        def steering_sample(self):
            if self.count==0:return np.asarray(p0['steering']['position']+p0['steering']['velocity'])
            return np.r_[tr['qpos'][self.count-1,setup['steering_qpos_addresses']],tr['qvel'][self.count-1,setup['steering_qvel_addresses']]]
        def scan(self):return dict(native_tick=self.count)
        def step(self,*request):
            assert np.array_equal(np.asarray(request,float),commands[self.count,[1,2,5]]),'SAVED_REQUEST_DIVERGED'
            self.count+=1;self.d.time=self.count*.01;self.adapter.last=tr['ctrl'][self.count-1,setup['actuator_ids']]
    v=Vehicle()
    class Evidence:
        first=None
        def __init__(self,*_):pass
        def update(self,*_):return False  # recorded original detector never discovered
    def packet(v,*_):
        if v.count==16930:return copy.deepcopy(endpacket)
        return dict(body=v.body(),native_tick=v.count,controller_memory=dict(last_ctrl=v.adapter.last.tolist(),integral=0.))
    causal=types.SimpleNamespace(Evidence=Evidence,packet=packet)
    norm=types.SimpleNamespace(PeriodicSupport=lambda:None)
    class Reserve:
        def __init__(self,*args,**kw):pass
        def check(self,p,rr):
            if v.count==11680:return read(P/'BRAKE_PREEMPTIONS.json')[0]['proof']
            return dict(passed=True,current_stop_passed=True)
    def finite(setup,p,source,requests,label):return copy.deepcopy(plans[0 if label=='ORIGINAL_COMPLETE_STATIC_GUIDANCE'else 1])
    calls=[]
    def renew(*args,**kwargs):
        calls.append(v.count)
        if v.count==13880:return copy.deepcopy(plans[2])
        assert v.count==16930,'UNEXPECTED_RENEWAL_STATE'
        raise NextRenewal()
    def virtual(a):
        z=np.tan(a);return float(math.atan(.6*(z[0]/(.6+.27*z[0])+z[1]/(.6-.27*z[1]))/2))
    fakekernel=types.ModuleType('kernel');fakekernel.O=R/'runs/v1275_time_window_fixed24';previous=sys.modules.get('kernel');sys.modules['kernel']=fakekernel
    scope=dict(math=math,time=time,np=np,R=R,C=R/'experiments/v1067_causal_replan_brake_reserve',
        load=lambda name,path:causal if 'causal' in name else norm,dump=lambda *_:None,virtual=virtual,
        finite_plan=finite,Reserve=Reserve,renew=renew)
    tree=ast.parse(Path(path).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),scope)
    error=None;reached=False
    try:scope['navigate'](v,setup,read(R/'experiments/v1275_time_window_fixed24/TASK_main_slot24.json'),time.time()+600,O/'recorded_interface',{})
    except NextRenewal:reached=True
    except AssertionError as exc:error=str(exc)
    finally:
        if previous is None:sys.modules.pop('kernel',None)
        else:sys.modules['kernel']=previous
    return dict(next_renewal_reached=reached,error=error,recorded_native_checked=v.count,renewal_origins=calls,
        models=0,physical_native=0,analytical_native=0,scope='recorded interface replay, not new dynamics')
if __name__=='__main__':
    path=Path(sys.argv[1])if len(sys.argv)>1 else R/'experiments/v1067_causal_replan_brake_reserve/owner.py'
    answer=run(path);print(json.dumps(answer));sys.exit(0 if answer['next_renewal_reached']else 1)
