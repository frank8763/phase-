"""Authorized true dynamic t0 query; prohibit any native integration during preparation."""
import fcntl,json,os,signal,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v897_refuge_navigation'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from authority import authorized
from handshake import file_sha,verify_sources,require
from packet_contract import policy_packet
def run(task,receipt,freeze_sha):
    deadline=authorized(task,receipt,time.time(),freeze_sha);verify_sources(R,C/'SOURCE_FREEZE.json')
    require(task['role']=='dynamic_t0'and task['task_id']in {'t0_we','t0_ns','t0_ew'},'ONLY_REGISTERED_T0_QUERY')
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cpus=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpus[3]})
    out=Path(task['output']);require(not out.exists(),'T0_ALREADY_ATTEMPTED');out.mkdir(parents=True)
    result=dict(passed=False,environment_initializations_attempted=1,environment_initializations_completed=0,native_integrations=0,internal_factory_compile_or_load_count='NOT_SEPARATELY_INSTRUMENTED')
    previous=sys.getprofile();attempted=[]
    def prohibit(frame,event,arg):
        if event=='c_call'and getattr(arg,'__name__','')in ['mj_step','mj_step1','mj_step2']:
            attempted.append(getattr(arg,'__name__'));raise RuntimeError('INTEGRATION_DURING_T0_QUERY')
    def alarm(*_):raise TimeoutError('ABSOLUTE_T0_DEADLINE')
    signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,max(.001,min(85,deadline-10-time.time())))
    try:
        sys.path.insert(0,str(C))  # Explicit lazy dynamic adapter, after authorization.
        from physical import create_vehicle
        sys.setprofile(prohibit);v=create_vehicle(out/'physics',task);result['environment_initializations_completed']=1
        packet=v.scan();require(v.count==0 and v.d.time==0.,'T0_ALREADY_ADVANCED')
        require(v.actor is not None and v.m.nmocap==1,'SINGLE_ACTOR_REQUIRED')
        a=v.actor.config
        require(a['radius_m']==.1 and a['amplitude_m']==.25 and a['maximum_speed_m_s']==.08 and a['phase_rad']==task['phase'],'ORIGINAL_ACTOR_CHANGED')
        require(v.first_detection is None and len(packet['ranges'])==32,'UNSEEN_ORIGINAL_RANGE_T0_REQUIRED')
        require(v.bad==0 and v.min_clear>=.15 and v.min_self>=-1e-10,'T0_SAFETY_FAILED')
        wire=policy_packet(task['run_id'],v,packet,time.monotonic(),time.monotonic(),'WAITING')
        require(set(wire['scan'])=={'native_tick','time','ranges','xy','yaw'}and not any(k in wire for k in ['actor','raw_lidar','actor_xy']),'TRUTH_LEAK')
        result.update(passed=True,initial_body=v.body(),minimum_clearance_m=v.min_clear,bad_contacts=v.bad,actor=a,model_sha256=file_sha(out/'physics/scene_model.mjb'),native_count=v.count,initial_time=float(v.d.time),policy_packet_keys=list(wire),scan_packet_keys=list(wire['scan']))
    except BaseException as e:result.update(passed=False,error=repr(e),traceback=traceback.format_exc())
    finally:
        sys.setprofile(previous);signal.setitimer(signal.ITIMER_REAL,0)
        result['prohibited_native_calls_attempted']=attempted
        (out/'PREFLIGHT_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
if __name__=='__main__':
    task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text())
    result=run(task,receipt,file_sha(C/'SOURCE_FREEZE.json'));print(json.dumps(result),flush=True);sys.exit(0 if result['passed']else 1)
