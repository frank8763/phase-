"""Independent current-source, full-stop, response, feedback and native audit."""
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1195_eight_gib_timed_refuge'))
from route_tools import *
C=Path(__file__).resolve().parent
O=R/'runs/v1204_goal_audit_worker'
sys.path.insert(0,str(C))
from audit_goal import load_bundle,verify
import gzip,types,fcntl,signal
sys.path.insert(0,str(R/'experiments/v1186_live_observer_regeneration'))
import candidate_observer as observer_source
import stop_certificates
import night_goal as goal_source
projection=load('v1195_projection',R/'experiments/v1179_frozen_recovery_native/audit.py').project
def table_check(out,name,x,sensors):
    from refresh import causal_packets
    from joint_domain import Domain,NORMALS
    k=x['packet']['native_tick'];clean,_=causal_packets([s for s in sensors if s['native_tick']<=k],x['packet'])
    causal=load('v1195_rebuild_'+name,R/'experiments/v1024_full_route_execution/causal.py');norm=load('v1195_prior_'+name,R/'experiments/v1037_periodic_norm_source/periodic_norm.py');e=causal.Evidence(x['setup']['known']);e.periodic=norm.PeriodicSupport()
    for s in clean:e.update(s)
    fresh=e.source(types.SimpleNamespace(count=k,d=types.SimpleNamespace(time=x['packet']['sim_time'])))
    assert fresh['source_native_tick']==x['source']['source_native_tick']and abs(fresh['source_age_s']-x['source']['source_age_s'])<=1e-9
    for a,b in zip(fresh['periodic']['vertices'],x['source']['periodic']['vertices']):assert np.array(a).shape==np.array(b).shape and abs(np.array(a)-b).max()<=1e-9
    with np.load(out/(name+'_TABLE.npz'))as z:t={n:z[n].copy()for n in z.files}
    domain=Domain(fresh['periodic']['vertices']);assert np.array_equal(domain.A,t['A'])and np.array_equal(domain.b,t['b'])
    dual=t['dual'];directions=np.array([[[nx,nx*np.sin(.32*time),nx*np.cos(.32*time),ny,ny*np.sin(.32*time),ny*np.cos(.32*time)]for nx,ny in NORMALS]for time in t['centers']]);res=directions-np.einsum('tnj,jk->tnk',dual,domain.A)
    upper=np.einsum('tnj,j->tn',dual,domain.b)+np.where(res>=0,res*domain.upper,res*domain.lower).sum(2)+1e-8+.08*((2*np.pi/.32/256)/2+.075)+2e-7;assert(dual>=0).all()and abs(upper-t['bounds']).max()<=1e-9
    return t
