"""Explain stored motion/plans/active-reference tracking without any models."""
import collections
import json
import math
import os
from pathlib import Path
from reproduce import NoModel
import numpy as np

R=Path(__file__).resolve().parents[2];O=R/'runs/v1371_overnight_retrospective'
def read(p):return json.loads(p.read_text())
def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));results=[]
    for name in ['rpp_default_horizon_m1_s01_main','rpp_local_horizon_m1_s01_main']:
        d=R/'runs/v858_nav2_verified/v1370'/name;native=read(d/'RESULT.json');routes=read(d/'CAUSAL_ROUTE_RECORDS.json');segments=read(d/'SEGMENT_RECORDS.json');brakes=read(d/'CAUSAL_BRAKE_RECORDS.json');commands=read(d/'ROS_COMMANDS.json');journal=read(d/'APPLIED_JOURNAL.json')
        with np.load(d/'physics/NATIVE_TRACE.npz') as z:xy=z['qpos'][:,:2].copy();times=z['time'].copy()
        distances=np.linalg.norm(xy-[4.,-2.],axis=1);travel=np.linalg.norm(np.diff(xy,axis=0),axis=1)
        full=[x for x in routes if x['report'].get('status')=='GLOBAL_GOAL_PATH'];installed=[x for x in segments if x['event']=='INSTALL_ORDERED_ROUTE'];installed_ids={x['plan_index'] for x in installed}
        task=read(d/'TASK.json');references={0:dict(poses=task['reference_path'],plan_index=0,gear=1)};counter=0;queue=[];plan=0
        for event in segments:
            if event['event']=='INSTALL_ORDERED_ROUTE':
                queue=event['segments'][1:];plan=event['plan_index'];counter+=1;references[counter]=dict(event['segments'][0],plan_index=plan)
            elif event['event']=='CUSP_NEXT_SEGMENT_CHECK' and event['accepted']:
                assert queue;counter+=1;references[counter]=dict(queue.pop(0),plan_index=plan)
        tracking=[]
        for index,ref in references.items():
            selected=[c for c in commands if c['source']=='CONTROLLER' and c['segment_index']==index and abs(c['v'])>=.005]
            if not selected:continue
            bodies=np.asarray([journal[c['observation_native_tick']]['body'] for c in selected]);rear=bodies[:,:2]-.3*np.c_[np.cos(bodies[:,2]),np.sin(bodies[:,2])];path=np.asarray(ref['poses']);errors=[];angles=[]
            for offset in range(0,len(rear),256):
                delta=rear[offset:offset+256,None,:]-path[None,:,:2];squared=(delta*delta).sum(axis=2);nearest=squared.argmin(axis=1);errors.extend(np.sqrt(squared[np.arange(len(nearest)),nearest]).tolist());yaw=bodies[offset:offset+256,2]-path[nearest,2];angles.extend(np.abs(np.arctan2(np.sin(yaw),np.cos(yaw))).tolist())
            tracking.append(dict(segment_index=index,plan_index=ref['plan_index'],gear=ref['gear'],commands=len(selected),maximum_rear_reference_distance_m=max(errors),p95_rear_reference_distance_m=float(np.quantile(errors,.95)),maximum_heading_error_rad=max(angles)))
        speeds=np.asarray([j['body'][3] for j in journal]);zero=sum(abs(j['request'][0])<.005 and abs(j['request'][1])<.005 for j in journal)
        detail=[]
        for p in routes:
            detail.append(dict(index=p['index'],native_tick=p['native_tick'],status=p['report'].get('status'),planned_body_goal_distance_m=p['report'].get('body_goal_distance_m'),planner_kernel_s=p['report'].get('kernel_wall_s'),end_to_end_planning_s=p['wall_s'],live_minimum_m=p.get('live_result_validation',{}).get('minimum_clearance_m'),live_required_m=p.get('live_result_validation',{}).get('required_m'),installed=p['index'] in installed_ids,first_segment_refused='first_segment_refusal' in p))
        result=dict(task=name,original_goal_distance_m=8.,minimum_actual_goal_distance_m=float(distances.min()),minimum_goal_native_tick=int(distances.argmin()+1),final_actual_goal_distance_m=float(distances[-1]),minimum_goal_sim_time_s=float(times[distances.argmin()]),
            all_trajectory_travel_m=float(travel.sum()),after_detection_travel_m=native['physical']['actual_travel_after_detection_m'],actual_reverse_travel_m=float(travel[speeds[1:]<-.005].sum()),actual_forward_travel_m=float(travel[speeds[1:]>.005].sum()),zero_request_native=zero,
            route_proposals=len(routes),proposal_status_counts=dict(collections.Counter(x['report'].get('status') for x in routes)),full_goal_proposals=len(full),installed_full_goal_proposals=sum(x['index'] in installed_ids for x in full),installed_routes=len(installed),
            total_planner_kernel_s=sum(x['report'].get('kernel_wall_s',0.) for x in routes),total_planning_delivery_s=sum(x['wall_s'] for x in routes),task_native_wall_s=native['wall_s'],brake_reason_counts=dict(collections.Counter(x['reason'] for x in brakes)),
            last_brakes=[dict(native_tick=x['native_tick'],reason=x['reason'],body=x['body'],goal_distance_m=math.dist(x['body'][:2],[4.,-2.])) for x in brakes[-7:]],routes=detail,tracking_by_active_segment=tracking,
            maximum_active_rear_path_distance_m=max(x['maximum_rear_reference_distance_m'] for x in tracking),p95_segment_distance_max_m=max(x['p95_rear_reference_distance_m'] for x in tracking),models=0,physical_native=0,scope='saved-data diagnosis, no counterfactual execution')
        results.append(result)
    (O/'MOTION_AND_PLANNING.json').write_text(json.dumps(dict(results=results,models=0,physical_native=0),indent=2)+'\n')
    for x in results:print(json.dumps({k:v for k,v in x.items() if k not in ['routes','tracking_by_active_segment','last_brakes']}))

if __name__=='__main__':main()
