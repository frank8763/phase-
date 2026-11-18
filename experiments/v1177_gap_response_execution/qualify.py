"""Production executor + saved audit on original saved arrays; no new dynamics."""
from gap_tools import *
import ast,copy,math,types,tempfile,gzip,importlib.abc,fcntl
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODEL_QUALIFICATION '+name)
sys.meta_path.insert(0,NoModels())
import gap_execution as ex
review=load('v1177_production_saved_review',C/'audit.py')
def main():
    assert not(O/'QUALIFICATION.json').exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    fixture=read(R/'experiments/v1139_afternoon_observer/STATIC_T0_SOURCE_FIXTURE.json');setup=fixture['setup'];positive=[];negative=[]
    for task in [t for t in read(C/'TASKS.json')if t['role']=='main']:
        plan=plan_for(task);ss,uu,mm,req=[plan[k]for k in ['states','controls','memory','requests']];n=len(uu)
        class Vehicle:
            def __init__(self):
                self.count=0;self.adapter=q.model.Predictor(setup,dict(q.initial(fixture['packet']),steering_load_episode=False)).adapter;self.d=types.SimpleNamespace(qvel=np.zeros(19),time=0.);self.commands=[];self.sensors=[];self.scan();self.scan()
            def body(self):
                s=ss[self.count];return [*s[:4],s[5]]
            def steering_sample(self):
                s=ss[self.count];k=math.tan(s[6])/.6;front=np.array([math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k))]);der=(1+math.tan(s[6])**2)/np.array([(1-.27*k)**2+(.6*k)**2,(1+.27*k)**2+(.6*k)**2]);return np.r_[front,der*s[7]]
            def scan(self):
                s=ss[self.count];r=dict(native_tick=self.count,time=.01*self.count,xy=s[:2].tolist(),yaw=float(s[2]),ranges=[3.]*32);self.sensors.append(r);return r
            def step(self,v,w,stale):
                i=self.count;assert i<n and np.max(abs(np.array([v,w,float(stale)])-req[i]))<=1e-12
                s=ss[i];u=self.adapter.compute(v,w,s[3],s[5],stale);assert abs(u-uu[i]).max()<=1e-10
                self.commands.append([0.,v,w,s[3],s[5],stale]);self.count+=1;a=ss[self.count];self.d.time=.01*self.count;self.d.qvel[0]=a[3]*math.cos(a[2])-a[4]*math.sin(a[2]);self.d.qvel[1]=a[3]*math.sin(a[2])+a[4]*math.cos(a[2]);self.d.qvel[5]=a[5]
        vehicle=Vehicle();certs=[]
        def certify(packet):
            row=dict(passed=True,checks=dict(synthetic_interface_only=True),minimum_raw=.35,packet=copy.deepcopy(packet),analytic_native=2200,synthetic=True);certs.append(row);return row
        result=ex.run_component(vehicle,plan,certify,lambda *_:True,lambda *_:None);assert result['passed']and vehicle.count==n and abs(vehicle.adapter.last-mm[-1,:4]).max()<=1e-10
        result.update(synthetic=True,models=0,new_actual_native=n,own_replay_native=n,fully_recorded_actual_native=n,error=None,measured_feature_covered=True,replay=dict(passed=True,maximum_qpos_qvel_ctrl_mocap_error=0.,contact_mismatched_ticks=0),physical=dict(bad_contacts=0,root_guard_native_count=n,fully_recorded_native=n,first_actor_detection=None))
        after=ss[1:];qp=np.zeros((n,20));qv=np.zeros((n,19));ctrl=np.zeros((n,11));qp[:,:2]=after[:,:2];qp[:,2]=.2;qp[:,3]=np.cos(after[:,2]/2);qp[:,6]=np.sin(after[:,2]/2)
        k=np.tan(after[:,6])/.6;front=np.c_[np.arctan(.6*k/(1-.27*k)),np.arctan(.6*k/(1+.27*k))];der=(1+np.tan(after[:,6])**2)[:,None]/np.c_[(1-.27*k)**2+(.6*k)**2,(1+.27*k)**2+(.6*k)**2]
        qp[:,setup['steering_qpos_addresses']]=front;qv[:,setup['steering_qvel_addresses']]=der*after[:,7,None];qv[:,0]=after[:,3]*np.cos(after[:,2])-after[:,4]*np.sin(after[:,2]);qv[:,1]=after[:,3]*np.sin(after[:,2])+after[:,4]*np.cos(after[:,2]);qv[:,5]=after[:,5];ctrl[:,setup['actuator_ids']]=uu
        root=O/'qualification';root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root,prefix='saved_array_only_')as folder:
            out=Path(folder);(out/'physics').mkdir();fake=dict(task,output=str(out))
            for file,value in [('RESULT.json',result),('physics/SETUP.json',setup),('ACTUAL_INITIAL_PACKET.json',vehicle._gap_journal[0]['packet']),('REQUEST_JOURNAL.json',vehicle._gap_journal),('MEASURED_STOP_CERTIFICATES.json',certs),('physics/BODY_COMMANDS.json',vehicle.commands)]:dump(out/file,value)
            np.savez_compressed(out/'physics/NATIVE_TRACE.npz',time=np.arange(1,n+1)*.01,qpos=qp,qvel=qv,ctrl=ctrl,clearance=np.full(n,.35),self_margin=np.full(n,.01),mocap_pos=np.empty((n,0,3)),mocap_quat=np.empty((n,0,4)))
            for file,value in [('CONTACTS.json.gz',[[]for _ in range(n+1)]),('SENSORS.json.gz',vehicle.sensors)]:
                with gzip.open(out/'physics'/file,'wt')as f:json.dump(value,f)
            audit=review.audit(fake,save=False,synthetic=True,review_stops=False);assert audit['passed'];positive.append(dict(component=task['component'],production_calls=n,production_saved_audit=True,synthetic_only=True))
            for label,file,mutate in [('memory','REQUEST_JOURNAL.json',lambda z:z[2300].__setitem__('integral',z[2300]['integral']+.001)),('request','physics/BODY_COMMANDS.json',lambda z:z[2300].__setitem__(1,z[2300][1]+.001)),('incomplete_stop','MEASURED_STOP_CERTIFICATES.json',lambda z:z[0].__setitem__('analytic_native',2199)),('clock','REQUEST_JOURNAL.json',lambda z:z[0]['packet'].__setitem__('sim_time',.01))]:
                path=out/file;before=path.read_bytes();data=json.loads(before);mutate(data);dump(path,data)
                try:review.audit(fake,save=False,synthetic=True,review_stops=False)
                except AssertionError:negative.append(task['component']+'_'+label)
                else:raise AssertionError('MUTATION_ACCEPTED '+label)
                path.write_bytes(before)
        # These are production no-drive entry guards, using the same substitute.
        for label,mutate,permit,cert in [('second_owner',lambda v:setattr(v,'_gap_executing',True),lambda *_:True,certify),('missing_stop',lambda v:None,lambda *_:True,lambda _:(_ for _ in ()).throw(AssertionError('missing'))),('expired',lambda v:None,lambda *_:False,certify)]:
            v=Vehicle();mutate(v)
            try:ex.run_component(v,plan,cert,permit,lambda *_:None)
            except AssertionError:negative.append(task['component']+'_'+label)
            else:raise AssertionError('ENTRY_NEGATIVE_ACCEPTED '+label)
            assert v.count==0
    worker=load('v1177_worker_noauthority',C/'worker.py');argv=sys.argv[:];sys.argv=['worker',str(C/'TASK_rate_main.json')]
    try:
        try:worker.main()
        except AssertionError as e:assert 'NO_NEW_MODEL_AUTHORITY'in str(e);negative.append('worker_no_authority')
        else:raise AssertionError('MODEL_AUTHORITY_GATE_BYPASSED')
    finally:sys.argv=argv
    for file in C.glob('*.py'):ast.parse(file.read_text())
    assert all(n not in sys.modules for n in ['mujoco','vehicle','torch','rclpy'])
    result=dict(passed=True,components=positive,rejected=negative,models=0,physical_native=0,new_state_prediction=0,synthetic_calls=sum(z['production_calls']for z in positive),no_physical_factory_imported=True,physical_window_open=False)
    dump(O/'QUALIFICATION.json',result);print(json.dumps(result));fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=='__main__':main()
