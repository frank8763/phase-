"""Production fresh owner/chain against a saved measured-array vehicle only."""
from chain_tools import *
import types,gzip,fcntl,signal,traceback,importlib.abc,copy
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODEL_SOFTWARE_REHEARSAL '+name)
sys.meta_path.insert(0,NoModels())
def main():
    assert not(O/'QUALIFICATION.json').exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);begin=time.monotonic();end=time.time()+900
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SOFTWARE_CHAIN_900S')));signal.alarm(900)
    parent=R/'runs/v858_nav2_verified/v1179/main';setup=read(parent/'physics/SETUP.json')
    with np.load(parent/'physics/NATIVE_TRACE.npz')as z:data={k:z[k].copy()for k in z.files}
    rr=np.array(read(parent/'physics/BODY_COMMANDS.json'));initial=read(parent/'CANONICAL_INITIAL_PACKET.json')
    with gzip.open(parent/'physics/SENSORS.json.gz','rt')as f:rows=json.load(f)
    scans={}
    for row in rows:scans.setdefault(row['native_tick'],row)
    class Vehicle:
        def __init__(self):
            self.count=0;self.adapter=q.model.Predictor(setup,dict(q.initial(initial),steering_load_episode=False)).adapter;self.adapter.commands.ids=np.array(setup['actuator_ids']);self.d=types.SimpleNamespace();self.first_detection=None;self.sensor_rows=[];self.commands=[];self.calls=0;self.update();self.scan();self.scan()
        def update(self):
            if self.count:
                for k in ['qpos','qvel','ctrl']:setattr(self.d,k,data[k][self.count-1].copy())
            else:self.d.qpos=np.r_[-4.,-2.,.2,1.,np.zeros(16)];self.d.qvel=np.zeros(19);self.d.ctrl=np.zeros(data['ctrl'].shape[1])
            self.d.time=.01*self.count if self.count==0 else float(data['time'][self.count-1])
            if self.count>=15560:self.first_detection=dict(recorded_array_only=True)
        def body(self):
            qp=self.d.qpos;qv=self.d.qvel;yaw=math.atan2(2*(qp[3]*qp[6]+qp[4]*qp[5]),1-2*(qp[5]**2+qp[6]**2));return [*qp[:2],yaw,qv[0]*math.cos(yaw)+qv[1]*math.sin(yaw),qv[5]]
        def steering_sample(self):return np.r_[self.d.qpos[setup['steering_qpos_addresses']],self.d.qvel[setup['steering_qvel_addresses']]]
        def scan(self):
            assert self.count in scans,'ARRAY_SENSOR_SCHEDULE_CHANGED';row=copy.deepcopy(scans[self.count]);self.sensor_rows.append(row);return row
        def step(self,v,w,stale=False):
            i=self.count;assert i<len(rr);assert abs(np.array([v,w,float(stale)])-rr[i,[1,2,5]]).max()<=1e-10,('LIVE_REQUEST_DIFFERS',i,[v,w,stale],rr[i,[1,2,5]].tolist())
            b=self.body();u=self.adapter.compute(float(v),float(w),b[3],b[4],bool(stale));assert abs(u-data['ctrl'][i,setup['actuator_ids']]).max()<=1e-8,('LIVE_CONTROL_DIFFERS',i)
            self.commands.append(rr[i].tolist());self.count+=1;self.calls+=1;self.update();previous.body_gate(packet(self))
    out=O/'software_rehearsal';out.mkdir();error=None;result=dict(passed=False,models=0,new_mujoco_native=0,saved_array_vehicle_only=True,new_prediction_work=True)
    try:
        owner=configure_owner(O,end);import kernel;kernel.remaining_root=lambda:end-time.time();v=Vehicle();owner.navigate(v,setup,read(C/'TASK_main.json'),end,out,result)
        assert v.calls==42808 and result['passed']and result['feedback_execution']['full_fresh_t0_navigation']and result['feedback_execution']['formal_retained_commit']is False
        result.pop('_evidence',None);result.pop('_direct_segments',None);result.update(passed=True,production_feedback_calls=v.calls,historical_commands_used_by_production_owner=0,production_requests_and_controls_match_measured_fixture=True,goal_distance_m=result['actual_goal_distance_m'],known_recovery_counts=v._chain_counts,original_static_preview_total_unknown=True)
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());result=dict(passed=False,models=0,new_mujoco_native=0,error=error,saved_array_vehicle_only=True,production_feedback_calls=v.calls if 'v'in locals()else 0,known_observer_cpp_native=getattr(getattr(locals().get('v'),'_chain_engine',None),'native',None),analytical_total_native=None)
    result.update(wall_s=time.monotonic()-begin);dump(O/'QUALIFICATION.json',result);print(json.dumps({k:v for k,v in result.items()if k in ['passed','production_feedback_calls','goal_distance_m','error','wall_s']}));return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