def audit(task,result_override=None,qualification_only=False,output_path=None,*,legacy_observer_only=False):
    out=Path(task['output']);r=result_override if result_override is not None else read(out/'RESULT.json');assert (r['passed']or r.get('functional_failure'))and r['error']is None
    # This immutable shared auditor reconstructs every native actuator allocation,
    # memory, contacts, sensor poses, initial scene and original normal segments.
    base=load('v1195_original_native_audit',R/'experiments/v1195_eight_gib_timed_refuge/audit_refusal.py');base.audit(task,result_override=result_override,output_path=(output_path.parent/'BASE_NATIVE_QUALIFICATION.json')if qualification_only else out/'BASE_NATIVE_AUDIT.json',require_replay=not qualification_only,final_packet_override=read(out/'LIVE_GOAL_INPUT.json')['packet']if qualification_only else None)
    setup=read(out/'physics/SETUP.json')
    with np.load(out/'physics/NATIVE_TRACE.npz')as z:trace={k:z[k].copy()for k in z.files}
    p0=read(out/'CANONICAL_INITIAL_PACKET.json');states=np.vstack([q.initial(p0)['state'],projection(trace['qpos'],trace['qvel'],setup)]);commands=np.array(read(out/'physics/BODY_COMMANDS.json'))
    with gzip.open(out/'physics/SENSORS.json.gz','rt')as f:sensors=json.load(f)
    x=read(out/'LIVE_OBSERVER_INPUT.json');start=x['packet']['native_tick'];assert start==r['recovery_origin_native']and abs(q.initial(x['packet'])['state']-states[start]).max()<=1e-8
    # Same-seed from-t0 prefix must equal the corresponding preserved failure;
    # the live owner is forbidden to read these historical raw arrays.
    if task['seed']in[10060001,10060002]:
        old=R/('runs/v858_nav2_verified/v1185/main_slot'+str(task['slot']).zfill(2))
        with np.load(old/'physics/NATIVE_TRACE.npz')as z:
            assert len(z['time'])==start
            for key in['qpos','qvel','ctrl','mocap_pos','mocap_quat','time']:assert trace[key][:start].shape==z[key].shape and (not z[key].size or abs(trace[key][:start]-z[key]).max()<=1e-8)
    if (r.get('functional_failure')or{}).get('reason')=='NO_CURRENT_STATE_OBSERVATION_REFUGE':
        assert len(trace['time'])==start
        table_check(out,'LIVE_OBSERVER',x,sensors)
        result=dict(passed=True,functional_passed=False,safety_evidence_only=True,native_reviewed=len(trace['time']),analytical_cpp_native=0,models=0,new_mujoco_native=0,reason='safe stopped current observation source refused')
        result.update(qualification_only=bool(qualification_only),actual_replay_verified=not qualification_only);dump(output_path or out/'FINAL_INDEPENDENT_AUDIT.json',result);return result
    table=table_check(out,'LIVE_OBSERVER',x,sensors);g=q.Geometry(x,table);chosen=read(out/'LIVE_OBSERVER_SELECTION.json');sel=chosen['selected'];assert sel['cut']in [11400,11800];rows=observer_source.candidate_rows(sel['turn'],sel['stage_native'],sel['cut']);assert rows==[tuple(row)for row in chosen['rows']]
    engine=q.accelerator.Engine(setup,q.model.parameters()['coefficients']);org=dict(q.initial(x['packet']),steering_load_episode=False);ss,uu,mm=engine.simulate(org,rows);pr,_=g.final(dict(x,goal=ss[-1,:2].tolist(),safe_terminal_pose=ss[-1,:3].tolist()),ss,uu,rows);assert pr['passed']
    with np.load(out/'LIVE_OBSERVER_REFERENCE.npz')as z:
        for name,a in[('states',ss),('controls',uu),('memory',mm)]:assert z[name].shape==a.shape and abs(z[name]-a).max()<=1e-8
    flags=stop_certificates.flags_before(rows);certs=read(out/'LIVE_OBSERVER_CERTIFICATES.json');offset=0;total=len(ss)-1
    for c in certs:
        assert c['offset']==offset and c['native']==start+offset
        p=c['packet'];assert abs(q.initial(p)['state']-states[start+offset]).max()<=1e-8 and c['steering_load_episode']==flags[offset]['steering_load_episode']
        assert p['coupled_episode']==flags[offset]['coupled_episode']and p['steering_motion_active']==flags[offset]['steering_motion_active']
        origin=dict(q.initial(p),steering_load_episode=bool(c['steering_load_episode']));block=bridge.front(bridge.remaining_rows(rows,offset),c['prefix']);proof,pred=stop_certificates.prove(engine,g,x,p,origin,block)
        for name,pr in zip(['current','prospective'],proof):assert pr['passed']and pr['states_sha256']==c[name]['states_sha256']and pr['controls_sha256']==c[name]['controls_sha256']
        n=c['prefix'];actual=states[start+offset:start+offset+n+1];d=actual-pred[1][:n+1];assert(np.c_[np.linalg.norm(d[:,:2],axis=1),abs(np.arctan2(np.sin(d[:,2]),np.cos(d[:,2]))),abs(d[:,6])]<=[.04,.035,.015]).all();offset+=n
    assert offset==total
    planned=np.array([[v,0. if mode or v==0. else v*math.tan(t)/.6,0.]for t,v,n,mode in rows for _ in range(int(n))]);assert abs(planned-commands[start:start+total][:,[1,2,5]]).max()<=1e-12
    d=states[start:start+total+1]-ss;assert(np.c_[np.linalg.norm(d[:,:2],axis=1),abs(np.arctan2(np.sin(d[:,2]),np.cos(d[:,2]))),abs(d[:,6])]<=[.04,.035,.015]).all()
    cursor=0
    for turn,speed,n,mode in rows:
        if mode:
            poses=states[start+cursor:start+cursor+n+1,:3];anchor=poses[0];assert g.cycle(anchor[None,:])[0]-.02-np.hypot(.44,.375)*.1>=q.REQUIRED and np.linalg.norm(poses[:,:2]-anchor[:2],axis=1).max()<=.02 and abs(np.arctan2(np.sin(poses[:,2]-anchor[2]),np.cos(poses[:,2]-anchor[2]))).max()<=.1
        cursor+=int(n)
    fresh=read(out/'LIVE_GOAL_INPUT.json');gs=fresh['packet']['native_tick'];assert gs==start+total and previous.stopped(fresh['packet'])and abs(q.initial(fresh['packet'])['state']-states[gs]).max()<=1e-8
    gt=table_check(out,'LIVE_GOAL',fresh,sensors)
    if legacy_observer_only:
        answer=dict(passed=True,scope='preserved actual native/observer only; new goal not executed',
            actual_replay_verified=not qualification_only,native_reviewed=len(trace['time']),
            observer_stop_certificates=len(certs),analytical_cpp_native=engine.native,
            models=0,new_mujoco_native=0,new_goal_physical_passed=False)
        dump(output_path or out/'OBSERVER_ONLY_AUDIT.json',answer);return answer
    bundle=load_bundle(out/'CURRENT_GOAL_ENTRY')
    final=read(out/'ACTUAL_FINAL_PACKET.json');applied=read(out/'APPLIED_JOURNAL.json')
    memory=np.asarray([row['last_ctrl']+[row['integral']]for row in applied[gs:]]+
        [final['controller_memory']['last_ctrl']+[final['controller_memory']['integral']]])
    external=dict(states=states[gs:],controls=trace['ctrl'][gs:,setup['actuator_ids']],
        memory=memory,requests=commands[gs:][:,[1,2,5]])
    goal=verify(fresh,gt,bundle,bool(flags[-1]['steering_load_episode']),external=external)
    assert r['passed'] and r['physical']['actual_travel_after_detection_m']>=1.
    assert np.linalg.norm(states[-1,:2]-task['goal_xy'])+.08<=.45
    answer=dict(passed=True,actual_replay_verified=not qualification_only,
        physical_audit_complete=not qualification_only,observer_stop_certificates=len(certs),
        goal=goal,native_reviewed=len(trace['time']),analytical_cpp_native=engine.native+goal['analytical_cpp_native'],
        models=0,new_mujoco_native=0,formal_retained_commit=False)
    dump(output_path or out/'FINAL_INDEPENDENT_AUDIT.json',answer);return answer
