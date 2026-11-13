"""Single saved Smac path, parked-steering handoff proposal, zero physical models."""
import sys,json,time,signal,hashlib,importlib.abc,shutil,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1108_parked_steering_handoff';OLD=R/'runs/v1107_reference_frame_alignment';STOP=R/'runs/v1103_connected_reference'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','torch','factory','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));import kernel,numpy as np
sys.path.insert(0,str(C));import track;from track import rollout
sys.path.insert(0,str(R/'experiments/v1103_connected_reference'));from reference_contract import context,admit,select_after_recheck
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,x):(O/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
    assert not(O/'PLAN.json').exists(),'NO_DUPLICATE_RUN'
    qualification=json.loads((O/'ENTRY_QUALIFICATION.json').read_text());assert qualification['passed']
    binding=json.loads((O/'SOURCE_FREEZE.json').read_text())
    assert all(sha(R/name)==value for name,value in binding.items()),'FROZEN_SOURCE_CHANGED'
    for p in C.iterdir():
        if p.suffix in {'.py','.md'}:shutil.copyfile(p,O/p.name)
    guard=sha(R/'REVIEW_PENDING');begun=time.monotonic();retained=None;replacement=None
    save('PLAN.json',dict(scope='one fixed V1107 path with stopped steering-only gear handoff',cross_track_threshold_m=.04,original_path=True,original_actuator_allocator=True,model_aware_preview_is_new_reference_policy=True,preview_maximum_native=500,applied_block_native=25,steering_grid_size=21,full_stop_native=2200,rolling_stop_spacing=125,maximum_native=40000,inner_wall_s=240,outer_wall_s=250,models=0,physical_integrations=0,new_measurements=0,official_planning_calls=0,automatic_physical_launch=False))
    answer=dict(passed=False,new_analytical_tracking_native=None,new_analytical_rolling_stop_native=None,reused_old_stop_native=2200)
    def halt(*_):raise TimeoutError('BOUNDED240S_SAVED_PATH_TRACKING')
    signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,240)
    try:
        old=json.loads((OLD/'COMPLETION.json').read_text());assert old['closed'] and old['official_planner']['passed'] and old['independent_rigid_geometry']['passed'] and old['retained_stop']['passed']
        x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());pg=json.loads((OLD/'PATH_GEARS.json').read_text())
        with np.load(STOP/'RETAINED_STOP.npz')as z:
            stop_s=z['states'].copy();stop_u=z['controls'].copy();stop_r=z['requests'].copy()
        assert np.max(abs(stop_s[0]-kernel.initial(x['packet'])['state']))<=1e-8,'RETAINED_STOP_WRONG_ORIGIN'
        retained=dict(context=context(x),requests=stop_r,controls=stop_u,independent_stop_passed=True)
        answer['reused_path_geometry']=old['independent_rigid_geometry'];answer['reused_retained_stop']=old['retained_stop']
        review,states,controls,requests=rollout(x,np.array(pg['path']),pg['gear'])
        np.savez_compressed(O/'CONTROLLER_SOURCE.npz',states=states,controls=controls,requests=requests,command_modes=np.array(track.MODES),steering_targets=np.array(track.ALIGN_TARGETS))
        answer['serialized_replay']=track.replay(x,states,controls,requests);assert answer['serialized_replay']['passed'],'SERIALIZED_MODE_REPLAY_MISMATCH'
        with np.load(OLD/'CONTROLLER_SOURCE.npz')as old_profile:
            n=3641;prefix=max(float(abs(states[:n+1]-old_profile['states'][:n+1]).max()),float(abs(controls[:n]-old_profile['controls'][:n]).max()),float(abs(requests[:n]-old_profile['requests'][:n]).max()))
        assert prefix<=1e-8,'FIRST_COMPLETED_GEAR_PREFIX_CHANGED'
        answer['first_completed_gear_prefix']=dict(native=3641,maximum_state_ctrl_request_error=prefix)
        answer.update(original_controller_review=review,new_analytical_tracking_native=len(requests),new_analytical_rolling_stop_native=2200*len(review.get('rolling_stops',[])))
        initial_error=float(abs(states[0]-kernel.initial(x['packet'])['state']).max());assert initial_error<=1e-8,'ACTUAL_ORIGIN_CHANGED'
        answer['actual_origin_binding']=dict(passed=True,maximum_state_error=initial_error,control_policy_changed=True,old155_prefix_equivalence_not_claimed=True)
        st,dy=kernel.ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(states[:,:3])
        answer['saved_profile_geometry']=dict(minimum_full_cycle_raw_m=float(np.minimum(st,dy).min()),required_raw_m=kernel.REQUIRED,all_recorded_predicted_states_pass=bool(np.minimum(st,dy).min()>=kernel.REQUIRED),complete_profile=review['passed'])
        if review['passed']:
            manifest=admit(x,review,states,controls,requests);save('COMPLETE_REFERENCE_CONTRACT.json',manifest);replacement=dict(context=context(x),manifest=manifest,whole_goal_admitted=True);answer['passed']=True
    except BaseException as exc:answer.update(passed=False,error=repr(exc),traceback=traceback.format_exc())
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    answer['preview_accounting']=dict(track.COUNTS)
    answer['analytical_counts_complete']=answer['new_analytical_tracking_native'] is not None and answer['preview_accounting']['cpp_work_exact']
    answer['entry_analytical_work']=qualification['analytical_work']
    if retained is not None:
        decision=select_after_recheck(context(x),retained,replacement);answer['handoff_selection']=dict(mode=decision['mode'],retained_stop_preserved=decision['retained_stop']is retained,actual_execution=False)
    answer['frozen_source_unchanged']=all(sha(R/name)==value for name,value in binding.items());answer['guard_original']=sha(R/'REVIEW_PENDING')==guard
    answer['passed']=bool(answer['passed'] and answer['frozen_source_unchanged'] and answer['guard_original'])
    answer.update(closed=True,wall_s=time.monotonic()-begun,models=0,physical_integrations=0,new_measurements=0,training_updates=0,official_planning_calls=0,automatic_physical_launch=False,whole_route_acceptance=False)
    save('COMPLETION.json',answer)
    pointer=R/'CURRENT_EXPERIMENT.json';current=json.loads(pointer.read_text())
    if current.get('active_run')=='runs/v1108_parked_steering_handoff':
        current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,automatic_additional_simulation=False,latest_software_experiment=dict(version='v1108',completion='runs/v1108_parked_steering_handoff/COMPLETION.json',passed=answer['passed'],closed=True,whole_route_acceptance=False,physical_integrations=0))
        tmp=pointer.with_suffix('.v1108.tmp');tmp.write_text(json.dumps(current,indent=2,ensure_ascii=False)+'\n');tmp.replace(pointer)
    print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
