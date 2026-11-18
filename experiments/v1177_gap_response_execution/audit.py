"""Actual state/control/sensor/contact/stop certificates; offline4core only."""
from gap_tools import *
import fcntl,gzip,signal,math
from gap_execution import proof,stopped
old_audit=load('v1177_old_state_projection',R/'experiments/v1157_response_execution/audit.py')
def read_gz(p):
    with gzip.open(p,'rt')as f:return json.load(f)
def audit(task,save=True,synthetic=False,review_stops=True):
    out=Path(task['output']);result=read(out/'RESULT.json');setup=read(out/'physics/SETUP.json');journal=read(out/'REQUEST_JOURNAL.json');initial_packet=read(out/'ACTUAL_INITIAL_PACKET.json');certs=read(out/'MEASURED_STOP_CERTIFICATES.json');commands=np.array(read(out/'physics/BODY_COMMANDS.json'),float);plan=plan_for(task)
    if synthetic:assert result.get('synthetic')is True and out.is_relative_to(O/'qualification')
    else:
        fixture,contract=task_contract(task);contract.validate_actual(task,fixture,setup,sha(out/'physics/scene_model.mjb'));assert not result.get('synthetic',False)
    with np.load(out/'physics/NATIVE_TRACE.npz')as z:t={k:z[k].copy()for k in z.files}
    n=len(t['time']);assert n==len(journal)==len(commands)==result['new_actual_native']==result['own_replay_native']==result['fully_recorded_actual_native']
    assert result['error']is None and result['replay']['passed']and result['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and result['replay']['contact_mismatched_ticks']==0
    ss=np.vstack([origin(initial_packet)['state'],old_audit.project(t['qpos'],t['qvel'],setup)]);uu=t['ctrl'][:,setup['actuator_ids']];rr=commands[:,[1,2,5]]
    assert np.isfinite(ss).all()and np.isfinite(uu).all()and abs(t['time']-.01*np.arange(1,n+1)).max()<=1e-8
    if result['normal_complete']:assert n==task['planned_native']and np.array_equal(rr,plan['requests'])
    else:
        assert result.get('functional_failure')and n>=2200 and np.array_equal(rr[-2200:],np.zeros((2200,3)))
        k=n-2200;assert np.array_equal(rr[:k],plan['requests'][:k])and all(j['phase']=='functional_stop'for j in journal[-2200:])
    owner=q.model.Predictor(setup,origin(initial_packet)).adapter;loaded=False;maximum=np.zeros(3);memoryerr=0.;controlerr=0.;packeterr=0.
    for i,row in enumerate(journal):
        assert row['before_native']==i and row['applied']and np.array_equal(row['request'],rr[i])
        packet=row['packet'];assert packet['native_tick']==i and abs(packet['sim_time']-.01*i)<=1e-8 and packet['steering_load_episode']is loaded
        packeterr=max(packeterr,float(abs(np.array(origin(packet)['state'])-ss[i]).max()));assert packeterr<=1e-8
        assert max(abs(commands[i,3]-ss[i,3]),abs(commands[i,4]-ss[i,5]))<=1e-8
        memoryerr=max(memoryerr,float(abs(owner.last-row['last_ctrl']).max()),abs(owner.integral-row['integral']))
        assert np.array_equal(row['last_ctrl'],packet['controller_memory']['last_ctrl'])and row['integral']==packet['controller_memory']['integral']
        u=owner.compute(*map(float,rr[i,:2]),ss[i,3],ss[i,5],bool(rr[i,2]));controlerr=max(controlerr,float(abs(u-uu[i]).max()))
        if rr[i,0]>=.005:loaded=True
        if row['phase']=='fixed_input':
            d=ss[i+1]-plan['states'][i+1];e=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2]))),abs(d[6])]);maximum=np.maximum(maximum,e)
            assert abs(e-row['response_error']).max()<=1e-10
    assert max(memoryerr,controlerr)<=1e-10
    if result['passed']:assert(maximum<=[.04,.035,.015]).all()and result['normal_complete']
    lim=np.array(setup['limits']);rate=np.array(setup['slew_per_second'])*.01
    assert (uu>=lim[:,0]-1e-10).all()and(uu<=lim[:,1]+1e-10).all()and(abs(np.diff(np.vstack([initial_packet['controller_memory']['last_ctrl'],uu]),axis=0))<=rate+1e-10).all()
    assert(abs(ss[:,3:6])<=[.13,.03,.16]).all()and abs(ss[-50:,3:6]).max()<=.003 and abs(ss[-50:,7]).max()<=.015
    geometry=old_audit.ref._old.Geometry(setup['known'],None);raw=float(geometry.clearances(ss[1:,:3])[0].min());assert raw>=.15-1e-8 and t['clearance'].min()>=.15-1e-8 and t['self_margin'].min()>=-1e-10
    physical=result['physical'];assert physical['bad_contacts']==0 and physical['root_guard_native_count']==n and physical['fully_recorded_native']==n and physical['first_actor_detection']is None
    contacts=read_gz(out/'physics/CONTACTS.json.gz');sensors=read_gz(out/'physics/SENSORS.json.gz');assert len(contacts)==n+1
    assert [s['native_tick']for s in sensors]==[0,0]+list(range(0,n+1,5))and sensors[0]==sensors[1]==sensors[2]
    for s in sensors:
        k=s['native_tick'];assert abs(s['time']-.01*k)<=1e-8 and abs(np.array(s['xy'])-ss[k,:2]).max()<=1e-8 and abs(math.atan2(math.sin(s['yaw']-ss[k,2]),math.cos(s['yaw']-ss[k,2])))<=1e-6
        assert len(s['ranges'])==32 and np.isfinite(s['ranges']).all()
    assert set(range(0,n,8)).issubset({c['packet']['native_tick']for c in certs})
    jobs=[]
    for j,c in enumerate(certs):
        packet=c['packet'];k=packet['native_tick'];assert c['passed']and c['analytic_native']==2200 and all(c['checks'].values())and 0<=k<n
        assert abs(np.array(origin(packet)['state'])-ss[k]).max()<=1e-8 and abs(np.array(packet['controller_memory']['last_ctrl'])-journal[k]['last_ctrl']).max()<=1e-10 and abs(packet['controller_memory']['integral']-journal[k]['integral'])<=1e-10
        jobs.append(dict(id=j,plan=task['component'],offset=k,origin=origin(packet)))
    parallel_count=0
    if review_stops and not synthetic:
        sys.path.insert(0,str(R/'experiments/v1176_multicore_stop_backend'))
        import backend
        assert Path(backend.__file__).resolve()==R/'experiments/v1176_multicore_stop_backend/backend.py','WRONG_PARALLEL_BACKEND'
        # V1176 fixed backend setup equals the exact original NS fixture. Assert
        # this explicitly before using it on actual measured states.
        assert setup==read(R/'runs/v1173_rate_preconditioned_input/INPUTS.json')['setup']
        rows,timing=backend.parallel(jobs,read(C/'SOURCE_FREEZE.json')['files'])
        for row,old in zip(rows,certs,strict=True):assert row['passed']and abs(row['minimum_raw']-old['minimum_raw'])<=1e-10
        parallel_count=len(rows)*2200;dump(out/'PARALLEL_STOP_AUDIT_TIMING.json',timing)
    result=dict(passed=True,functional_component_passed=bool(result['passed']),synthetic_qualification=synthetic,actual_native_reviewed=n if not synthetic else 0,models=0,new_mujoco_integrations=0,analytical_cpp_native=parallel_count,analytical_python_native=0,maximum_response_error=maximum,controller_error=controlerr,memory_error=memoryerr,packet_error=packeterr,minimum_actual_raw=raw,complete_stop_certificates=len(certs),multicore_review_used=bool(review_stops and not synthetic),no_dynamic_arrival_claim=True)
    if save:dump(out/'FINAL_INDEPENDENT_AUDIT.json',result)
    return result
if __name__=='__main__':
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('GAP_RESPONSE_AUDIT_180S')));signal.setitimer(signal.ITIMER_REAL,180)
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    r=audit(read(Path(sys.argv[1])));print(json.dumps({k:v for k,v in r.items()if k in ['passed','functional_component_passed','actual_native_reviewed','analytical_cpp_native']}))
