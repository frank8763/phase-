"""Independent actual trace, control, causal capture and full-stop review."""
from response_tools import *
import math
import gzip
import signal
import numpy as np
from response_execution import initial,Adapter,Predictor,Engine,ref,REQUIRED,capture,stop_proof,stopped


def wrapped(x):return np.arctan2(np.sin(x),np.cos(x))


def project(q,v,setup):
    virtual_math=load('v1157_independent_virtual_math',R/'experiments/v1003_causal_recovery_execution/predictor.py')
    yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    front=q[:,setup['steering_qpos_addresses']];rate=v[:,setup['steering_qvel_addresses']]
    delta=np.array([virtual_math.virtual(x)for x in front])
    drate=np.array([virtual_math.virtual_rate(x,y)for x,y in zip(front,rate)])
    return np.c_[q[:,:2],yaw,v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw),
                  -v[:,0]*np.sin(yaw)+v[:,1]*np.cos(yaw),v[:,5],delta,drate]


def audit(task,save=True,synthetic=False,predictor_factory=Predictor):
    out=Path(task['output']);result=read(out/'RESULT.json');setup=read(out/'physics/SETUP.json')
    if synthetic:
        assert out.is_relative_to(O/'qualification_fixtures') and result.get('synthetic') is True,'SYNTHETIC_SCOPE'
    else:
        assert not result.get('synthetic',False),'SYNTHETIC_NOT_PHYSICAL'
        assert out.is_relative_to(R/'runs/v858_nav2_verified/v1157')
        assert sha(out/'physics/scene_model.mjb')==setup['model_sha256']
    journal=read(out/'REQUEST_JOURNAL.json');commands=np.asarray(read(out/'physics/BODY_COMMANDS.json'),float)
    original=read(out/'ACTUAL_INITIAL_PACKET.json');capture_record=read(out/'ACTUAL_CAPTURE_ORIGIN.json')
    capture_packet=capture_record['packet'];target=np.array(capture_record['target'])
    proofs=read(out/'MEASURED_STOP_CERTIFICATES.json')
    with np.load(out/'physics/NATIVE_TRACE.npz') as z:trace={k:z[k].copy()for k in z.files}
    with np.load(R/'runs/v1156_response_input_preparation/PLAN.npz') as z:nominal=z['states'].copy();fixed=z['requests'][:6400].copy()
    n=len(trace['time']);assert n==len(journal)==len(commands) and commands.shape==(n,6),'COMPLETE_RECORD_LENGTH'
    after=project(trace['qpos'],trace['qvel'],setup)
    states=np.vstack([np.array(initial(original)['state']),after])
    ctrl=trace['ctrl'][:,setup['actuator_ids']]
    assert np.isfinite(ctrl).all() and np.isfinite(states).all() and np.max(abs(trace['time']-(np.arange(n)+1)*.01))<=1e-8
    assert result['models']==1 and result['new_actual_native']==result['own_replay_native']==result['fully_recorded_actual_native']==n
    assert result['passed'] and result['normal_complete'] and result['error'] is None
    capture_count=result['capture_native'];assert type(capture_count) is int and 0<capture_count<=600 and n==8600+capture_count
    assert capture_packet['native_tick']==6400 and abs(capture_packet['sim_time']-64.)<=1e-8
    assert np.max(abs(np.array(initial(capture_packet)['state'])-states[6400]))<=1e-8 and stopped(capture_packet)
    expected_target=states[6400,:3].copy();expected_target[:2]+=.04*np.array([math.cos(expected_target[2]),math.sin(expected_target[2])])
    assert np.max(abs(target-expected_target))<=1e-12,'CAUSAL_CAPTURE_TARGET'
    rr=commands[:,[1,2,5]]
    assert np.array_equal(rr[:6400],fixed),'FIXED_PREFIX_REQUESTS'
    assert np.array_equal(rr[-2200:],np.zeros((2200,3))) and all(j['phase']=='capture_stop'for j in journal[-2200:])
    assert np.max(abs(np.array(capture_packet['controller_memory']['last_ctrl'])-ctrl[6399]))<=1e-10
    owner=Predictor(setup,initial(original)).adapter
    memory_error=0.;control_error=0.;packet_error=0.;response_max=np.zeros(3)
    p=predictor_factory(setup,initial(capture_packet));predicted=0
    geometry=ref._old.Geometry(setup['known'],None)
    for i,(command,row)in enumerate(zip(commands,journal)):
        assert row['before_native']==i and row['applied'] is True and np.array_equal(np.array(row['request'],float),rr[i]),'REQUEST_JOURNAL'
        expected_phase='initial_hold'if i<2200 else'changing_drive'if i<4200 else'drive_stop'if i<6400 else'capture'if i<6400+capture_count else'capture_stop'
        assert row['phase']==expected_phase,'STAGE_ORDER'
        before=row['packet'];assert before['native_tick']==i and abs(before['sim_time']-.01*i)<=1e-8
        state=np.array(initial(before)['state']);packet_error=max(packet_error,float(abs(state-states[i]).max()))
        assert packet_error<=1e-8,'MEASURED_STATE_BINDING'
        assert max(abs(command[3]-states[i,3]),abs(command[4]-states[i,5]))<=1e-8,'MEASURED_SPEED_BINDING'
        memory_error=max(memory_error,float(abs(owner.last-row['last_ctrl']).max()),abs(owner.integral-row['integral']))
        assert np.max(abs(np.asarray(before['controller_memory']['last_ctrl'])-row['last_ctrl']))<=1e-10 and abs(before['controller_memory']['integral']-row['integral'])<=1e-10
        u=owner.compute(float(command[1]),float(command[2]),float(command[3]),float(command[4]),bool(command[5]))
        control_error=max(control_error,float(abs(u-ctrl[i]).max()))
        if i<6400:expected=nominal[i+1]
        else:
            if i<6400+capture_count:
                v,w,status=capture.request(states[i],target)
                assert status=='CAPTURING' and np.max(abs(rr[i]-[v,w,0.]))<=1e-12,'CAUSAL_CAPTURE_REQUEST'
            elif i==6400+capture_count:assert capture.request(states[i],target)[2]=='CAPTURED','CAPTURE_TERMINATION'
            expected,_=p.step(float(command[1]),float(command[2]),bool(command[5]));predicted+=1
        delta=states[i+1]-expected
        response_max=np.maximum(response_max,[np.linalg.norm(delta[:2]),abs(wrapped(delta[2])),abs(delta[6])])
    assert max(memory_error,control_error)<=1e-10,'ACTUAL_CONTROLLER_RECONSTRUCTION'
    assert (response_max<=[.04,.035,.015]).all(),'ACTUAL_RESPONSE'
    assert np.max(abs(np.asarray(capture_packet['controller_memory']['last_ctrl'])-journal[6400]['last_ctrl']))<=1e-10
    assert abs(capture_packet['controller_memory']['integral']-journal[6400]['integral'])<=1e-10
    position=float(np.linalg.norm(states[-1,:2]-target[:2]));yaw=float(abs(wrapped(states[-1,2]-target[2])))
    assert position<=.025 and yaw<=.1 and abs(states[-50:,3:6]).max()<=.003 and abs(states[-50:,7]).max()<=.015
    limits=np.array(setup['limits']);rate=np.array(setup['slew_per_second'])*.01
    assert (ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()
    assert (abs(np.diff(np.vstack([original['controller_memory']['last_ctrl'],ctrl]),axis=0))<=rate+1e-10).all()
    assert (abs(states[:,3:6])<=[.13,.03,.16]).all()
    raw=float(geometry.clearances(after[:,:3])[0].min())
    assert raw>=.15-1e-8 and float(trace['clearance'].min())>=.15-1e-8 and float(trace['self_margin'].min())>=-1e-10
    physical=result['physical'];assert physical['bad_contacts']==0 and physical['root_guard_native_count']==n and physical['fully_recorded_native']==n
    assert result['replay']['passed'] and result['replay']['replay_native']==n and result['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and result['replay']['contact_mismatched_ticks']==0
    contacts=read_gzip(out/'physics/CONTACTS.json.gz');sensors=read_gzip(out/'physics/SENSORS.json.gz')
    assert len(contacts)==n+1 and physical['first_actor_detection'] is None
    assert [x['native_tick'] for x in sensors]==[0,0]+list(range(0,n+1,5)),'SENSOR_TICK_COVERAGE'
    assert sensors[0]==sensors[1] and sensors[1]==sensors[2],'T0_SENSOR_BINDING'
    for scan in sensors:
        i=scan['native_tick'];assert abs(scan['time']-.01*i)<=1e-8 and np.max(abs(np.asarray(scan['xy'])-states[i,:2]))<=1e-8
        assert abs(wrapped(scan['yaw']-states[i,2]))<=1e-6 and len(scan['ranges'])==32 and np.isfinite(scan['ranges']).all()
    required=list(range(0,n,8))
    actual_ticks=[row['packet']['native_tick'] for row in proofs]
    assert set(required).issubset(actual_ticks) and 6400 in actual_ticks and 6400+capture_count in actual_ticks,'FULL_STOP_COVERAGE'
    review_engine=Engine(setup)if not synthetic else None
    for row in proofs:
        packet=row['packet'];i=packet['native_tick']
        assert 0<=i<n and row['passed'] is True and all(row['checks'].values()) and row['analytic_native']==2200
        assert np.max(abs(np.array(initial(packet)['state'])-states[i]))<=1e-8,'STOP_MEASURED_BINDING'
        assert abs(packet['sim_time']-.01*i)<=1e-8
        assert np.max(abs(np.asarray(packet['controller_memory']['last_ctrl'])-journal[i]['last_ctrl']))<=1e-10 and abs(packet['controller_memory']['integral']-journal[i]['integral'])<=1e-10,'STOP_MEMORY_BINDING'
        if not synthetic:
            ss,uu=review_engine.simulate(initial(packet),[(0.,0.,2200,0)])
            independent=stop_proof(setup,packet,ss,uu,geometry)
            assert independent['passed'] and abs(independent['minimum_raw_m']-row['minimum_raw_m'])<=1e-10
    proof=dict(passed=True,synthetic_qualification=synthetic,physical_native=n if not synthetic else 0,
        models=0,new_mujoco_integrations=0,analytical_python_native=predicted if not synthetic else 0,
        analytical_cpp_native=review_engine.native if review_engine else 0,
        response_max=response_max,controller_max_error=control_error,memory_max_error=memory_error,
        packet_max_error=packet_error,minimum_raw_actual_m=raw,capture_native=capture_count,
        capture_position_error_m=position,capture_heading_error_rad=yaw,complete_stop_certificates=len(proofs),
        independent_complete_stops_recomputed=not synthetic,whole_route_passed=False,new24=False)
    if save:dump(out/'FINAL_INDEPENDENT_AUDIT.json',proof)
    return proof


def read_gzip(path):
    with gzip.open(path,'rt')as f:return json.load(f)


if __name__=='__main__':
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('AUDIT_120S')))
    signal.setitimer(signal.ITIMER_REAL,120)
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
    import fcntl
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    proof=audit(read(Path(sys.argv[1])));print(encode(proof))
