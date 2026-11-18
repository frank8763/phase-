"""Real saved-ray source reconstruction, missing-evidence gate, whole onward seam."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('QUALIFICATION_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
import copy,gzip,types,traceback,fcntl,signal
live=load('phase_v1264_qualified_actual_live',C/'ew_live.py')
helper=load('phase_v1264_analytical_interface',R/'experiments/v1203_goal_entry_handoff/qualify_entry.py')
aud=load('phase_v1264_independent_stage_audit',C/'audit_chain.py')
causal=load('phase_v1264_saved_ray_audit',R/'experiments/v1204_goal_audit_worker/native_audit.py')

class Proxy(helper.AnalyticalInterface):
    def __init__(self,x,sensors):
        super().__init__(x);self.sensor_rows=copy.deepcopy(sensors);self.first_detection=dict(saved_actual_discovery=True)
        self.adapter.commands.ids=np.arange(4)
        del self.adapter.parked_target
        assert not hasattr(self.adapter,'parked_target'),'REGRESSION_REQUIRES_ACTUAL_MISSING_FIELD'
    def body(self):return self.packet()['body']
    def steering_sample(self):
        s=self.packet()['steering'];return np.asarray(s['position']+s['velocity'])
    @property
    def d(self):
        s=self.predictor.state;a=s[2]
        return types.SimpleNamespace(time=self.packet()['sim_time'],qvel=np.asarray([s[3]*np.cos(a)-s[4]*np.sin(a),s[3]*np.sin(a)+s[4]*np.cos(a)]),ctrl=self.adapter.last)
def bundle(raw):
    x=read(raw/('EW_ONWARD_INPUT.json'if(raw/'EW_ONWARD_INPUT.json').exists()else'ROUTE_RECOVERY_INPUT.json'))
    with gzip.open(raw/'physics/SENSORS.json.gz','rt')as f:sensors=json.load(f)
    return x,[s for s in sensors if s['native_tick']<=x['packet']['native_tick']]

def main():
    begin=time.monotonic();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not read(O/'APPROVAL.json')['models_authorized']
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('EW_LIVE_QUALIFICATION_600S')));signal.alarm(600)
    x,sensors=bundle(R/'runs/v858_nav2_verified/v1248/main_slot17');v=Proxy(x,sensors);out=O/'LIVE_CURRENT_MISSING_FUTURE';out.mkdir()
    # Reproduce the exact parent symptom before any analytical advancement.
    with np.load(R/'runs/v858_nav2_verified/v1248/main_slot17/ROUTE_JOINT_TABLE.npz')as z:redtable={k:z[k].copy()for k in z.files}
    try:live.component.execute(v,x,redtable,time.monotonic()+10,lambda owner:owner.packet())
    except AttributeError as exc:
        assert 'parked_target'in str(exc)and v.count==v.begin
        dump(O/'PARENT_RED_REPRODUCTION.json',dict(passed=True,parent_attribute_error_reproduced=True,analytical_native=0,physical_native=0,models=0))
    else:raise AssertionError('EXACT_PARENT_ATTRIBUTE_ERROR_NOT_REPRODUCED')
    # Reject active modes rather than silently clearing them.
    mode_negatives=[]
    for name in ['target','active','memory']:
        bad=Proxy(x,sensors)
        if name=='target':bad.adapter.parked_target=.1
        elif name=='active':bad.adapter._steering_motion_active=True
        else:bad.adapter.integral=float('nan')
        try:live.initialize_component_adapter(bad)
        except AssertionError:assert bad.count==bad.begin;mode_negatives.append(name)
        else:raise AssertionError('ACTIVE_OR_INVALID_ADAPTER_ACCEPTED '+name)
    # Exercise the actual two-stage owner. This proxy cannot manufacture future
    # physical scans: it must stop at the real-evidence gate after the component.
    try:live.execute(v,x['setup'],None,time.time()+500,None,out,None,output=out,remaining_fn=lambda:1000.)
    except AssertionError as exc:assert str(exc)=='EW_MISSING_NEW_ACTUAL_SENSOR_PACKETS',str(exc)
    else:raise AssertionError('ANALYTICAL_SCAN_ACCEPTED_AS_ACTUAL_EVIDENCE')
    sx=read(out/'EW_OBSERVATION_INPUT.json');table=causal.table_check(out,'EW_OBSERVATION',sx,sensors)
    trace=aud.arrays(out/'EW_OBSERVATION_EXECUTED.npz');reference=aud.arrays(out/'EW_OBSERVATION_REFERENCE.npz');plan=read(out/'EW_OBSERVATION_SELECTION.json');journal=read(out/'EW_OBSERVATION_JOURNAL.json')
    component=aud.verify_component(sx,table,plan,reference,trace,{k:trace[k]for k in['states','controls','memory','requests']},journal)
    old_arrays=aud.arrays(R/'runs/v1257_ew_adapter_entry/LIVE_CURRENT_MISSING_FUTURE/EW_OBSERVATION_EXECUTED.npz')
    assert set(old_arrays)==set(trace)and all(np.array_equal(old_arrays[k],trace[k])for k in trace),'ADAPTER_INIT_CHANGED_COMPONENT_SCIENCE_ARRAYS'
    assert v.count-v.begin==component['native']==9881 and not(out/'EW_ONWARD_INPUT.json').exists()
    negatives=[]
    for key in ['controls','states','memory','requests']:
        bad={k:trace[k].copy()for k in['states','controls','memory','requests']};bad[key][0,0]+=.01
        try:aud.verify_component(sx,table,plan,reference,trace,bad,journal)
        except AssertionError:negatives.append('component_'+key)
        else:raise AssertionError('EXTERNAL_COMPONENT_TAMPER_ACCEPTED '+key)
    # Independently exercise the new onward call site on a genuine recorded EW
    # packet and its own real historical whitelist, not hypothetical new scans.
    ox,osensors=bundle(R/'runs/v858_nav2_verified/v1257/slot17_main');ov=Proxy(ox,osensors);ow=O/'LIVE_REAL_REFRESHED_ONWARD';ow.mkdir()
    fresh,ft,calls=live.refresh(ov,ox['setup'],ow,'EW_ONWARD')
    independent=causal.table_check(ow,'EW_ONWARD',fresh,osensors)
    assert np.array_equal(ft['bounds'],independent['bounds'])
    # Include a loaded rest handoff: the first signed reverse must reset the
    # load naturally, with no arbitrary state/memory reset in the executor.
    ov._live_load=True;ov.predictor.steering_load_episode=True
    live.initialize_component_adapter(ov)
    selected=live.select_onward(fresh,ft,True,time.monotonic()+120)
    assert selected['passed'],'RECORDED_EW_ONWARD_SEAM_REFUSED'
    q.dump(ow/'EW_ONWARD_SELECTION.json',{k:a for k,a in selected.items()if k not in['states','controls','memory']})
    np.savez_compressed(ow/'EW_ONWARD_REFERENCE.npz',**{k:selected[k]for k in['states','controls','memory']})
    answer=live.run_onward(ov,fresh,ft,selected,time.monotonic()+120,lambda:True,live.packet)
    ot=ov._ew_onward_trace;np.savez_compressed(ow/'EW_ONWARD_EXECUTED.npz',**ot);q.dump(ow/'EW_ONWARD_JOURNAL.json',ov._ew_onward_journal)
    onward=aud.verify_onward(fresh,ft,read(ow/'EW_ONWARD_SELECTION.json'),aud.arrays(ow/'EW_ONWARD_REFERENCE.npz'),ot,{k:ot[k]for k in['states','controls','memory','requests']},ov._ew_onward_journal)
    for key in ['controls','states','memory','requests']:
        bad={k:ot[k].copy()for k in['states','controls','memory','requests']};bad[key][0,0]+=.01
        try:aud.verify_onward(fresh,ft,read(ow/'EW_ONWARD_SELECTION.json'),aud.arrays(ow/'EW_ONWARD_REFERENCE.npz'),ot,bad,ov._ew_onward_journal)
        except AssertionError:negatives.append('onward_'+key)
        else:raise AssertionError('EXTERNAL_ONWARD_TAMPER_ACCEPTED '+key)
    # Immutable full-native safety verifier on an actual old whole EW success.
    oldtask=next(t for t in read(R/'experiments/v1237_night_metadata_entry/TASKS.json')if t['task_id']=='route_main_EAST_WEST')
    base=load('phase_v1264_real_all_native_check',C/'audit_refusal.py').audit(oldtask,output_path=O/'REAL_ALL_NATIVE_AUDIT_QUALIFICATION.json')
    result=dict(passed=True,models=0,physical_native=0,component=component,onward=onward,negative_external_arrays=negatives,
        missing_actual_future_evidence_rejected=True,no_onward_steps_after_missing_evidence=True,
        real_current_ray_domain_reconstructed=True,real_refreshed_handoff_ray_domain_reconstructed=True,real_all_native_auditor_passed=base['passed'],
        actual_new_sensor_evidence=False,composite_actual_goal_not_yet_executed=True,
        parent_red_reproduced=True,adapter_entry_negatives=mode_negatives,component_arrays_unchanged=True,
        component_cpp_native=plan['analytical_cpp_native']+component['analytical_cpp_native'],onward_cpp_native=selected['analytical_cpp_native']+onward['analytical_cpp_native'],
        analytical_python_native=2*(component['native']+onward['native']),negative_audit_partial_work_unknown=True,wall_s=time.monotonic()-begin)
    dump(O/'LIVE_ADAPTER_QUALIFICATION.json',result);dump(O/'EW_SOURCE_QUALIFICATION.json',dict(passed=True,actual_new_sensor_evidence=False,composite_actual_goal_not_yet_executed=True))
    dump(O/'NATIVE_AUDIT_QUALIFICATION.json',dict(passed=True,actual_old_full_native=True,external_negatives=negatives));dump(O/'GOAL_AUDIT_QUALIFICATION.json',dict(passed=True,component_and_onward_seams=True));print((O/'LIVE_ADAPTER_QUALIFICATION.json').read_text())
    signal.alarm(0);fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=='__main__':
    try:main()
    except BaseException as exc:dump(O/'LIVE_PREPARATION_ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),models=0,physical_native=0,partial_analytical_unknown=True));raise
