"""Update path-dependent inputs while preserving all exogenous observations."""
import numpy as np

def refresh(env,original_obs,shift,B):
    _,before=B.state_hash(env,shift,include_model=True,components=True)
    raw=np.asarray(env.last_raw_obs,dtype=np.float32).copy();old_base=np.asarray(env.last_base_action,dtype=np.float32).copy()
    if raw.shape!=(127,) or int(env.inner.lidar_num)!=36:raise RuntimeError('Path observation schema differs')
    wanted=np.asarray([env.inner._waypoint_distance()/10.0,env.inner._waypoint_angle()/np.pi],dtype=np.float32)
    result=np.asarray(original_obs,dtype=np.float32).copy();result[38:40]+=wanted-raw[38:40];raw[38:40]=wanted
    env.last_raw_obs=raw;new_base=np.asarray(env._base_action(raw),dtype=np.float32);env.last_base_action=new_base.copy();result[127:129]+=new_base-old_base
    mask=np.ones(186,dtype=bool);mask[[38,39,127,128]]=False
    if not np.array_equal(result[mask],np.asarray(original_obs)[mask]):raise B.ReplayMismatch('Non-path observation changed')
    _,after=B.state_hash(env,shift,include_model=True,components=True)
    if set(before)!=set(after):raise B.ReplayMismatch('Splice changed state schema')
    changes=[k for k in before if before[k]!=after[k]]
    forbidden=[k for k in changes if not k.endswith(('.last_raw_obs','.last_base_action'))]
    if forbidden:raise B.ReplayMismatch('Splice changed physics/RNG/SHIFT/other cache: '+str(forbidden))
    return result,{'changed_state_components':changes,'changed_observation_components':np.flatnonzero(result!=original_obs).tolist(),
        'complete_other_state_equal':True,'all_non_path_observation_equal':True,'no_sensor_queries':True}

def install(C,A,B):
    apply_original=C.apply_candidate;rollout_original=C.rollout
    pending=False;audits=[]
    def apply(*args,**kwargs):
        nonlocal pending
        result=apply_original(*args,**kwargs);pending=True;return result
    def rollout(env,model,shift,obs,gate_step):
        nonlocal pending
        if pending:
            obs,audit=refresh(env,obs,shift,B);audits.append(audit);A.write(B.OUT/'semantic_sync_checks.json',audits)
        pending=False
        return rollout_original(env,model,shift,obs,gate_step)
    C.apply_candidate=apply;C.rollout=rollout
