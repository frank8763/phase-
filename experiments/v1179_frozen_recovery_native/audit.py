from recovery_tools import *
import fcntl,gzip,hashlib,signal
projection=load('v1179_saved_state_projection',R/'experiments/v1003_causal_recovery_execution/predictor.py')
def project(qp,qv,setup):
    yaw=np.arctan2(2*(qp[:,3]*qp[:,6]+qp[:,4]*qp[:,5]),1-2*(qp[:,5]**2+qp[:,6]**2));front=qp[:,setup['steering_qpos_addresses']];vel=qv[:,setup['steering_qvel_addresses']]
    return np.c_[qp[:,:2],yaw,qv[:,0]*np.cos(yaw)+qv[:,1]*np.sin(yaw),-qv[:,0]*np.sin(yaw)+qv[:,1]*np.cos(yaw),qv[:,5],[projection.virtual(x)for x in front],[projection.virtual_rate(x,y)for x,y in zip(front,vel)]]
def audit(task):
    out=Path(task['output']);result=read(out/'RESULT.json');assert result['passed']and result['error']is None and result['formal_retained_commit']is False and result['universal_error_support_verified']is False
    setup=read(out/'physics/SETUP.json');scene=load('v1179_audit_scene_identity',R/'experiments/v1144_saved_entry_relay/scene_contract.py');scene.verify(setup,read(PARENT/'physics/SETUP.json'),task);assert sha(out/'physics/scene_model.mjb')==sha(PARENT/'physics/scene_model.mjb')
    with np.load(out/'physics/NATIVE_TRACE.npz')as z:trace={k:z[k].copy()for k in z.files}
    with np.load(PARENT/'physics/NATIVE_TRACE.npz')as z:
        for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:assert trace[k][:HISTORY].shape==z[k].shape and (not z[k].size or abs(trace[k][:HISTORY]-z[k]).max()<=1e-8),'HISTORICAL_STATE_CHANGED'
    with np.load(out/'physics/INITIAL_STATE.npz')as z,np.load(PARENT/'physics/INITIAL_STATE.npz')as y:assert np.array_equal(z['state'],y['state'])
    n=len(trace['time']);suffix=n-HISTORY;assert suffix==result['new_actual_native']==result['new_recovery_native']and result['historical_reconstruction_native']==HISTORY and result['total_actual_model_native']==result['fully_recorded_native']==n
    assert n==result['own_replay_native']and result['replay']['passed']and result['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and result['replay']['contact_mismatched_ticks']==0
    commands=np.array(read(out/'physics/BODY_COMMANDS.json'),float);historical=np.array(read(PARENT/'physics/BODY_COMMANDS.json'),float);assert commands.shape==(n,6)and np.array_equal(commands[:HISTORY,1:],historical[:,1:])
    initial=read(out/'CANONICAL_INITIAL_PACKET.json');states=np.vstack([q.initial(initial)['state'],project(trace['qpos'],trace['qvel'],setup)]);source=read(out/'ACTUAL_SOURCE_PACKET.json');journal=read(out/'RECOVERY_JOURNAL.json');assert len(journal)==suffix
    assert abs(np.array(q.initial(source)['state'])-states[HISTORY]).max()<=1e-8 and source['dynamic_discovered']is True and source['native_tick']==HISTORY
    ref,schedule=load_reference();rr=commands[:,[1,2,5]];owner=q.model.Predictor(setup,dict(q.initial(initial),steering_load_episode=False)).adapter
    early=read(R/'runs/v858_nav2_verified/v1144/observation_main/MODE_JOURNAL.json');late=read(PARENT/'MODE_JOURNAL.json');control_error=0.;memory_error=0.;capture=result['capture_native'];assert suffix==5885+capture+2200 and 0<=capture<=600
    for i in range(n):
        before=states[i];mode=None
        if 20160<=i<HISTORY:
            old=early[i-20160]if i<32515 else late[i-32515];assert old['native']==i;mode=old['target']if old['mode']else None
        owner.parked_target=mode
        if i>=HISTORY:
            j=i-HISTORY;row=journal[j];assert row['before_native']==i and row['local_native']==j and row['applied']and np.array_equal(row['request'],rr[i])
            assert abs(np.array(q.initial(row['packet'])['state'])-before).max()<=1e-8 and row['packet']['native_tick']==i and abs(row['packet']['sim_time']-.01*i)<=1e-8
            memory_error=max(memory_error,float(abs(owner.last-row['last_ctrl']).max()),abs(owner.integral-row['integral']))
            if j<5885:
                turn,speed=schedule[j];v,w,_=q.tracking.request(before,ref['states'][j],turn,speed);assert row['phase']=='reference'and row['reference_index']==j+1
            elif j<5885+capture:v,w,status=q.capture.request(before,ref['states'][-1,:3]);assert status=='CAPTURING'and row['phase']=='capture'
            else:v=w=0.;assert row['phase']=='final_stop'
            assert abs(rr[i]-[v,w,0.]).max()<=1e-12,'FROZEN_CAUSAL_POLICY_CHANGED'
        u=owner.compute(float(rr[i,0]),float(rr[i,1]),before[3],before[5],bool(rr[i,2]));control_error=max(control_error,float(abs(u-trace['ctrl'][i,setup['actuator_ids']]).max()))
    assert max(control_error,memory_error)<=1e-8
    with np.load(out/'SHADOW.npz')as z:shadow=z['states'].copy()
    org=dict(q.initial(source),steering_load_episode=False);engine=q.accelerator.Engine(setup,q.model.parameters()['coefficients']);cs,cu,cm=engine.simulate(org,[q.accelerator.row(float(v),float(w))for v,w,_ in rr[HISTORY:]])
    assert shadow.shape==cs.shape and abs(shadow-cs).max()<=1e-8,'COMPLETE_SHADOW_CHANGED'
    actual=states[HISTORY:];diff=actual-shadow;modelerror=np.c_[np.linalg.norm(diff[:,:2],axis=1),abs(np.arctan2(np.sin(diff[:,2]),np.cos(diff[:,2]))),abs(diff[:,6])];assert(modelerror<=[.04,.035,.015]).all()
    nominal=ref['states'][np.minimum(np.arange(suffix+1),5885)];dd=actual-nominal;poseerror=np.c_[np.linalg.norm(dd[:,:2],axis=1),abs(np.arctan2(np.sin(dd[:,2]),np.cos(dd[:,2])))];assert(poseerror<=[.04,.035]).all()
    selected=read(R/'runs/v1160_safe_terminal_connection/SELECTED.json')
    with np.load(R/selected['table_path'])as z:table={k:z[k].copy()for k in ['bounds','centers']}
    geometry=q.Geometry(selected['input'],table);shadowraw=np.minimum(*geometry.components(shadow[:,:3],np.arange(len(shadow))));assert shadowraw.min()>=q.REQUIRED
    final=actual[-1];goal=float(np.linalg.norm(final[:2]-[4.,-2.]));targeterr=float(np.linalg.norm(final[:2]-ref['states'][-1,:2]));assert goal+.08<=.45 and targeterr<=.025 and geometry.cycle(final[None,:3])[0]>=q.REQUIRED
    assert(rr[-2200:]==0).all()and abs(actual[-50:,3:6]).max()<=.003 and abs(actual[-50:,7]).max()<=.015
    lim=np.array(setup['limits']);rate=np.array(setup['slew_per_second'])*.01;ctrl=trace['ctrl'][:,setup['actuator_ids']]
    assert(ctrl>=lim[:,0]-1e-10).all()and(ctrl<=lim[:,1]+1e-10).all()and(abs(np.diff(np.vstack([initial['controller_memory']['last_ctrl'],ctrl]),axis=0))<=rate+1e-10).all()
    assert(abs(actual[:,3:6])<=[.13,.03,.16]).all()and trace['clearance'].min()>=.15-1e-8 and trace['self_margin'].min()>=-1e-10
    physical=result['physical'];assert physical['bad_contacts']==0 and physical['root_guard_native_count']==n and physical['fully_recorded_native']==n and physical['first_actor_detection']is not None
    assert np.isfinite(trace['qpos']).all()and np.isfinite(trace['qvel']).all()and abs(trace['time']-.01*np.arange(1,n+1)).max()<=1e-8
    with gzip.open(out/'physics/CONTACTS.json.gz','rt')as f:contacts=json.load(f)
    with gzip.open(out/'physics/SENSORS.json.gz','rt')as f:sensors=json.load(f)
    assert len(contacts)==n+1
    for s in sensors:
        k=s['native_tick'];assert 0<=k<=n and abs(s['time']-.01*k)<=1e-8 and abs(np.array(s['xy'])-states[k,:2]).max()<=1e-8 and len(s['ranges'])==32 and np.isfinite(s['ranges']).all()
    assert set(range(0,n+1,5)).issubset({s['native_tick']for s in sensors})
    proof=dict(passed=True,finite_original_saved_task_recovery=True,original_full_fresh_route_confirmation=False,historical_native_reviewed=HISTORY,new_recovery_native_reviewed=suffix,goal_distance_m=goal,goal_upper_m=goal+.08,minimum_native_actual_clearance=float(trace['clearance'].min()),maximum_model_response=modelerror.max(0),maximum_reference_pose=poseerror.max(0),maximum_control_error=control_error,maximum_memory_error=memory_error,shadow_cpp_python_error=float(abs(shadow-cs).max()),analytical_cpp_native=engine.native,analytical_python_native=0,models=0,new_mujoco_native=0,formal_retained_commit=False,universal_model_error_support_verified=False)
    dump(out/'FINAL_INDEPENDENT_AUDIT.json',proof);return proof
if __name__=='__main__':
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('RECOVERY_SAVED_AUDIT_180S')));signal.setitimer(signal.ITIMER_REAL,180)
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=audit(read(Path(sys.argv[1])));print(json.dumps({k:v for k,v in r.items()if k in ['passed','goal_distance_m','new_recovery_native_reviewed','analytical_cpp_native']}))
