"""Independent saved-data audit, no MuJoCo imports or physical integration."""
from route_tools import *
import gzip,fcntl,signal
projection=load('v1184_original_projection',R/'experiments/v1179_frozen_recovery_native/audit.py').project
def audit(task):
    if task['case_id']=='WEST_EAST':return load('v1184_exact_WE_audit',R/'experiments/v1180_fresh_recovery_chain/audit.py').audit(task)
    out=Path(task['output']);r=read(out/'RESULT.json');assert r['passed']and r['error']is None and r['historical_reconstruction_native']==r['historical_controls_used']==0 and r['formal_retained_commit']is False
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
    x=read(out/'ROUTE_RECOVERY_INPUT.json');start=x['packet']['native_tick'];assert start==r['recovery_origin_native']
    assert abs(np.array(q.initial(x['packet'])['state'])-states[start]).max()<=1e-8
    from refresh import causal_packets
    clean,_=causal_packets([s for s in sensors if s['native_tick']<=start],x['packet'])
    causal=load('v1184_audit_estimator',R/'experiments/v1024_full_route_execution/causal.py');norm=load('v1184_audit_prior',R/'experiments/v1037_periodic_norm_source/periodic_norm.py');e=causal.Evidence(setup['known']);e.periodic=norm.PeriodicSupport()
    for scan in clean:e.update(scan)
    import types
    fresh=e.source(types.SimpleNamespace(count=start,d=types.SimpleNamespace(time=x['packet']['sim_time'])))
    assert fresh['source_native_tick']==x['source']['source_native_tick'] and abs(fresh['source_age_s']-x['source']['source_age_s'])<=1e-9
    for a,b in zip(fresh['periodic']['vertices'],x['source']['periodic']['vertices']):assert np.array(a).shape==np.array(b).shape and abs(np.array(a)-b).max()<=1e-9
    with np.load(out/'ROUTE_JOINT_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
    from joint_domain import Domain,NORMALS
    domain=Domain(fresh['periodic']['vertices']);assert np.array_equal(domain.A,table['A'])and np.array_equal(domain.b,table['b'])
    du=table['dual'];centers=table['centers'];directions=np.array([[[nx,nx*np.sin(.32*t),nx*np.cos(.32*t),ny,ny*np.sin(.32*t),ny*np.cos(.32*t)]for nx,ny in NORMALS]for t in centers]);res=directions-np.einsum('tnj,jk->tnk',du,domain.A);upper=np.einsum('tnj,j->tn',du,domain.b)+np.where(res>=0,res*domain.upper,res*domain.lower).sum(2)+1e-8+.08*((2*np.pi/.32/256)/2+.075)+2e-7
    assert(du>=0).all()and abs(upper-table['bounds']).max()<=1e-9
    _,fixed=finite_plan(task['case_id']);assert read(out/'ROUTE_ROWS.json')==fixed
    fast=q.accelerator.Engine(setup,q.model.parameters()['coefficients']);org=dict(q.initial(x['packet']),steering_load_episode=False);ss,uu,mm=fast.simulate(org,fixed);g=q.Geometry(x,table);proof,rr=g.final(x,ss,uu,fixed);assert proof['passed']
    with np.load(out/'ROUTE_REFERENCE.npz')as z:
        for k,val in [('states',ss),('controls',uu),('memory',mm)]:assert z[k].shape==val.shape and abs(z[k]-val).max()<=1e-8
    pj=read(out/'ROUTE_POLICY_JOURNAL.json');policy=read(out/'ROUTE_POLICY_RESULT.json');req=commands[start:][:,[1,2,5]];assert len(pj)==len(req)==policy['recovery_native'] and(req[-2200:]==0).all()
    from route_policy import command
    schedule=[(float(t),float(v),bool(m))for t,v,k,m in fixed for _ in range(k)]
    rebuilt=[]
    for i,row in enumerate(pj):
        assert row['before_native']==start+i and abs(req[i]-row['request']).max()<=1e-12
        if i<len(schedule):
            turn,speed,park=schedule[i];vr,wr=command(states[start+i],ss[i],turn,speed,park);assert row['parked_target']==(turn if park else None) and row['reference_index']==i+1
        elif row['phase']=='capture':vr,wr,status=q.capture.request(states[start+i],ss[-1,:3]);assert status=='CAPTURING'
        else:vr=wr=0.;assert row['phase']=='final_stop'
        assert abs(req[i]-[vr,wr,0.]).max()<=1e-12
        rebuilt.append(q.accelerator.row(vr,wr,row['parked_target']is not None,row['parked_target']or 0.))
    cs,cu,cm=fast.simulate(org,rebuilt)
    with np.load(out/'ROUTE_SHADOW.npz')as z:assert z['states'].shape==cs.shape and abs(z['states']-cs).max()<=1e-8
    delta=states[start:]-cs;assert(np.c_[np.linalg.norm(delta[:,:2],axis=1),abs(np.arctan2(np.sin(delta[:,2]),np.cos(delta[:,2]))),abs(delta[:,6])]<=[.04,.035,.015]).all()
    assert np.minimum(*g.components(cs[:,:3],np.arange(len(cs)))).min()>=q.REQUIRED and g.cycle(states[-1:,:3])[0]>=q.REQUIRED
    for i,row in enumerate(pj):
        ref=ss[row['reference_index']];d=states[start+i+1]-ref;assert np.linalg.norm(d[:2])<=.04 and abs(math.atan2(math.sin(d[2]),math.cos(d[2])))<=.035
    physical=r['physical'];assert physical['bad_contacts']==0 and physical['root_guard_native_count']==n and physical['first_actor_detection']is not None and physical['actual_travel_after_detection_m']>=1.
    assert np.linalg.norm(states[-1,:2]-task['goal_xy'])+.08<=.45 and previous.stopped(read(out/'ACTUAL_FINAL_PACKET.json'))
    proof=dict(passed=True,fresh_t0_known_course_development=True,historical_controls_used=0,native_reviewed=n,goal_distance_m=float(np.linalg.norm(states[-1,:2]-task['goal_xy'])),minimum_native_actual_clearance=float(trace['clearance'].min()),control_error=maximum,memory_error=memoryerror,analytical_cpp_native=fast.native,models=0,new_mujoco_native=0,formal_retained_commit=False,new24=False,full_current_causal_domain_rebuilt=True)
    dump(out/'FINAL_INDEPENDENT_AUDIT.json',proof);return proof
if __name__=='__main__':
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V1184_SAVED_AUDIT_300S')));signal.alarm(300);lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);print(json.dumps(audit(read(Path(sys.argv[1])))))
