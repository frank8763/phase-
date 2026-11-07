"""Future one-task native executor. Vehicle import is below the authority check."""
import fcntl,json,os,signal,socket,sys,time,traceback
from pathlib import Path
from handshake import Startup,authorized,policy_packet,file_sha,require,verify_sources
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
def dump(path,data):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');temporary.replace(path)
def send(sock,data,peer):
    try:sock.sendto(json.dumps(data,allow_nan=False).encode(),peer)
    except (FileNotFoundError,ConnectionRefusedError,BlockingIOError):pass
def run(task,receipt,freeze_sha):
    deadline=authorized(task,receipt,time.time(),freeze_sha)
    verify_sources(R,C/'SOURCE_FREEZE.json')
    # Deliberately placed after authority validation, also checked by zero-model tests.
    from physical import create_vehicle,replay
    out=Path(task['output']);require(out.resolve().is_relative_to(R/'runs/v858_nav2_verified'),'OUTPUT_SCOPE')
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cpus=sorted(os.sched_getaffinity(0));require(len(cpus)>=4,'FOUR_CPU_PARTITION_REQUIRED');os.sched_setaffinity(0,{cpus[3]})
    os.chdir(R);sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
    address=str(Path(task['socket_dir'])/'physics.sock');peer=str(Path(task['socket_dir'])/'ros.sock')
    require(not Path(address).exists(),'STALE_PHYSICS_SOCKET');sock.bind(address);sock.setblocking(False)
    session=Startup(task['run_id']);vehicle=None;started=time.monotonic();snapshot=None;measured_at=None;stop_at=None
    result=dict(passed=False,actual_native=None,replay_native=0,private_native=0,environment_initialization_attempted=False)
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('ABSOLUTE_MODEL_DEADLINE')))
    signal.setitimer(signal.ITIMER_REAL,max(.001,deadline-5-time.time()));status='INITIALIZING'
    try:
        result['environment_initialization_attempted']=True;vehicle=create_vehicle(out/'physics',task)
        result['environment_initialization_completed']=True;require(vehicle.count==0 and vehicle.d.time==0.,'T0_ALREADY_ADVANCED')
        snapshot=vehicle.scan();measured_at=time.monotonic();last_sent=0.;status='WAITING_READY'
        while session.phase=='WAITING':
            now=time.monotonic();require(now-started<35 and time.time()<deadline-30,'STARTUP_35S_DEADLINE')
            for _ in range(64):
                try:packet=json.loads(sock.recv(65536))
                except BlockingIOError:break
                session.receive(packet,now,vehicle.count,float(vehicle.d.time))
            if now-last_sent>=.02:
                send(sock,policy_packet(task['run_id'],vehicle,snapshot,measured_at,now,session.phase),peer);last_sent=now
            time.sleep(.002)
        if session.armed_at is None:
            status='PREARM_ABORT';result.update(vehicle.finish());return result
        status='RUNNING';k=0;maximum_lag=0.;stale_ticks=0;reason='UNKNOWN'
        while True:
            now=time.monotonic()
            for _ in range(64):
                try:packet=json.loads(sock.recv(65536))
                except BlockingIOError:break
                session.receive(packet,now,vehicle.count,float(vehicle.d.time))
            if session.phase=='STOPPING'and stop_at is None:stop_at=now;reason='ROS_STOP'
            if now-session.armed_at>=task['wall_limit_s']or time.time()>=deadline-25:
                if stop_at is None:stop_at=now;reason='AUTHORIZED_NAVIGATION_OR_ROOT_DEADLINE';session.phase='STOPPING'
            if stop_at is not None and now-stop_at>=task['brake_s']:break
            target=session.armed_at+k*.01;time.sleep(max(0.,target-time.monotonic()));now=time.monotonic()
            maximum_lag=max(maximum_lag,now-target);require(maximum_lag<=.1,'PHYSICS_WALL_LAG_OVER_100MS')
            stale_ticks+=int(session.controls(now)[2]);session.step(vehicle,now)
            if k%5==0:snapshot=vehicle.scan();measured_at=time.monotonic()
            send(sock,policy_packet(task['run_id'],vehicle,snapshot,measured_at,time.monotonic(),session.phase),peer)
            if k%100==0:dump(out/'PARTIAL.json',dict(status=status,actual_native=vehicle.count,sim_time=float(vehicle.d.time),body=list(vehicle.body()),armed_at=session.armed_at,maximum_wall_lag_s=maximum_lag))
            k+=1
        result.update(vehicle.finish(),maximum_wall_lag_s=maximum_lag,stale_command_ticks=stale_ticks,stop_reason=reason)
        comparison=replay(vehicle,deadline,out/'physics');result.update(replay=comparison,replay_native=comparison['replay_native'])
        ros=json.loads((out/'ROS_RESULT.json').read_text())if(out/'ROS_RESULT.json').exists()else{}
        result['ros_action']=ros;result['passed']=bool(ros.get('action_status')==4 and result['goal_distance_m']<=.45 and result['final_translation_speed_m_s']<=.03 and comparison['passed']and result['bad_contacts']==0)
        status='NATIVE_COMPLETE'
    except BaseException as e:
        status='PHYSICAL_OR_EVIDENCE_EXCEPTION';result.update(error=repr(e),traceback=traceback.format_exc())
        if vehicle:result.update(vehicle.finish())
        if vehicle and vehicle.count>0 and not result.get('replay'):result['replay_native']=None;result['replay_count_status']='UNKNOWN_OR_NOT_COMPLETED_SEE_PROGRESS'
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);sock.close();Path(address).unlink(missing_ok=True)
        result.update(status=status,closed=True,startup_events=session.events,armed_at=session.armed_at)
        dump(out/'RESULT.json',result)
    return result
def main():
    task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text())
    result=run(task,receipt,file_sha(C/'SOURCE_FREEZE.json'));return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
