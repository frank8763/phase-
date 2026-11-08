"""Closed native truth only for evaluation; causal set and map data never altered."""
import gzip,json,math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v894_wait_map_validation';REC=R/'records/nav2_v894_20261108'
sys.path[:0]=[str(R/'experiments/v891_dynamic_consistency_software'),str(R/'experiments/v881_timing_accounting_continuation')]
from support_envelope import polygon
from reproduce import pose,footprint,intersects
from snapshot_geometry import field
from exact_footprint import pose_values
def read(p):return json.loads(p.read_text())
def main():
    assert read(O/'COMPLETION.json')['closed'];p=R/'runs/v858_nav2_verified/v894/main_we';n=read(p/'RESULT.json');setup=read(p/'physics/SETUP.json');journal=json.loads(gzip.decompress((p/'MOTION_ENVELOPE.json.gz').read_bytes()));z=np.load(p/'physics/NATIVE_TRACE.npz');failed=np.load(p/'physics/FAILED_NATIVE_STATE.npz')
    cfg=read(R/'experiments/v894_wait_map_validation/A_motion.yaml');vertices=json.loads(cfg['local_costmap']['local_costmap']['ros__parameters']['footprint']);speed=np.linalg.norm(z['qvel'][:,:2],axis=1);at=z['time'];end=float(failed['time']);last=failed['qpos'];last_yaw=2*math.atan2(last[6],last[3]);lower=float(pose_values(field(setup['known']),[[last[0],last[1],last_yaw]])[0])
    # Last uninterrupted interval with measured translation speed below .03.
    moving=np.flatnonzero(speed>.03);index=int(moving[-1]+1)if len(moving)else 0
    interval=at>=at[index];travel=float(np.sum(np.linalg.norm(np.diff(z['qpos'][interval,:2],axis=0),axis=1)))
    states=journal['states'];tail=[s for s in states if s['time']>=end-2.];reliable=sum(bool(s['certified_unknown_rays'])for s in tail)
    rows=[]
    for t in [100.,110.,115.,120.,122.,124.,126.,128.,float(at[-1])]:
        i=int(np.argmin(abs(at-t)));q=z['qpos'][i];a=2*math.atan2(q[6],q[3]);state=next(s for s in reversed(states)if s['time']<=float(at[i])+1e-9);age=max(0.,float(at[i])-state['time']);bounds=np.asarray(state['support_bounds'])+.1+.08*(age+2.5);outer=polygon(bounds);body=footprint(pose(q[0],q[1],a),vertices)
        rows.append(dict(sim_time=float(at[i]),native_tick=round(float(at[i])*100),vehicle_xy=q[:2].tolist(),yaw=a,actual_speed_m_s=float(speed[i]),actual_clearance_m=float(z['clearance'][i]),causal_source_time=state['time'],source_age_s=age,causal_center_support=state['support_bounds'],last_certified_return_age_s=state['time']-state['last_hit_time'],padded_wait_pose_intersects_causal_forecast=intersects(body,outer),forecast_polygon=outer.tolist()))
    snapshots=read(p/'COSTMAP_SNAPSHOT_INDEX.json');global_rows=[x for x in snapshots if x['kind']=='global_costmap'];map_counts=[]
    for row in global_rows:
        with np.load(p/row['path'])as a:values=a['data']
        map_counts.append(dict(at=row['at'],cells=len(values),unknown_cells=int(np.sum(values==255))))
    c=setup['actor'];velocity=np.asarray(c['axis_xy'])*c['amplitude_m']*c['omega_rad_s']*math.cos(c['omega_rad_s']*end+c['phase_rad'])
    routes=read(p/'ROUTER_REQUESTS.json');d=n['first_actor_detection'];after=n['armed_at']+d['native_tick']*.01;successful_after=sum(bool(x['passed']and x['started_monotonic']>=after)for x in routes)
    result=dict(status='NATIVE_CLEARANCE_GATE_FAILED_WHILE_VEHICLE_ALMOST_STOPPED',actual_native=n['actual_native'],accepted_native_trace_rows=len(at),failed_native_snapshot_tick=n['actual_native'],failed_snapshot_complete_arrays=failed.files,replay_native=None,replay_status=n['replay_status'],minimum_actual_clearance_m=n['minimum_actual_clearance_m'],bad_contacts=n['bad_contacts'],known_static_full_body_clearance_lower_bound_m=lower,actual_minimum_source_is_dynamic_actor=lower>.15 and n['minimum_actual_clearance_m']<.15,final_vehicle_speed_m_s=n['final_translation_speed_m_s'],final_actor_speed_m_s_evaluator_only=float(np.linalg.norm(velocity)),goal_distance_m=n['goal_distance_m'],actual_travel_after_discovery_m=n['actual_travel_after_detection_m'],successful_periodic_routes_after_discovery=successful_after,final_slow_interval_start_sim_s=float(at[index]),final_slow_interval_duration_s=end-float(at[index]),translation_during_final_slow_interval_m=travel,last2s_received_scans=len(tail),last2s_scans_with_certified_unknown_hit=reliable,last_causal_state=states[-1],global_full_snapshot_count=len(global_rows),global_all_unknown_snapshot_count=sum(x['unknown_cells']==x['cells']for x in map_counts),global_snapshot_unknown_counts=map_counts,wait_pose_geometry_witnesses=rows,models=0,integrations=0,limitations=['Causal forecast intersection shows that waiting pose lacks admission under that outer forecast; it is not by itself proof every possible actor path collides','Native actual clearance failure independently establishes this physical failure; no model replay was added after closure','Complete failed final native snapshot retained; accepted native rows omit that final step, so no full-state replay claim','Known map and forecast snapshots do not reconstruct every internal planner/controller decision'])
    (REC/'STOPPED_ACTOR_ANALYSIS.json').write_text(json.dumps(result,indent=2)+'\n')
    # A small regression witness targets the real failure: zero speed is not a
    # sufficient wait-safe certificate when the causal actor forecast intersects.
    last_witness=next(x for x in rows if abs(x['sim_time']-126.)<.02)
    certificate=dict(original_zero_speed_rule_would_hold=last_witness['actual_speed_m_s']<=.03,new_wait_admission_requires_disjoint_forecast=not last_witness['padded_wait_pose_intersects_causal_forecast'],old_rule_rejected_by_concrete_saved_witness=last_witness['actual_speed_m_s']<=.03 and last_witness['padded_wait_pose_intersects_causal_forecast'],models=0,integrations=0,not_an_implemented_vehicle_recovery_policy=True)
    assert certificate['old_rule_rejected_by_concrete_saved_witness'];(REC/'WAIT_ADMISSION_COUNTEREXAMPLE.json').write_text(json.dumps(certificate,indent=2)+'\n')
    print(json.dumps({k:result[k]for k in ['final_slow_interval_start_sim_s','final_slow_interval_duration_s','translation_during_final_slow_interval_m','last2s_received_scans','last2s_scans_with_certified_unknown_hit','global_all_unknown_snapshot_count','known_static_full_body_clearance_lower_bound_m','successful_periodic_routes_after_discovery']}),flush=True)
if __name__=='__main__':main()
