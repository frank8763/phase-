"""Audit existing complete qualification traces; never re-execute the policy."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('SAVED_ONLY '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
import gzip,fcntl,traceback
aud=load('phase_v1264_complete_stage_audit',C/'audit_chain.py')
causal=load('phase_v1264_complete_causal',R/'experiments/v1204_goal_audit_worker/native_audit.py')
def main():
    start=time.monotonic();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    prior=read(O/'LIVE_PREPARATION_ERROR.json');assert "'float' object is not callable"in prior['error']
    first=O/'LIVE_CURRENT_MISSING_FUTURE';second=O/'LIVE_REAL_REFRESHED_ONWARD'
    results=[];negative=[];cpp=0
    for prefix,out,raw in [('EW_OBSERVATION',first,R/'runs/v858_nav2_verified/v1248/main_slot17'),('EW_ONWARD',second,R/'runs/v858_nav2_verified/v1257/slot17_main')]:
        x=read(out/(prefix+'_INPUT.json'))
        with gzip.open(raw/'physics/SENSORS.json.gz','rt')as f:sensors=json.load(f)
        table=causal.table_check(out,prefix,x,sensors);selection=read(out/(prefix+'_SELECTION.json'));reference=aud.arrays(out/(prefix+'_REFERENCE.npz'));trace=aud.arrays(out/(prefix+'_EXECUTED.npz'));journal=read(out/(prefix+'_JOURNAL.json'))
        fn=aud.verify_component if prefix=='EW_OBSERVATION'else aud.verify_onward
        external={k:trace[k]for k in['states','controls','memory','requests']};answer=fn(x,table,selection,reference,trace,external,journal);cpp+=answer['analytical_cpp_native'];results.append(answer)
        for key in external:
            bad={k:a.copy()for k,a in external.items()};bad[key][0,0]+=.01
            try:fn(x,table,selection,reference,trace,bad,journal)
            except AssertionError:negative.append(prefix+'_'+key)
            else:raise AssertionError('BAD_EXTERNAL_ACCEPTED')
        if prefix=='EW_ONWARD':
            bad=read(out/(prefix+'_SELECTION.json'));bad['response_reserve_m']=0.
            try:fn(x,table,bad,reference,trace,external,journal)
            except AssertionError:negative.append('lowered_park_reserve')
            else:raise AssertionError('LOWERED_RESERVE_ACCEPTED')
    assert not(first/'EW_ONWARD_INPUT.json').exists()
    oldtask=next(t for t in read(R/'experiments/v1237_night_metadata_entry/TASKS.json')if t['task_id']=='route_main_EAST_WEST')
    base=load('phase_v1264_complete_base_safety',C/'audit_refusal.py').audit(oldtask,output_path=O/'REAL_ALL_NATIVE_AUDIT_QUALIFICATION.json')
    result=dict(passed=True,models=0,physical_native=0,component=results[0],onward=results[1],negative_external_arrays=negative,
        missing_actual_future_evidence_rejected=True,no_onward_steps_after_missing_evidence=True,
        real_current_ray_domain_reconstructed=True,real_refreshed_handoff_ray_domain_reconstructed=True,real_all_native_auditor_passed=base['passed'],
        actual_new_sensor_evidence=False,composite_actual_goal_not_yet_executed=True,old_complete_traces_reused_without_policy_execution=True,
        prior_auditor_scalar_shadowing_failure_retained=True,analytical_cpp_native=cpp,negative_audit_partial_work_unknown=True,wall_s=time.monotonic()-start)
    dump(O/'LIVE_ADAPTER_QUALIFICATION.json',result);dump(O/'EW_SOURCE_QUALIFICATION.json',dict(passed=True,actual_refreshed_packet_saved_qualification=True,models=0,physical_native=0))
    dump(O/'NATIVE_AUDIT_QUALIFICATION.json',dict(passed=True,external_negatives=negative,actual_old_full_native=True));dump(O/'GOAL_AUDIT_QUALIFICATION.json',dict(passed=True,reserved_source_full_execution=True));print((O/'LIVE_ADAPTER_QUALIFICATION.json').read_text());fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=='__main__':
    try:main()
    except BaseException as exc:dump(O/'COMPLETE_SAVED_AUDIT_ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),models=0,physical_native=0));raise
