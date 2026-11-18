"""Complete production policy on saved arrays, no new dynamics or model imports."""
from recovery_tools import *
import ast,copy,types,importlib.abc,fcntl
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODEL_QUALIFICATION '+name)
sys.meta_path.insert(0,NoModels())
from policy_execution import run_policy
def main():
    assert not(O/'QUALIFICATION.json').exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    saved=read(R/'runs/v1148_overnight_causal_recovery/actual_source/FRESH_INPUT.json');setup=saved['setup'];reference,schedule=load_reference()
    with np.load(R/'runs/v1163_joint_timing_repair/case001.npz')as z:ss,uu,mm,req=[z[k].copy()for k in ['states','controls','memory','requests']]
    assert len(uu)==8085 and abs(ss[0]-q.initial(saved['packet'])['state']).max()<=1e-8
    class Vehicle:
        def __init__(self):
            self.count=HISTORY;self.adapter=q.model.Predictor(setup,dict(q.initial(saved['packet']),steering_load_episode=False)).adapter;self.d=types.SimpleNamespace(qvel=np.zeros(19),time=.01*HISTORY);self.first_detection=dict(historical=True);self._recovery_setup=setup;self.calls=0;self.bad_body=False;self.scans=[];self.update()
        def update(self):
            s=ss[self.count-HISTORY];self.d.time=.01*self.count;self.d.qvel[0]=s[3]*math.cos(s[2])-s[4]*math.sin(s[2]);self.d.qvel[1]=s[3]*math.sin(s[2])+s[4]*math.cos(s[2]);self.d.qvel[5]=s[5]
        def body(self):
            s=ss[self.count-HISTORY];return [*s[:3],.14 if self.bad_body else s[3],s[5]]
        def steering_sample(self):
            s=ss[self.count-HISTORY];k=math.tan(s[6])/.6;front=np.array([math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k))]);der=(1+math.tan(s[6])**2)/np.array([(1-.27*k)**2+(.6*k)**2,(1+.27*k)**2+(.6*k)**2]);return np.r_[front,der*s[7]]
        def step(self,v,w,stale):
            i=self.count-HISTORY;assert abs(np.array([v,w,float(stale)])-req[i]).max()<=1e-12;assert abs(self.adapter.last-mm[i,:4]).max()<=1e-10 and abs(self.adapter.integral-mm[i,4])<=1e-10
            u=self.adapter.compute(v,w,ss[i,3],ss[i,5],stale);assert abs(u-uu[i]).max()<=1e-10;self.count+=1;self.calls+=1;self.update()
        def scan(self):self.scans.append(self.count);return dict(native_tick=self.count)
    class SavedPredictor:
        def __init__(self,setup,origin):self.index=0;assert abs(origin['state']-ss[0]).max()<=1e-8
        def step(self,v,w,stale):
            i=self.index;assert abs(req[i]-[v,w,float(stale)]).max()<=1e-12;self.index+=1;return ss[self.index].copy(),uu[i].copy()
    v=Vehicle();result=run_policy(v,reference,schedule,lambda:True,lambda _:None,predictor_factory=SavedPredictor)
    assert result['passed']and result['new_recovery_native']==v.calls==8085 and result['capture_native']==0 and result['final_stop_executed']
    assert result['formal_retained_commit']is False and result['universal_error_support_verified']is False
    assert len(v._recovery_journal)==8085 and abs(v.adapter.last-mm[-1,:4]).max()<=1e-10 and (req[-2200:]==0).all()
    negatives=[]
    for name,mutate,permit in [('second_owner',lambda v:setattr(v,'_recovery_owner',True),lambda:True),('wrong_source',lambda v:setattr(v,'count',HISTORY-1),lambda:True),('expired',lambda v:None,lambda:False),('body_cap',lambda v:setattr(v,'bad_body',True),lambda:True)]:
        z=Vehicle();mutate(z)
        try:run_policy(z,reference,schedule,permit,lambda _:None,predictor_factory=SavedPredictor)
        except AssertionError:negatives.append(name)
        else:raise AssertionError('NEGATIVE_ACCEPTED '+name)
        assert z.calls==0
    commands=np.array(read(PARENT/'physics/BODY_COMMANDS.json'));assert commands.shape==(HISTORY,6)
    early=read(R/'runs/v858_nav2_verified/v1144/observation_main/MODE_JOURNAL.json');late=read(PARENT/'MODE_JOURNAL.json')
    for i in range(20160,HISTORY):
        row=early[i-20160]if i<32515 else late[i-32515];assert row['native']==i and len(row['last_ctrl'])==4 and np.isfinite(row['integral'])
    # Import the complete actual entry and audit with all physical modules blocked.
    load('v1179_worker_interface',C/'worker.py');review=load('v1179_audit_interface',C/'audit.py')
    with np.load(PARENT/'physics/NATIVE_TRACE.npz')as z:
        actual=review.project(z['qpos'],z['qvel'],setup);ctrl=z['ctrl'][:,setup['actuator_ids']].copy()
    owner=q.model.Predictor(setup,dict(state=np.array([-4.,-2.,0.,0.,0.,0.,0.,0.]),last_ctrl=np.zeros(4),integral=0.,virtual_rate=.6,steering_load_episode=False)).adapter;maximum=0.
    for i,command in enumerate(commands):
        row=None if i<20160 else early[i-20160]if i<32515 else late[i-32515];owner.parked_target=row['target']if row and row['mode']else None
        if row:assert abs(owner.last-row['last_ctrl']).max()<=1e-10 and abs(owner.integral-row['integral'])<=1e-10
        before=np.array([-4.,-2.,0.,0.,0.,0.,0.,0.])if i==0 else actual[i-1];assert abs(before[[3,5]]-command[[3,4]]).max()<=1e-10
        u=owner.compute(float(command[1]),float(command[2]),before[3],before[5],bool(command[5]));maximum=max(maximum,float(abs(u-ctrl[i]).max()))
    assert maximum<=1e-8,'HISTORICAL_CAUSAL_CONTROL_CHANGED'
    for p in C.glob('*.py'):ast.parse(p.read_text())
    for task in read(C/'TASKS.json'):task_contract(task)
    dump(O/'QUALIFICATION.json',dict(passed=True,production_saved_array_calls=8085,historical_command_metadata=HISTORY,historical_saved_control_calls=HISTORY,historical_control_error=maximum,negative_cases=negatives,full_final_stop_2200=True,models=0,new_mujoco_native=0,new_analytical_predictions=0,saved_array_substitute_not_actual_physics=True,finite_evaluation_not_formal_admission=True))
    print('V1179_COMPLETE_SAVED_POLICY_QUALIFIED')
if __name__=='__main__':main()
