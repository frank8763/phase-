"""Independent complete recorded-component verifier with actual rejection tests."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('SAVED_AUDIT_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import copy,fcntl,hashlib,importlib.util,json,math,os,time
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/(C.name+'_audit')
s=importlib.util.spec_from_file_location('v1255_independent_loader',R/'experiments/v1250_ew_current_goal/package_loader.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
entry=m.get_goal_entry();q=entry.q;np=entry.np
read=lambda p:json.loads(p.read_text())
def main():
    os.sched_setaffinity(0,{2});os.sched_setscheduler(0,os.SCHED_IDLE,os.sched_param(0))
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    source=R/'runs/v1255_ew_component_entry';raw=R/'runs/v858_nav2_verified/v1248/main_slot17'
    x=read(raw/'ROUTE_RECOVERY_INPUT.json');plan=read(source/'PLAN.json');journal=read(source/'JOURNAL.json')
    assert read(source/'COMPLETION.json')['passed']
    with np.load(raw/'ROUTE_JOINT_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
    with np.load(source/'EXECUTED.npz')as z:trace={k:z[k].copy()for k in z.files}
    expected_rows=plan['rows']+[[0.,0.,2200,0]]
    expected=q.requests_of(expected_rows);org=dict(q.initial(x['packet']),steering_load_episode=False)
    engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);ss,uu,mm=engine.simulate(org,expected_rows)
    g=q.Geometry(x,table);a,b=g.components(ss[:,:3],np.arange(len(ss)));low=float(np.minimum(a,b).min())
    def verify(external):
        assert external['requests'].shape==expected.shape and np.array_equal(external['requests'],expected),'REQUEST_SCHEDULE_BINDING'
        for key,target in [('states',ss),('shadow',ss),('controls',uu),('memory',mm)]:
            assert external[key].shape==target.shape and np.isfinite(external[key]).all() and abs(external[key]-target).max()<=1e-8,'FULL_EXTERNAL_'+key
        checks,upper=q.helper.checks(external['states'],external['controls'],external['requests'],x['packet'],x['setup'],np.asarray(plan['target'][:2]),low,q.REQUIRED)
        assert all(checks.values())and g.cycle(ss[-1:,:3])[0]>=q.REQUIRED
        assert np.array_equal(external['requests'][-2200:],np.zeros((2200,3)))and np.isin(expected[:,0],[-.03,0.,.08]).all()
        return upper
    upper=verify(trace);negatives=[]
    for key,index in [('controls',(0,0)),('states',(1,0)),('memory',(1,4)),('shadow',(1,2)),('requests',(0,1))]:
        bad={k:v.copy()for k,v in trace.items()};bad[key][index]+=.01
        try:verify(bad)
        except AssertionError:negatives.append(key)
        else:raise AssertionError('TAMPERED_EXTERNAL_ACCEPTED '+key)
    assert len(journal)==len(expected)
    load=False
    for i,row in enumerate(journal):
        assert row['native']==x['packet']['native_tick']+i+1 and np.array_equal(row['request'],expected[i])
        if expected[i,0]>=.005:load=True
        elif expected[i,0]<=-.005:load=False
        assert row['load']is load,'LOAD_EPISODE_HANDOFF'
    result=dict(passed=True,models=0,physical_native=0,native=len(uu),analytical_cpp_native=engine.native,
        minimum_raw_m=low,terminal_cycle_m=float(g.cycle(ss[-1:,:3])[0]),goal_upper_m=upper,
        maximum_state_control_memory_error=max(float(abs(trace[k]-v).max())for k,v in [('states',ss),('shadow',ss),('controls',uu),('memory',mm)]),
        actual_rejection_tests=negatives,continuous_shadow_and_load_verified=True,
        actual_sensor_evidence=False,original_goal_certified=False,physical_eligible=False,
        earlier_qualification_ctrl_negative_only_checked_difference_this_audit_tests_verifier_rejection=True)
    q.dump(O/'FINAL_INDEPENDENT_COMPONENT_AUDIT.json',result);print(json.dumps(result));fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=='__main__':main()
