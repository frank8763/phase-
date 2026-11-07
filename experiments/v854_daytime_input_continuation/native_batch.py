"""Prepared CPU native batch adapter; USER HAS NOT AUTHORIZED MODEL EXECUTION.

This file is not invoked by the zero-model qualifications. It uses the same
compiled robot predictor, original controls, full warmstart and single thread.
Native equivalence and physical timing remain UNQUALIFIED until a separately
authorized original-model test. No GPU throughput or speedup is asserted.
"""
import numpy as np


def rollout_existing_sequences(predictor,real,controls):
    import mujoco.rollout
    from self_geometry import quaternion_matrices,containment_margin
    m,d,mj=predictor.model,predictor.data,predictor.mj
    controls=np.asarray(controls,float);assert controls.ndim==3 and controls.shape[2]==4 and np.isfinite(controls).all()
    count,horizon,_=controls.shape;assert count>0 and horizon in [240,320,328,336]
    # Caller must deduplicate *full sequences*, keep original ordering, and
    # scatter outputs back before applying unchanged feasibility and scoring.
    mj.mj_resetData(m,d)
    for name in ['qpos','qvel','act','qacc_warmstart']:getattr(d,name)[:]=getattr(real,name)
    d.time=float(real.time);d.ctrl[:]=0.;mj.mj_forward(m,d)
    spec=mj.mjtState.mjSTATE_FULLPHYSICS;initial=np.empty(mj.mj_stateSize(m,spec));mj.mj_getState(m,d,initial,spec)
    action=np.zeros((count,horizon,m.nu));action[:,:,predictor.command_map.ids]=controls
    states,sensors=mujoco.rollout.rollout(m,d,np.repeat(initial[None],count,axis=0),action,initial_warmstart=np.repeat(real.qacc_warmstart[None],count,axis=0),persistent_pool=True)
    predictor.prediction_steps+=count*horizon
    q=states[:,:,1:1+m.nq];v=states[:,:,1+m.nq:1+m.nq+m.nv]
    flat=sensors.reshape(count*horizon,-1);geoms=flat[:,7:].reshape(count*horizon,-1,7)
    bounds=predictor.self_geometry.bounds(geoms[:,:,:3],quaternion_matrices(geoms[:,:,3:]),flat[:,:3],flat[:,3:7]).reshape(count,horizon,-1)
    output=[]
    for i in range(count):
        d.qpos[:]=q[i,-1];d.qvel[:]=v[i,-1];mj.mj_kinematics(m,d);terminal=predictor.self_geometry.actual(m,d);complete=np.vstack((bounds[i],terminal))
        yaw=np.arctan2(2*(q[i,:,3]*q[i,:,6]+q[i,:,4]*q[i,:,5]),1-2*(q[i,:,5]**2+q[i,:,6]**2))
        output.append(dict(qpos=q[i].copy(),qvel=v[i].copy(),poses=np.c_[q[i,:,:2],yaw],self_bounds=complete,minimum_self_margin=float(containment_margin(complete,predictor.domain).min()),terminal_speed=float(np.linalg.norm(v[i,-1,:2]))))
    return output
