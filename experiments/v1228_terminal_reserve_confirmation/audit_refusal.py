from campaign_context import *
import gzip,fcntl,signal
projection=load('v1228_safety_projection',R/'experiments/v1179_frozen_recovery_native/audit.py').project
def audit(task,result_override=None,output_path=None):
    out=Path(task['output']);r=result_override if result_override is not None else read(out/'RESULT.json');assert(r['passed']or r.get('functional_failure'))and r['error']is None and r['historical_reconstruction_native']==r['historical_controls_used']==0 and r['formal_retained_commit']is False
    setup=read(out/'physics/SETUP.json');scene=load('v1184_saved_route_contract',R/'experiments/v1089_route_scene_contract/contract.py');scene.verify_saved(out/'physics',task)
    with np.load(out/'physics/NATIVE_TRACE.npz')as z:trace={k:z[k].copy()for k in z.files}
    n=len(trace['time']);p0=read(out/'CANONICAL_INITIAL_PACKET.json');states=np.vstack([q.initial(p0)['state'],projection(trace['qpos'],trace['qvel'],setup)]);commands=np.array(read(out/'physics/BODY_COMMANDS.json'));journal=read(out/'APPLIED_JOURNAL.json')
    assert n==r['new_actual_native']==r['total_actual_model_native']==r['fully_recorded_native']==r['own_replay_native']==len(journal)==len(commands)
    assert r['replay']['passed']and r['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and r['replay']['contact_mismatched_ticks']==0
    owner=q.model.Predictor(setup,dict(q.initial(p0),steering_load_episode=False)).adapter;maximum=0.;memoryerror=0.
    for i,row in enumerate(journal):
        assert row['before_native']==i and row['applied']and np.array_equal(row['request'],commands[i,[1,2,5]])
        assert abs(states[i,[3,5]]-commands[i,[3,4]]).max()<=1e-10
        memoryerror=max(memoryerror,float(abs(owner.last-row['last_ctrl']).max()),abs(owner.integral-row['integral']));owner.parked_target=row['parked_target'];u=owner.compute(*commands[i,[1,2,3,4]],bool(commands[i,5]));maximum=max(maximum,float(abs(u-trace['ctrl'][i,setup['actuator_ids']]).max()))
    assert max(maximum,memoryerror)<=1e-8
    limits=np.array(setup['limits']);rate=np.array(setup['slew_per_second'])*.01;ctrl=trace['ctrl'][:,setup['actuator_ids']];assert(ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()and(abs(np.diff(np.vstack([p0['controller_memory']['last_ctrl'],ctrl]),axis=0))<=rate+1e-10).all()
    assert(abs(states[:,3:6])<=[.13,.03,.16]).all()and trace['clearance'].min()>=.15-1e-8 and trace['self_margin'].min()>=-1e-10
    assert np.isfinite(trace['qpos']).all()and np.isfinite(trace['qvel']).all()and abs(trace['time']-.01*np.arange(1,n+1)).max()<=1e-8
    with gzip.open(out/'physics/SENSORS.json.gz','rt')as f:sensors=json.load(f)
    with gzip.open(out/'physics/CONTACTS.json.gz','rt')as f:contacts=json.load(f)
    assert len(contacts)==n+1 and all(c[2]not in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact']for row in contacts for c in row)
    for s in sensors:
        k=s['native_tick'];assert 0<=k<=n and abs(s['time']-.01*k)<=1e-8 and abs(np.array(s['xy'])-states[k,:2]).max()<=1e-8 and len(s['ranges'])==32
    assert set(range(0,n+1,5)).issubset({s['native_tick']for s in sensors})
    # Direct normal segments have current actual feedback, not saved controls.
    segments=read(out/'DIRECT_SEGMENTS.json');assert segments and segments[0]['origin_native']==0;discovery=r['first_causal_discovery_native'];assert discovery>0
    for s in segments:
        plan=read(R/s['path']);assert plan['passed']and all(plan['checks'].values());a=s['origin_native'];m=s['executed_native'];req=np.array(plan['planned_body_requests'])[:m];assert abs(req-commands[a:a+m][:,[1,2,5]]).max()<=1e-12
        predicted=np.array(plan['state_path'])[:m+1];diff=states[a:a+m+1]-predicted;assert np.linalg.norm(diff[:,:2],axis=1).max()<=.04 and abs(np.arctan2(np.sin(diff[:,2]),np.cos(diff[:,2]))).max()<=.035 and abs(diff[:,6]).max()<=.015
    assert any(s['label']=='DISCOVERY_STOP'and s['executed_native']==2200 for s in segments)
    final=read(out/'ACTUAL_FINAL_PACKET.json');assert previous.stopped(final)
    physical=r['physical'];assert physical['bad_contacts']==0 and physical['root_guard_native_count']==n and physical['first_actor_detection']is not None
    proof=dict(passed=True,safety_evidence_only=True,functional_passed=bool(r['passed']),native_reviewed=n,control_error=maximum,memory_error=memoryerror,all_actual_clearance_m=float(trace['clearance'].min()),analytical_cpp_native=0,models=0,new_mujoco_native=0)
    if (r.get('functional_failure')or{}).get('reason')=='OBSERVER_CERTIFIED_STOP_COMPLETED':
        backup=load('v1228_independent_backup',R/'experiments/v1219_stop_preserving_observer/audit_observer.py').verify_backup(out,time.monotonic()+180)
        proof.update(backup=backup,analytical_cpp_native=backup['analytical_cpp_native'])
    dump(output_path or out/'FINAL_INDEPENDENT_AUDIT.json',proof);return proof
if __name__=='__main__':
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('CONFIRMATION_SAFETY_AUDIT_300S')));signal.alarm(300);f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);print(json.dumps(audit(read(Path(sys.argv[1])))))
