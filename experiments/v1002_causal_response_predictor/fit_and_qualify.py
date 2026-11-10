"""Fit calibration schedules only; roll held-out requests without truth feedback."""
import gzip,hashlib,json,math,sys
from pathlib import Path
import numpy as np
from model import Predictor,virtual,virtual_rate
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v1002_causal_response_predictor'
def read(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def load(task):
    p=O/'responses'/task['name'];setup=read(p/'physics/SETUP.json');origin=task['origin_native_tick']
    with np.load(p/'physics/NATIVE_TRACE.npz')as z:q=z['qpos'][origin-1:];v=z['qvel'][origin-1:];ctrl=z['ctrl'][origin:,setup['actuator_ids']]
    yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));speed=v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw);lateral=-v[:,0]*np.sin(yaw)+v[:,1]*np.cos(yaw)
    enc=q[:,setup['steering_qpos_addresses']];rates=v[:,setup['steering_qvel_addresses']]
    delta=np.array([virtual(x)for x in enc]);rate=np.array([virtual_rate(a,b)for a,b in zip(enc,rates)])
    state=np.c_[q[:,:2],yaw,speed,lateral,v[:,5],delta,rate]
    records=json.loads(gzip.decompress((p/'physics/ALLOCATION.json.gz').read_bytes()));first=records[0]['proof']
    initial=dict(state=state[0].tolist(),last_ctrl=first['previous'],integral=first['previous_integral'],virtual_rate=task['virtual_rate_rad_s'])
    requests=[(r['v'],r['w'],r['stale'])for r in records]
    return dict(task=task,setup=setup,state=state,ctrl=ctrl,records=records,initial=initial,requests=requests)

if __name__=='__main__':
    for row in read(O/'RESTORE_RECEIPT.json')['files']:assert hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['sha256']
    tasks=read(R/'experiments/v995_sim_time_response/TASKS.json');rows=[load(x)for x in tasks]
    sx=[];sy=[];vx=[];vy=[];lx=[];ly=[]
    for row in rows[:2]:
        state=row['state'];u=row['ctrl'];target=np.array([virtual(x[:2])for x in u]);k=np.tan(state[1:,6])/.6
        sx.extend(np.c_[state[:-1,7],target-state[:-1,6]]);sy.extend(state[1:,7]);vx.extend(np.c_[state[:-1,3],u[:,2:].mean(axis=1)]);vy.extend(state[1:,3]);lx.extend(np.c_[state[1:,3]*k,state[1:,7]]);ly.extend(state[1:,4])
    solve=lambda x,y:np.linalg.lstsq(np.asarray(x),np.asarray(y),rcond=None)[0]
    steering=solve(sx,sy);speed=solve(vx,vy);lateral=solve(lx,ly)
    fixed=read(R/'experiments/v997_input_consistent_recovery/RESPONSE_PARAMETERS.json')
    p=dict(gain_a=fixed['gain_a'],steering_rate_b=fixed['steering_rate_b'],steering_discrete=steering.tolist(),speed_discrete=speed.tolist(),lateral_discrete=lateral.tolist(),
        fitted_tasks=[tasks[i]['name']for i in [0,1]],held_out_tasks=[tasks[i]['name']for i in [2,3]],sample_dt=.01,forecast_truth_feedback=False)
    matrix=np.array([[1-.01*steering[1],.01*steering[0]],[-steering[1],steering[0]]]);poles=np.linalg.eigvals(matrix)
    stable=bool(max(abs(poles))<1 and abs(speed[0])<1);p['steering_poles']=[[float(x.real),float(x.imag)]for x in poles];p['speed_pole']=float(speed[0]);p['stable_discrete_poles']=stable
    dump(C/'PARAMETERS.json',p);reports=[];full_pass=stable
    for index,row in enumerate(rows):
        predictor=Predictor(row['setup'],row['initial'],p);states=[];commands=[]
        for request in row['requests']:
            state,u=predictor.step(*request);states.append(state);commands.append(u)
        states=np.array(states);commands=np.array(commands);actual=row['state'][1:];position=np.linalg.norm(states[:,:2]-actual[:,:2],axis=1);heading=abs(np.arctan2(np.sin(states[:,2]-actual[:,2]),np.cos(states[:,2]-actual[:,2])))
        checks=dict(finite=bool(np.isfinite(states).all()),position=float(position.max())<=.01,heading=float(heading.max())<=.008,
            virtual_steering=float(abs(states[:,6]-actual[:,6]).max())<=.015,final_speed=float(abs(states[-50:,3]).max())<=.03,final_yaw=float(abs(states[-50:,5]).max())<=.03)
        if index>=2:full_pass=full_pass and all(checks.values())
        item=dict(index=index,name=row['task']['name'],held_out=index>=2,checks=checks,maximum_position_error_m=float(position.max()),maximum_heading_error_rad=float(heading.max()),
            maximum_virtual_steering_error_rad=float(abs(states[:,6]-actual[:,6]).max()),maximum_ctrl_prediction_error=float(abs(commands-row['ctrl']).max()),
            predictor_used_only_initial_state_and_planned_requests=True,analytical_prediction_steps=800,models_initialized=0,mujoco_integrations=0,physical_replay=0)
        reports.append(item);np.savez_compressed(O/(row['task']['name']+'_CAUSAL_PREDICTION.npz'),predicted_states=states,actual_saved_states=actual,predicted_ctrl=commands,actual_saved_ctrl=row['ctrl'])
    receipt=dict(passed=bool(full_pass),models=0,mujoco_integrations=0,physical_replay=0,analytical_prediction_steps=3200,
        parameters=p,task_reports=reports,fit_never_uses_held_out_schedules=True,forecast_never_uses_future_actual_speed_or_encoders=True,
        global_safety_bound=False,physical_ready=False,dependent_model_authority=False)
    dump(O/'CAUSAL_PREDICTION_QUALIFICATION.json',receipt);print(json.dumps(receipt))
