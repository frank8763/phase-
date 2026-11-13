"""Single saved Smac path, metric-only correction, zero physical models."""
import sys,json,time,signal,hashlib,importlib.abc,shutil,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1104_polyline_tracking';OLD=R/'runs/v1103_connected_reference'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','torch','factory','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));import kernel,numpy as np
sys.path.insert(0,str(C));from track import rollout
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
    save('PLAN.json',dict(scope='one EW21520 saved complete Smac path with point-to-segment metric correction only',cross_track_threshold_m=.04,original_path_and_control_policy=True,full_stop_native=2200,rolling_stop_spacing=125,maximum_native=40000,inner_wall_s=240,outer_wall_s=250,models=0,physical_integrations=0,new_measurements=0,official_planning_calls=0,automatic_physical_launch=False))
    answer=dict(passed=False,new_analytical_tracking_native=None,new_analytical_rolling_stop_native=None,reused_old_stop_native=2200)
    def halt(*_):raise TimeoutError('BOUNDED240S_SAVED_PATH_TRACKING')
    signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,240)
    try:
        old=json.loads((OLD/'COMPLETION.json').read_text());assert old['closed'] and old['official_planner']['passed'] and old['independent_rigid_geometry']['passed'] and old['retained_stop']['passed']
        x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());pg=json.loads((OLD/'PATH_GEARS.json').read_text())
        with np.load(OLD/'RETAINED_STOP.npz')as z:
            stop_s=z['states'].copy();stop_u=z['controls'].copy();stop_r=z['requests'].copy()
        assert np.max(abs(stop_s[0]-kernel.initial(x['packet'])['state']))<=1e-8,'RETAINED_STOP_WRONG_ORIGIN'
        retained=dict(context=context(x),requests=stop_r,controls=stop_u,independent_stop_passed=True)
        answer['reused_path_geometry']=old['independent_rigid_geometry'];answer['reused_retained_stop']=old['retained_stop']
        review,states,controls,requests=rollout(x,np.array(pg['path']),pg['gear'])
        np.savez_compressed(O/'CONTROLLER_SOURCE.npz',states=states,controls=controls,requests=requests)
        answer.update(original_controller_review=review,new_analytical_tracking_native=len(requests),new_analytical_rolling_stop_native=2200*len(review.get('rolling_stops',[])))
        with np.load(OLD/'CONTROLLER_SOURCE.npz')as z:
            n=len(z['requests']);assert n==155 and len(requests)>=n,'SAVED155_PREFIX_INCOMPLETE'
            prefix=max(float(abs(states[:n+1]-z['states']).max()),float(abs(controls[:n]-z['controls']).max()),float(abs(requests[:n]-z['requests']).max()))
        assert prefix<=1e-8,'CONTROL_POLICY_PREFIX_CHANGED'
        answer['prefix_equivalence']=dict(passed=True,native=n,maximum_state_control_request_error=prefix)
        st,dy=kernel.ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(states[:,:3])
        answer['saved_profile_geometry']=dict(minimum_full_cycle_raw_m=float(np.minimum(st,dy).min()),required_raw_m=kernel.REQUIRED,all_recorded_predicted_states_pass=bool(np.minimum(st,dy).min()>=kernel.REQUIRED),complete_profile=review['passed'])
        if review['passed']:
            manifest=admit(x,review,states,controls,requests);save('COMPLETE_REFERENCE_CONTRACT.json',manifest);replacement=dict(context=context(x),manifest=manifest,whole_goal_admitted=True);answer['passed']=True
    except BaseException as exc:answer.update(passed=False,error=repr(exc),traceback=traceback.format_exc())
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    if retained is not None:
        decision=select_after_recheck(context(x),retained,replacement);answer['handoff_selection']=dict(mode=decision['mode'],retained_stop_preserved=decision['retained_stop']is retained,actual_execution=False)
    answer['frozen_source_unchanged']=all(sha(R/name)==value for name,value in binding.items());answer['guard_original']=sha(R/'REVIEW_PENDING')==guard
    answer['passed']=bool(answer['passed'] and answer['frozen_source_unchanged'] and answer['guard_original'])
    answer.update(closed=True,wall_s=time.monotonic()-begun,models=0,physical_integrations=0,new_measurements=0,training_updates=0,official_planning_calls=0,automatic_physical_launch=False,whole_route_acceptance=False)
    save('COMPLETION.json',answer)
    pointer=R/'CURRENT_EXPERIMENT.json';current=json.loads(pointer.read_text())
    if current.get('active_run')=='runs/v1104_polyline_tracking':
        current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,automatic_additional_simulation=False,latest_software_experiment=dict(version='v1104',completion='runs/v1104_polyline_tracking/COMPLETION.json',passed=answer['passed'],closed=True,whole_route_acceptance=False,physical_integrations=0))
        tmp=pointer.with_suffix('.v1104.tmp');tmp.write_text(json.dumps(current,indent=2,ensure_ascii=False)+'\n');tmp.replace(pointer)
    print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
