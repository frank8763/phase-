"""Saved-data audit; no physical model construction/integration."""
from chain_tools import *
import gzip,fcntl,signal,types
from chain import fresh_evidence,joint_table,front,Engine,initial,remaining_rows,certify
projection=load('v1180_state_projection',R/'experiments/v1179_frozen_recovery_native/audit.py').project
def audit(task):
    out=Path(task['output']);r=read(out/'RESULT.json');assert r['passed']and r['error']is None and r['historical_reconstruction_native']==r['historical_controls_used']==0 and r['formal_retained_commit']is False
    setup=read(out/'physics/SETUP.json');scene=load('v1180_audit_scene',R/'experiments/v1144_saved_entry_relay/scene_contract.py');scene.verify(setup,read(R/'runs/v858_nav2_verified/v1179/main/physics/SETUP.json'),task);assert sha(out/'physics/scene_model.mjb')==setup['model_sha256']
    with np.load(out/'physics/INITIAL_STATE.npz')as a,np.load(R/'runs/v858_nav2_verified/v1179/main/physics/INITIAL_STATE.npz')as b:assert np.array_equal(a['state'],b['state'])
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
    # Current-run scan provenance for both fresh certificate handoffs.
    source_checks=[]
    for name in ['OBSERVATION_ENTRY.json','REFRESH_INPUT.json','RECOVERY_INPUT.json']:
        x=read(out/name);k=x['packet']['native_tick'];dummy=types.SimpleNamespace(sensor_rows=[s for s in sensors if s['native_tick']<=k],count=k,d=types.SimpleNamespace(time=x['packet']['sim_time']),body=lambda:None)
        # fresh_evidence needs only packet for causal clock, not a physical vehicle.
        from refresh import causal_packets
        clean,_=causal_packets(dummy.sensor_rows,x['packet']);causal=load('v1180_audit_causal_'+name,R/'experiments/v1024_full_route_execution/causal.py');norm=load('v1180_audit_norm_'+name,R/'experiments/v1037_periodic_norm_source/periodic_norm.py');e=causal.Evidence(setup['known']);e.periodic=norm.PeriodicSupport()
        for s in clean:e.update(s)
        got=e.source(dummy);assert got['source_native_tick']==x['source']['source_native_tick']and abs(got['source_age_s']-x['source']['source_age_s'])<=1e-9
        for a,b in zip(got['periodic']['vertices'],x['source']['periodic']['vertices']):assert np.array(a).shape==np.array(b).shape and abs(np.array(a)-b).max()<=1e-9
        assert abs(np.array(q.initial(x['packet'])['state'])-states[k]).max()<=1e-8
        source_checks.append(dict(file=name,native=k,maximum_input_tick=clean[-1]['native_tick']))
    # Direct normal segments have current actual feedback, not saved controls.
    segments=read(out/'DIRECT_SEGMENTS.json');assert segments and segments[0]['origin_native']==0;discovery=r['first_causal_discovery_native'];assert discovery>0
    for s in segments:
        plan=read(R/s['path']);assert plan['passed']and all(plan['checks'].values());a=s['origin_native'];m=s['executed_native'];req=np.array(plan['planned_body_requests'])[:m];assert abs(req-commands[a:a+m][:,[1,2,5]]).max()<=1e-12
        predicted=np.array(plan['state_path'])[:m+1];diff=states[a:a+m+1]-predicted;assert np.linalg.norm(diff[:,:2],axis=1).max()<=.04 and abs(np.arctan2(np.sin(diff[:,2]),np.cos(diff[:,2]))).max()<=.035 and abs(diff[:,6]).max()<=.015
    assert any(s['label']=='DISCOVERY_STOP'and s['executed_native']==2200 for s in segments)
    # Every stored observer stop proof independently repropagated from its own
    # actual state/memory. The older library bound is activated only as declared.
    library=read(R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json')
    with np.load(R/'runs/v1135_causal_batch/domain/JOINT_TABLE.npz')as z:table={k:z[k].copy()for k in ['bounds','centers']}
    g=q.Geometry(library,table);engine=Engine(setup);rows=read(R/'runs/v1144_saved_entry_relay/software/ROWS.json')['rows'];certs=read(out/'OBSERVER_CERTIFICATES.json');seam=read(out/'REFRESH_SEAM.json')
    for j,c in enumerate(certs):
        k=c['native'];assert abs(np.array(q.initial(c['packet'])['state'])-states[k]).max()<=1e-8;block=front(remaining_rows(rows,c['offset']),c['prefix'])
        for name,sche in [('current',[(0.,0.,2200,0)]),('prospective',block+[(0.,0.,2200,0)])]:
            ss,uu=engine.simulate(initial(c['packet']),sche);proof,_=g.final(dict(library,packet=c['packet'],goal=ss[-1,:2].tolist(),safe_terminal_pose=ss[-1,:3].tolist()),ss,uu,sche);assert proof['passed']==c[name]['passed']and proof['states_sha256']==c[name]['states_sha256']and proof['controls_sha256']==c[name]['controls_sha256']
        assert c['current']['passed']and(c['prospective']['passed']or j==len(certs)-1)
    assert not certs[-1]['prospective']['passed']and certs[-1]['native']==seam['native']
    fresh=read(out/'REFRESH_INPUT.json');bp=read(out/'LIVE_REFRESH_PROOFS.json');block=front(remaining_rows(rows,seam['offset']),8)
    for name,sche in [('current',[(0.,0.,2200,0)]),('prospective',block+[(0.,0.,2200,0)])]:
        ss,uu=engine.simulate(initial(fresh['packet']),sche);proof=certify(dict(fresh,goal=ss[-1,:2].tolist(),safe_terminal_pose=ss[-1,:3].tolist()),ss,uu,sche);assert proof['passed']and proof['states_sha256']==bp[name]['states_sha256']
    x=read(out/'RECOVERY_INPUT.json');start=x['packet']['native_tick'];assert start==seam['native']+2208
    with np.load(out/'LIVE_JOINT_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
    from joint_domain import Domain,NORMALS
    domain=Domain(x['source']['periodic']['vertices']);assert np.array_equal(domain.A,table['A'])and np.array_equal(domain.b,table['b']);du=table['dual'];centers=table['centers'];directions=np.array([[[nx,nx*np.sin(.32*t),nx*np.cos(.32*t),ny,ny*np.sin(.32*t),ny*np.cos(.32*t)]for nx,ny in NORMALS]for t in centers]);res=directions-np.einsum('tnj,jk->tnk',du,domain.A);up=np.einsum('tnj,j->tn',du,domain.b)+np.where(res>=0,res*domain.upper,res*domain.lower).sum(2)+1e-8+.08*((2*np.pi/.32/256)/2+.075)+2e-7;assert(du>=0).all()and abs(up-table['bounds']).max()<=1e-9
    fixed=read(R/'experiments/v1163_joint_timing_repair/TASKS.json')['rows'];fast=q.accelerator.Engine(setup,q.model.parameters()['coefficients']);org=dict(q.initial(x['packet']),steering_load_episode=False);ss,uu,mm=fast.simulate(org,fixed);g=q.Geometry(x,table);assert q.proof(g,x,ss,uu,q.requests_of(fixed),mm)['passed']
    with np.load(out/'LIVE_RECOVERY_REFERENCE.npz')as z:assert abs(z['states']-ss).max()<=1e-8
    with np.load(out/'RECOVERY_SHADOW.npz')as z:shadow=z['states'].copy()
    req=commands[start:][:,[1,2,5]];cs,cu,cm=fast.simulate(org,[q.accelerator.row(float(v),float(w))for v,w,_ in req]);assert shadow.shape==cs.shape and abs(shadow-cs).max()<=1e-8
    delta=states[start:]-shadow;assert(np.c_[np.linalg.norm(delta[:,:2],axis=1),abs(np.arctan2(np.sin(delta[:,2]),np.cos(delta[:,2]))),abs(delta[:,6])]<=[.04,.035,.015]).all();assert np.minimum(*g.components(shadow[:,:3],np.arange(len(shadow)))).min()>=q.REQUIRED
    policy=read(out/'RECOVERY_POLICY_RESULT.json');pj=read(out/'RECOVERY_POLICY_JOURNAL.json');assert len(pj)==len(req)==8085+policy['capture_native']and(req[-2200:]==0).all();assert np.linalg.norm(states[-1,:2]-[4.,-2.])+.08<=.45 and g.cycle(states[-1:,:3])[0]>=q.REQUIRED
    schedule=[(t,v)for t,v,k,m in fixed for _ in range(k)]
    for i,row in enumerate(pj):
        if i<5885:
            turn,speed=schedule[i];v,w,_=q.tracking.request(states[start+i],ss[i],turn,speed)
        elif i<5885+policy['capture_native']:v,w,status=q.capture.request(states[start+i],ss[-1,:3]);assert status=='CAPTURING'
        else:v=w=0.
        assert abs(req[i]-[v,w,0.]).max()<=1e-12
    physical=r['physical'];assert physical['bad_contacts']==0 and physical['root_guard_native_count']==n and physical['first_actor_detection']is not None and physical['actual_travel_after_detection_m']>=1.
    proof=dict(passed=True,fresh_t0_known_course_development=True,historical_controls_used=0,native_reviewed=n,goal_distance_m=float(np.linalg.norm(states[-1,:2]-[4.,-2.])),minimum_native_actual_clearance=float(trace['clearance'].min()),control_error=maximum,memory_error=memoryerror,causal_sources=source_checks,all_observer_stop_proofs=len(certs),analytical_cpp_native=engine.native+fast.native,LP_calls=domain.calls,models=0,new_mujoco_native=0,formal_retained_commit=False,new24=False)
    dump(out/'FINAL_INDEPENDENT_AUDIT.json',proof);return proof
if __name__=='__main__':
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FRESH_SAVED_AUDIT_300S')));signal.alarm(300);lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=audit(read(Path(sys.argv[1])));print(json.dumps(r))
