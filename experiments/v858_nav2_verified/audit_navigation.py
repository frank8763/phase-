"""Saved evidence only: never initialize a model or import the online controller."""
import gzip,hashlib,json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
def audit(task):
 out=Path(task['output']);p=out/'physics';result=json.loads((out/'RESULT.json').read_text());setup=json.loads((p/'SETUP.json').read_text());replay=json.loads((p/'REPLAY.json').read_text());a=np.load(p/'NATIVE_TRACE.npz');n=len(a['time']);contacts=json.loads(gzip.decompress((p/'CONTACTS.json.gz').read_bytes()));commands=json.loads((p/'BODY_COMMANDS.json').read_text());ros=json.loads((out/'ROS_RESULT.json').read_text());proof=json.loads((p/'MODEL_BUILD_CONTRACT.json').read_text())
 ids=np.asarray(setup['actuator_ids'],int);limits=np.asarray(setup['limits']);ctrl=a['ctrl'][:,ids];rate=np.asarray(setup['slew_per_second'])*.01
 qpos=a['qpos'];qvel=a['qvel'];goal=float(np.linalg.norm(qpos[-1,:2]-task['goal_xy']));speed=float(np.linalg.norm(qvel[-1,:2]));bad=sum(c[2]in ['robot_self_contact','robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for frame in contacts for c in frame)
 checks=dict(native_count=n>0 and n==result['actual_native']==result['fully_recorded_native']==result['root_guard_native_count']==replay['replay_native'],full_native_timing=bool(np.allclose(a['time'],np.arange(1,n+1)*.01,rtol=0,atol=1e-9)),finite_arrays=all(np.isfinite(a[k]).all()for k in a.files),all_native_clearance=bool(np.min(a['clearance'])>=.15-1e-8),all_native_self=bool(np.min(a['self_margin'])>=-1e-10),contact_coverage=len(contacts)==n+1 and len(commands)==n,no_bad_contacts=bad==0 and result['bad_contacts']==0,ctrl_amplitude=bool(np.all(ctrl>=limits[:,0]-1e-10)and np.all(ctrl<=limits[:,1]+1e-10)),ctrl_slew=bool(np.all(abs(np.diff(np.vstack([np.zeros((1,len(ids))),ctrl]),axis=0))<=rate+1e-10)),model_sha=hashlib.sha256((p/'scene_model.mjb').read_bytes()).hexdigest()==setup['model_sha256'],full_control_state_replay=replay['passed']and replay['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and replay['contact_mismatched_ticks']==0,no_root_rewrite_record=not(p/'v648_nonphysical_mutation.json').exists(),closed_native=result['status']=='NATIVE_COMPLETE',wall_pacing=result.get('maximum_wall_lag_s',1)<=.1,genuine_ros_observations=ros.get('odometry_messages',0)>0 and ros.get('cmd_vel_messages',0)>0,model_semantics=proof.get('driver_contract',{}).get('passed',False))
 # Unknown proof schemas fail closed.
 checks['model_semantics']=proof.get('interface',{}).get('passed',False)
 discovery=result.get('first_actor_detection');travel=0.
 if task['dynamic'] and discovery:
  tick=discovery['native_tick'];xy=np.vstack([np.asarray(discovery['xy']),qpos[tick:,:2]]);travel=float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum())
 chain=(not task['dynamic'])or(discovery is not None and discovery['native_tick']>0 and travel>=1.-1e-8)
 functional=dict(action_success=ros.get('action_status')==4,strict_arrival=goal<=.45,actual_stopped=speed<=.03,dynamic_discovery_and_continuation=chain)
 summary=dict(evidence_passed=all(checks.values()),functional_passed=all(functional.values()),passed=all(checks.values())and all(functional.values()),checks=checks,functional_checks=functional,native_count=n,replay_native=replay['replay_native'],private_native=0,goal_distance_m=goal,final_translation_speed_m_s=speed,minimum_clearance_m=float(a['clearance'].min()),minimum_self_margin_m=float(a['self_margin'].min()),bad_contacts=bad,discovery=discovery,independently_recomputed_postdiscovery_travel_m=travel,maximum_state_error=replay['maximum_qpos_qvel_ctrl_mocap_error'])
 (out/'INDEPENDENT_AUDIT.json').write_text(json.dumps(summary,indent=2)+'\n');return summary
if __name__=='__main__':print(json.dumps(audit(json.loads(Path(sys.argv[1]).read_text()))))
