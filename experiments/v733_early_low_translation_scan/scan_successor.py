"""Concrete full native successor checks from actual post-scan belief only."""
import gzip,json,math
from types import SimpleNamespace
import numpy as np
from exact_footprint import pose_values
from reserved_recovery import ReservedRecovery
from recursive_domain import RecursiveDomain
from renewal_state import encode
from sensor_model import packet as sensed_packet

def evaluate_successors(index,real,domain,predictor,ids,model,mj,static,geometry,bounds,catalog,motion,protocol,initial_calls,root,physical,pose,charge_native):
    start=pose(real.qpos);when=float(real.time);goal=np.asarray(protocol['goal_xy']);candidates=[];forecasts=[]
    choices=[(0.,4.,4.),(0.,2.,6.),(0.,6.,2.),(-.42722137342572125,4.,4.),(.42722137342572125,4.,4.)]
    for j,(steer,left,right)in enumerate(choices):
        target=ReservedRecovery.target(steer,4.);target[2:]=[left,right]
        p=predictor.predict(real,target,ids,real.ctrl[ids],horizon=328,brake_after=248);q=predictor.last_forecast_qpos.copy();v=predictor.last_forecast_qvel.copy();ctrl=predictor.command_map.sequence(target,real.ctrl[ids],328,248)
        values=np.minimum(pose_values(SimpleNamespace(**static),p),domain.body_lower(p,when+np.arange(1,329)*.01));minimum=float(values.min());progress=float(np.linalg.norm(start[:2]-goal)-np.linalg.norm(p[-1,:2]-goal));angular=float(np.linalg.norm(v[-1,3:6]));reason='TIME_CLEARANCE'if minimum<.155 else'SELF_DOMAIN'if predictor.prediction_self_margin<.002 else'TERMINAL_SPEED'if predictor.terminal_speed>.025 else'TERMINAL_ANGULAR_SPEED'if angular>.025 else'GOAL_PROGRESS'if progress<.02 else None
        row=dict(index=j,target=target.tolist(),minimum_causal_clearance_m=minimum,self_margin_m=predictor.prediction_self_margin,terminal_speed_m_s=predictor.terminal_speed,terminal_angular_speed_rad_s=angular,goal_progress_m=progress,admissible=reason is None,reason=reason);candidates.append(row);forecasts.append((q,v,ctrl))
        np.savez_compressed(root/('SCAN_%02d_SUCCESSOR_%02d_PRIVATE.npz'%(index,j)),qpos=q,qvel=v,controls=ctrl,poses=p)
    result=dict(candidates=candidates,admissible_count=sum(x['admissible']for x in candidates),selected_index=None,actual_validation_steps=0,new_navigation_samples=0)
    eligible=[r for r in candidates if r['admissible']]
    if not eligible:return result
    selected=max(eligible,key=lambda r:(r['goal_progress_m'],r['minimum_causal_clearance_m'],-r['index']));j=selected['index'];q,v,controls=forecasts[j];copy=mj.MjData(model);mj.mj_copyData(copy,model,real)
    updated=RecursiveDomain(domain.origin);updated.time=domain.time;updated.possible=domain.possible.copy();updated.distance=domain.distance.copy();updated.last=dict(domain.last)
    actual_q=[];actual_v=[];observations=[];errors=[];minimum_actual=float('inf');minimum_self=float('inf');bad=0;max_excess=0.;public_start=round(when/.08)
    for tick,command in enumerate(controls):
        copy.ctrl[:]=0.;copy.ctrl[ids]=command;mj.mj_step(model,copy);charge_native();result['actual_validation_steps']+=1;motion.apply(model,copy);mj.mj_kinematics(model,copy);mj.mj_collision(model,copy);physical(copy,public_start+1+tick//8)
        actual_q.append(copy.qpos.copy());actual_v.append(copy.qvel.copy());error=max(float(np.max(abs(copy.qpos-q[tick]))),float(np.max(abs(copy.qvel-v[tick]))));errors.append(error);assert error<=1e-8,'SUCCESSOR_FULL_NATIVE_STATE_MISMATCH'
        if (tick+1)%8==0:
            step=public_start+(tick+1)//8;pp=pose(copy.qpos);packet=sensed_packet(pp[:2],pp[2],float(copy.time),step,protocol,motion,initial_calls);updated.update(packet);observations.append(dict(packet=packet,domain=encode(updated)));times=updated.time+np.linspace(0,3.28,329);truth=np.asarray([motion.xy(t)for t in times]);excess=float(updated.point_lower(truth,times).max());max_excess=max(max_excess,excess);assert excess<=1e-7
    result.update(selected_index=j,actual_full_state_error=max(errors),actual_goal_progress_m=float(np.linalg.norm(start[:2]-goal)-np.linalg.norm(pose(copy.qpos)[:2]-goal)),actual_new_packets=len(observations),maximum_actual_coverage_excess_m=max_excess,actual_terminal_pose=pose(copy.qpos).tolist(),actual_terminal_speed_m_s=float(np.linalg.norm(copy.qvel[:2])),actual_terminal_angular_speed_rad_s=float(np.linalg.norm(copy.qvel[3:6])),actual_final_domain_sha256=encode(updated)['possible_bits_sha256'])
    np.savez_compressed(root/('SCAN_%02d_SELECTED_SUCCESSOR_ACTUAL.npz'%index),qpos=actual_q,qvel=actual_v,controls=controls)
    with gzip.open(root/('SCAN_%02d_SUCCESSOR_OBSERVATIONS.json.gz'%index),'wt')as stream:json.dump(observations,stream)
    return result
