"""Wall-paced native backend. Policy input consists only of odometry and noisy scan."""
import fcntl,json,os,signal,socket,sys,time,traceback
from pathlib import Path
from physics_backend import Vehicle,R,C
from instrumentation import dump
OUT=R/'runs/v856_nav2_foundation';END=1794052800.
def main():
    task=json.loads(Path(sys.argv[1]).read_text());out=Path(task['output']);os.chdir(R)
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{sorted(os.sched_getaffinity(0))[3]})
    address='runs/v856_nav2_foundation/p.sock';peer='runs/v856_nav2_foundation/r.sock';assert not Path(address).exists(),'STALE_PHYSICS_SOCKET'
    s=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);s.bind(address);s.setblocking(False)
    vehicle=None;status='ENTRY_INCOMPLETE';result=dict(passed=False,environment_initializations_attempted=1,actual_native=0,replay_native=0,private_native=0);stale_ticks=0;maximum_lag=0.;last_packet=None;stop_at=None;reason=None;latest=None
    try:
        vehicle=Vehicle(out/'physics',task['case_id'],task['seed'],task['dynamic']);start=time.monotonic();k=0;status='RUNNING'
        while time.monotonic()-start<task['wall_limit_s']+2 and time.time()<END-20:
            now=time.monotonic()
            while True:
                try:latest=json.loads(s.recv(65536))
                except BlockingIOError:break
            if latest and latest.get('stop') and stop_at is None:stop_at=now;reason=latest['reason']
            if (out/'STOP.json').exists()and stop_at is None:stop_at=now;reason=json.loads((out/'STOP.json').read_text()).get('reason','ROS_STOP')
            if now-start>=task['wall_limit_s'] and stop_at is None:stop_at=now;reason='NAVIGATION_600S_WALL_STOP'
            if stop_at is not None and now-stop_at>=2:break
            target=start+k*.01;time.sleep(max(0.,target-time.monotonic()));now=time.monotonic();lag=now-target;maximum_lag=max(maximum_lag,lag)
            assert lag<=.1,'PHYSICS_WALL_LAG_OVER_100MS'
            stale=latest is None or now-latest.get('wall_monotonic',-1)>.2 or stop_at is not None;stale_ticks+=int(stale)
            v,w=(0.,0.)if stale else(latest.get('v',0.),latest.get('w',0.));vehicle.step(v,w,stale)
            if k%5==0:last_packet=vehicle.scan()
            packet=dict(native_tick=vehicle.count,sim_time=float(vehicle.d.time),wall_monotonic=time.monotonic(),body=vehicle.body(),scan=last_packet)
            try:s.sendto(json.dumps(packet).encode(),peer)
            except (FileNotFoundError,ConnectionRefusedError,BlockingIOError):pass
            if k%100==0:
                tmp=out/'PARTIAL.tmp';tmp.write_text(json.dumps(dict(status=status,native_tick=vehicle.count,sim_time=float(vehicle.d.time),body=vehicle.body(),goal_distance_m=float(__import__('numpy').linalg.norm(vehicle.d.qpos[:2]-vehicle.case['goal_xy'])),wall_elapsed_s=now-start,maximum_wall_lag_s=maximum_lag)));tmp.replace(out/'PARTIAL.json')
            k+=1
        else:reason=reason or'ROOT_OR_NAVIGATION_WALL_STOP'
        result.update(vehicle.finish(),maximum_wall_lag_s=maximum_lag,stale_command_ticks=stale_ticks,stop_reason=reason,wall_paced=True);replay=vehicle.replay();result.update(replay=replay,replay_native=replay['replay_native']);status='NATIVE_COMPLETE'
        ros=json.loads((out/'ROS_RESULT.json').read_text())if(out/'ROS_RESULT.json').exists()else{}
        result['passed']=ros.get('action_status')==4 and result['goal_distance_m']<=.45 and replay['passed'] and result['bad_contacts']==0
        result['ros_action']=ros
    except BaseException as e:
        status='PHYSICAL_OR_EVIDENCE_EXCEPTION';result.update(error=repr(e),traceback=traceback.format_exc(),stop_reason=status)
        if vehicle:
            result.update(vehicle.finish());result['actual_native']=vehicle.count;result['fully_recorded_native']=len(vehicle.rows)
    finally:
        s.close();Path(address).unlink(missing_ok=True);result.update(status=status,closed=True)
        dump((out if out.exists()else OUT)/('RESULT.json'if out.exists()else'NATIVE_ENTRY_ERROR.json'),result);print(json.dumps(result),flush=True)
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
