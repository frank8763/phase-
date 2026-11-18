"""Complete signed component execution and independent saved-state reconstruction."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from ew_handoff import *
import fcntl,json,signal,traceback
O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
def main():
    os=__import__('os');os.sched_setaffinity(0,{2});os.sched_setscheduler(0,os.SCHED_IDLE,os.sched_param(0))
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    raw=R/'runs/v858_nav2_verified/v1248/main_slot17';x=read(raw/'ROUTE_RECOVERY_INPUT.json')
    with np.load(raw/'ROUTE_JOINT_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
    spec=importlib.util.spec_from_file_location('v1254_analytical_interface',R/'experiments/v1203_goal_entry_handoff/qualify_entry.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    frozen={}
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and Path(p).resolve().is_relative_to(R)and Path(p).suffix=='.py':frozen[str(Path(p).resolve().relative_to(R))]=q.sha(Path(p))
    for p in [*C.glob('*.py'),C/'PROTOCOL.md',raw/'ROUTE_RECOVERY_INPUT.json',raw/'ROUTE_JOINT_TABLE.npz',R/'runs/v858_nav2_verified/v1237/route_main_EAST_WEST/ROUTE_RECOVERY_INPUT.json',R/'runs/v1159_bounded_steering_load/profile.so']:frozen[str(p.relative_to(R))]=q.sha(p)
    q.dump(O/'SOURCE_FREEZE.json',dict(files=frozen));start=time.monotonic();error=None;result={};native=0;engine=None
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('QUALIFICATION_600S')));signal.setitimer(signal.ITIMER_REAL,600)
    try:
        # Real entry binding negatives, before any analytical advancement.
        negatives=[]
        for name in ['clock','last_ctrl','future_source','lateral_state']:
            v=helper.AnalyticalInterface(x);one=copy.deepcopy(x);packet=v.packet()
            if name=='clock':packet['sim_time']+=.01
            elif name=='last_ctrl':packet['controller_memory']['last_ctrl'][0]+=.01
            elif name=='lateral_state':packet['body_lateral']+=.01
            else:one['source']['source_native_tick']+=1
            try:entry.bind_current(one,packet,False)
            except AssertionError:assert v.count==v.begin;negatives.append(name)
            else:raise AssertionError('BAD_BINDING_ACCEPTED '+name)
        v=helper.AnalyticalInterface(x);answer=execute(v,x,table,time.monotonic()+360,lambda v:v.packet(),lambda p:q.dump(O/'PROGRESS.json',p));native=answer['native']
        a=answer['arrays'];plan=answer['plan'];local=copy.deepcopy(x);local['goal']=plan['target'][:2].tolist()
        q.dump(O/'PLAN.json',{k:z for k,z in plan.items()if k not in ['states','controls','memory']})
        np.savez_compressed(O/'REFERENCE.npz',**{k:plan[k]for k in ['states','controls','memory']});np.savez_compressed(O/'EXECUTED.npz',**a);q.dump(O/'JOURNAL.json',answer['journal'])
        # Independent C++ rebuild uses the recorded requests, not source rows.
        engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);org=dict(q.initial(x['packet']),steering_load_episode=False)
        ss,uu,mm=engine.simulate(org,[q.accelerator.row(float(v),float(w))for v,w,_ in a['requests']])
        maximum=max(float(abs(ss-a['states']).max()),float(abs(uu-a['controls']).max()),float(abs(mm-a['memory']).max()),float(abs(ss-a['shadow']).max()))
        assert maximum<=1e-8,'INDEPENDENT_STATE_CONTROL_MEMORY'
        geometry=q.Geometry(x,table);static,dynamic=geometry.components(ss[:,:3],np.arange(len(ss)))
        low=float(np.minimum(static,dynamic).min())
        checks,upper=q.helper.checks(ss,uu,a['requests'],x['packet'],x['setup'],np.asarray(local['goal']),low,q.REQUIRED)
        assert all(checks.values())and geometry.cycle(ss[-1:,:3])[0]>=q.REQUIRED and np.array_equal(a['requests'][-2200:],np.zeros((2200,3)))
        assert np.isin(a['requests'][:,0],[-.03,0.,.08]).all()and len(answer['journal'])==native
        bad=a['controls'].copy();bad[0,0]+=.01
        assert abs(bad-uu).max()>1e-8,'NEGATIVE_CTRL_MUST_DIFFER'
        result=dict(passed=True,native=native,maximum_cpp_python_state_control_memory_error=maximum,minimum_raw_m=low,
            terminal_cycle_m=float(geometry.cycle(ss[-1:,:3])[0]),negative_bindings=negatives,external_ctrl_tamper_rejected=True,
            sensor_interface_calls=v.scans,actual_new_sensor_evidence=False,analytical_cpp_native=plan['analytical_cpp_native']+engine.native,
            analytical_python_native=2*native,original_goal_certified=False,physical_eligible=False)
        q.dump(O/'INDEPENDENT_COMPONENT_AUDIT.json',result)
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());q.dump(O/'ERROR.json',error)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,error=error,models=0,physical_native=0,source_unchanged=all(q.sha(R/p)==h for p,h in frozen.items()),wall_s=time.monotonic()-start,partial_work_unknown=error is not None)
        q.dump(O/'COMPLETION.json',result);print(json.dumps(result));fcntl.flock(lock,fcntl.LOCK_UN)
    return 0 if error is None else 1
if __name__=='__main__':sys.exit(main())
