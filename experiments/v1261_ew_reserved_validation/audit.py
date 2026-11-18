"""Complete physical, source, causal-refresh, component and terminal audit."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('INDEPENDENT_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
import gzip,fcntl,signal
from audit_chain import arrays,verify_component,verify_onward,verify_refusal
projection=load('phase_v1261_native_projection',R/'experiments/v1179_frozen_recovery_native/audit.py').project
causal=load('phase_v1261_independent_causal',R/'experiments/v1204_goal_audit_worker/native_audit.py')
def audit(task):
    out=Path(task['output']);r=read(out/'RESULT.json');base=load('phase_v1261_all_native_safety',C/'audit_refusal.py').audit(task,output_path=out/'BASE_NATIVE_AUDIT.json')
    setup=read(out/'physics/SETUP.json');native=arrays(out/'physics/NATIVE_TRACE.npz')
    states=np.vstack([q.initial(read(out/'CANONICAL_INITIAL_PACKET.json'))['state'],projection(native['qpos'],native['qvel'],setup)])
    commands=np.asarray(read(out/'physics/BODY_COMMANDS.json'));applied=read(out/'APPLIED_JOURNAL.json');final=read(out/'ACTUAL_FINAL_PACKET.json')
    memory=np.asarray([row['last_ctrl']+[row['integral']]for row in applied]+[final['controller_memory']['last_ctrl']+[final['controller_memory']['integral']]])
    def external(a,b):return dict(states=states[a:b+1],controls=native['ctrl'][a:b,setup['actuator_ids']],memory=memory[a:b+1],requests=commands[a:b][:,[1,2,5]])
    with gzip.open(out/'physics/SENSORS.json.gz','rt')as f:sensors=json.load(f)
    first=read(out/'EW_OBSERVATION_INPUT.json');a=first['packet']['native_tick'];assert a==r['recovery_origin_native']
    original=R/'runs/v858_nav2_verified/v1248/main_slot17';assert a==read(original/'ROUTE_RECOVERY_INPUT.json')['packet']['native_tick']
    with np.load(original/'physics/NATIVE_TRACE.npz')as z:
        for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
            assert native[key][:a].shape==z[key].shape and (not z[key].size or abs(native[key][:a]-z[key]).max()<=1e-8),'ORIGINAL_NORMAL_PREFIX_CHANGED'
    handoff=read(out/'EW_HANDOFF.json');b=handoff['handoff_native'];assert b-a==handoff['component_native']
    t=causal.table_check(out,'EW_OBSERVATION',first,sensors)
    comp=verify_component(first,t,read(out/'EW_OBSERVATION_SELECTION.json'),arrays(out/'EW_OBSERVATION_REFERENCE.npz'),arrays(out/'EW_OBSERVATION_EXECUTED.npz'),external(a,b),read(out/'EW_OBSERVATION_JOURNAL.json'))
    fresh=read(out/'EW_ONWARD_INPUT.json');assert fresh['packet']['native_tick']==b and handoff['actual_load']is comp['final_load']
    assert any(a<s['native_tick']<=b for s in sensors)and fresh['source']['source_native_tick']>a and fresh['source']['source_age_s']<=.051
    ft=causal.table_check(out,'EW_ONWARD',fresh,sensors);selection=read(out/'EW_ONWARD_SELECTION.json')
    if r.get('functional_failure'):
        assert r['functional_failure']['reason']=='EW_FRESH_DOMAIN_SOURCE_REFUSED'and len(commands)==b
        goal=verify_refusal(fresh,ft,selection)
    else:
        assert r['passed']and r['physical']['actual_travel_after_detection_m']>=1.
        goal=verify_onward(fresh,ft,selection,arrays(out/'EW_ONWARD_REFERENCE.npz'),arrays(out/'EW_ONWARD_EXECUTED.npz'),external(b,len(commands)),read(out/'EW_ONWARD_JOURNAL.json'))
        assert np.linalg.norm(states[-1,:2]-task['goal_xy'])+.08<=.45
    result=dict(passed=True,functional_passed=bool(r['passed']),physical_audit_complete=True,actual_replay_verified=True,
        native_reviewed=len(commands),component=comp,onward=goal,full_current_run_causal_domain_rebuilt_twice=True,
        analytical_cpp_native=comp['analytical_cpp_native']+goal['analytical_cpp_native'],models=0,new_mujoco_native=0,formal_retained_commit=False)
    dump(out/'FINAL_INDEPENDENT_AUDIT.json',result);return result
if __name__=='__main__':
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('EW_INDEPENDENT_AUDIT_300S')));signal.alarm(300)
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    print(json.dumps(audit(read(Path(sys.argv[1])))))
