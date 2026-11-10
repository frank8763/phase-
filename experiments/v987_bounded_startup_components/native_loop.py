"""Same100Hz model/control seam, explicit timing and bounded failed-prefix evidence closure."""
import fcntl,gzip,json,math,os,signal,socket,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static'),str(R/'experiments/v882_runtime_evidence_repair')]
from handshake import Startup,policy_packet,file_sha,require,verify_sources
from authority import authorized
from runtime_timing import Timing,CyclicGCWindow
from closure import dump,stop_requested,accounting_receipt

def send(sock,data,peer):
    try:sock.sendto(json.dumps(data,allow_nan=False).encode(),peer)
    except (FileNotFoundError,ConnectionRefusedError,BlockingIOError):pass

def attach_vehicle_timers(vehicle,timing):
    originals=[]
    timing.native_completed=0;timing.native_integration_uncertain=False;timing.native_observed=hasattr(vehicle,'native')
    for name in ['native','check']:
        if not hasattr(vehicle,name):continue
        original=getattr(vehicle,name)
        def call(*args,_f=original,_label='vehicle.'+name,**kwargs):
            if _label!='vehicle.native':return timing.call(_label,vehicle.count,_f,*args,**kwargs)
            stamp=timing.begin()
            try:
                value=_f(*args,**kwargs);timing.native_completed+=1;return value
            except BaseException:
                # A C-call interrupted before returning may have advanced partially.
                timing.native_integration_uncertain=True;raise
            finally:timing.end(_label,vehicle.count,stamp)
        originals.append((vehicle,name,original));setattr(vehicle,name,call)
    if hasattr(vehicle,'geometry')and hasattr(vehicle.geometry,'actual'):
        original=vehicle.geometry.actual
        def geometry(*args,**kwargs):return timing.call('vehicle.full_geometry',vehicle.count,original,*args,**kwargs)
        originals.append((vehicle.geometry,'actual',original));vehicle.geometry.actual=geometry
    return originals

def run(task,receipt,freeze_sha):
    deadline=authorized(task,receipt,time.time(),freeze_sha);verify_sources(R,C/'SOURCE_FREEZE.json')
    from budget import load as load_task_clock,model_deadline,alarm_seconds,check_restore
    task_clock=load_task_clock(task['output'],task,deadline);root_deadline=deadline;deadline=model_deadline(task_clock)
    # Future real vehicle imports remain strictly below authority validation.
    sys.path.insert(0,str(C))
    from physical import create_vehicle,replay
    out=Path(task['output']);require(out.resolve().is_relative_to(R/'runs/v858_nav2_verified'),'OUTPUT_SCOPE')
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cpus=sorted(os.sched_getaffinity(0));require(len(cpus)>=4,'FOUR_CPU_PARTITION_REQUIRED');os.sched_setaffinity(0,{cpus[3]})
    os.chdir(R);sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);address=str(Path(task['socket_dir'])/'physics.sock');peer=str(Path(task['socket_dir'])/'ros.sock');require(not Path(address).exists(),'STALE_PHYSICS_SOCKET');sock.bind(address);sock.setblocking(False)
    timing=Timing(math.ceil((task['wall_limit_s']+task['brake_s']+2)*100),wall=time.monotonic)
    session=Startup(task['run_id']);session._journals();vehicle=None;started=time.monotonic();snapshot=None;measured_at=None;stop_at=None;original_methods=[];gc_window=CyclicGCWindow();secondary=[]
    result=dict(passed=False,actual_native=None,replay_native=0,private_native=0,environment_initialization_attempted=False,maximum_wall_lag_s=0.,root_deadline_unix=root_deadline,task_clock=task_clock)
    def alarm(*_):raise TimeoutError('ABSOLUTE_MODEL_DEADLINE')
    def terminate(*_):raise InterruptedError('EXTERNAL_TERMINATION_STOP_NO_NAVIGATION_RESTART')
    old_term=signal.signal(signal.SIGTERM,terminate);signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,alarm_seconds(task_clock));status='INITIALIZING'
    try:
        result['environment_initialization_attempted']=True;vehicle=timing.call('factory_initialize',0,create_vehicle,out/'physics',task);result['environment_initialization_completed']=True;require(vehicle.count==task.get('origin_native_tick',0) and abs(vehicle.d.time-task.get('origin_sim_time',0.))<=1e-9,'CANONICAL_ORIGIN_ALREADY_ADVANCED')
        original_methods=attach_vehicle_timers(vehicle,timing);snapshot=vehicle.component_snapshot if task.get('origin_native_tick',0) else timing.call('scan',vehicle.count,vehicle.scan);measured_at=time.monotonic();last_sent=0.;status='WAITING_READY'
        # This candidate removes cyclic-GC pauses only; OS/GPU/IO delays are not claimed fixed.
        timing.call('prearm_gc_prepare',0,gc_window.enter)
        check_restore(task_clock,out,task['run_id'])
        startup_ready_at=time.monotonic()
        dump(out/'NATIVE_READY.json',dict(native_tick=vehicle.count,sim_time=float(vehicle.d.time),at=startup_ready_at,origin_validated=True))
        while session.phase=='WAITING':
            now=time.monotonic();require(now-startup_ready_at<35 and time.time()<deadline-30,'STARTUP_35S_DEADLINE')
            parent_stop=stop_requested(out,task['run_id'])
            if parent_stop is not None:
                session.receive(dict(kind='stop',run_id=task['run_id'],issued_at=now,reason=parent_stop['reason']),now,vehicle.count,float(vehicle.d.time))
                break
            for _ in range(64):
                try:packet=json.loads(sock.recv(65536))
                except BlockingIOError:break
                session.receive(packet,time.monotonic(),vehicle.count,float(vehicle.d.time))
            if now-last_sent>=.02 and session.phase=='WAITING':send(sock,policy_packet(task['run_id'],vehicle,snapshot,measured_at,now,session.phase),peer);last_sent=now
            time.sleep(.002)
        if session.armed_at is None:status='PREARM_ABORT'
        else:
            status='RUNNING';k=0;stale_ticks=0;reason='UNKNOWN'
            if task.get('origin_native_tick',0):measured_at=session.armed_at-(float(vehicle.d.time)-snapshot['time'])
            while True:
                stamp=timing.begin();now=time.monotonic()
                try:
                    for _ in range(64):
                        try:packet=json.loads(sock.recv(65536))
                        except BlockingIOError:break
                        session.receive(packet,time.monotonic(),vehicle.count,float(vehicle.d.time))
                finally:timing.end('receive',vehicle.count,stamp)
                parent_stop=stop_requested(out,task['run_id'])
                if parent_stop is not None and session.phase!='STOPPING':
                    session.receive(dict(kind='stop',run_id=task['run_id'],issued_at=now,reason=parent_stop['reason']),now,vehicle.count,float(vehicle.d.time))
                    session.events.append(dict(event='PARENT_STOP_FILE',native_tick=vehicle.count,reason=parent_stop['reason']))
                if session.phase=='STOPPING'and stop_at is None:stop_at=now;reason='ROS_STOP'
                if now-session.armed_at>=task['wall_limit_s']or time.time()>=deadline-25:
                    if stop_at is None:
                        stop_at=now;reason='AUTHORIZED_NAVIGATION_OR_ROOT_DEADLINE';session.phase='STOPPING';session.events.append(dict(event='LOCAL_DEADLINE_STOP',at=now,native_tick=vehicle.count,wall_limit_s=task['wall_limit_s']))
                if stop_at is not None and now-stop_at>=task['brake_s']:break
                target=session.armed_at+k*.01;timing.call('pacing_wait',vehicle.count,time.sleep,max(0.,target-time.monotonic()));now=time.monotonic();timing.lag(vehicle.count,target,now)
                # Original100ms gate and original absolute100Hz schedule remain unchanged.
                result['maximum_wall_lag_s']=timing.maximum_lag_s;require(timing.maximum_lag_s<=.1,'PHYSICS_WALL_LAG_OVER_100MS')
                stale_ticks+=int(session.controls(now)[2]);timing.call('step_and_native_safety',vehicle.count,session.step,vehicle,now)
                if vehicle.count%5==1:snapshot=timing.call('scan',vehicle.count,vehicle.scan);measured_at=time.monotonic()
                timing.call('observation_send',vehicle.count,send,sock,policy_packet(task['run_id'],vehicle,snapshot,measured_at,time.monotonic(),session.phase),peer)
                if k%100==0:timing.call('partial_write',vehicle.count,dump,out/'PARTIAL.json',dict(status=status,actual_native=vehicle.count,sim_time=float(vehicle.d.time),body=list(vehicle.body()),armed_at=session.armed_at,maximum_wall_lag_s=timing.maximum_lag_s))
                k+=1
            result.update(stale_command_ticks=stale_ticks,stop_reason=reason);status='NATIVE_COMPLETE'
    except BaseException as e:
        status='PHYSICAL_OR_EVIDENCE_EXCEPTION';result.update(error=repr(e),traceback=traceback.format_exc())
        if timing.overrun:result['timing_overrun']=timing.overrun
    finally:
        # Durable accounting precedes potentially interruptible serialization and
        # replay. Unknown totals are explicit, never inferred as zero.
        checkpoint=accounting_receipt(vehicle,timing,task,result,status)
        dump(out/'NATIVE_ACCOUNTING.json',checkpoint)
        # No further actual trajectory steps/brake/restart after a hard timing/safety abort.
        # Restore runtime-only state before lossless serialization and separate prefix replay.
        gc_window.close()
        for obj,name,original in reversed(original_methods):setattr(obj,name,original)
        result['cyclic_gc_originally_enabled']=gc_window.was_enabled
        if vehicle is not None:
            result['actual_native']=vehicle.count
            try:
                result.update(timing.call('evidence_save',vehicle.count,vehicle.finish));result['evidence_save_complete']=True
            except BaseException as e:
                result['evidence_save_complete']=False;secondary.append(dict(stage='evidence_save',error=repr(e),traceback=traceback.format_exc()));status='EVIDENCE_SAVE_EXCEPTION'
            if getattr(timing,'native_observed',False):
                result['native_api_calls_completed']=timing.native_completed
                if timing.native_integration_uncertain:
                    result.update(actual_native=None,actual_native_completed_lower_bound=max(vehicle.count,timing.native_completed),actual_count_status='NATIVE_CALL_INTERRUPTED_TOTAL_UNKNOWN')
                elif timing.native_completed!=vehicle.count-task.get('origin_native_tick',0):
                    result.update(actual_native=None,actual_native_completed_lower_bound=vehicle.count,actual_count_status='NATIVE_RETURN_COUNT_DIFFERS_FROM_RECORDED_VEHICLE_COUNT')
            dump(out/'NATIVE_ACCOUNTING.json',dict(checkpoint,evidence_save_complete=result.get('evidence_save_complete',False),fully_recorded_native=result.get('fully_recorded_native'),status='TRACE_SAVE_ATTEMPTED_BEFORE_REPLAY'))
            n=result.get('actual_native');fully=result.get('fully_recorded_native')
            if n==0:
                result.update(replay_native=0,replay_status='NO_EXECUTED_NATIVE_PREFIX')
            elif n is not None and n==fully and result.get('evidence_save_complete'):
                # Failed prefix may be verified, but this NEVER clears its navigation failure.
                # Replay is allowed only inside the same explicitly authorized future root window.
                if time.time()<deadline-10:
                    try:
                        comparison=timing.call('own_prefix_replay',n,replay,vehicle,deadline,out/'physics');result.update(replay=comparison,replay_native=comparison['replay_native'],replay_status='COMPLETED'if comparison['passed']else'MISMATCH')
                        if not comparison['passed']:status='REPLAY_MISMATCH'
                    except BaseException as e:
                        result.update(replay_native=None,replay_status='FAILED_OR_INTERRUPTED_UNKNOWN_TOTAL');secondary.append(dict(stage='own_prefix_replay',error=repr(e),traceback=traceback.format_exc()))
                else:result.update(replay_native=None,replay_status='NOT_STARTED_ROOT_DEADLINE_RESERVE')
            else:result.update(replay_native=None,replay_status='INCOMPLETE_NATIVE_RECORD_NO_FULL_REPLAY_CLAIM')
            if result.get('replay_native')is None:
                p=out/'physics/REPLAY_PROGRESS.json'
                if p.exists():
                    try:result['replay_completed_native_lower_bound']=json.loads(p.read_text())['executed_replay_native']
                    except Exception:pass
                result['replay_count_status']='UNKNOWN_OR_NOT_COMPLETED_SEE_PROGRESS'
        if secondary:result['secondary_errors']=secondary
        try:result['timing_profile']=timing.save(out)
        except BaseException as e:
            result.setdefault('secondary_errors',[]).append(dict(stage='timing_save',error=repr(e)));status='EVIDENCE_SAVE_EXCEPTION'
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGTERM,old_term);sock.close();Path(address).unlink(missing_ok=True)
        with gzip.open(out/'INGRESS.json.gz','wt')as f:json.dump(dict(receipts=session.receipts,execution=session.execution),f,allow_nan=False)
        result.update(status=status,closed=True,startup_events=session.events,armed_at=session.armed_at,maximum_wall_lag_s=timing.maximum_lag_s)
        ros=json.loads((out/'ROS_RESULT.json').read_text())if(out/'ROS_RESULT.json').exists()else{}
        result['ros_action']=ros
        if task['stage']=='component' and (out/'CLOSED_HANDOFF.json').exists():
            stages=json.loads((out/'CLOSED_HANDOFF.json').read_text())['stages']
            if len(stages)>=1:
                import numpy as np
                target=stages[-1]['path'][-1][:2]
                result['component_goal_distance_m']=float(np.linalg.norm(np.asarray(result['final_body'][:2])-target))
                result['original_route_goal_distance_m']=result.get('goal_distance_m')
                result['goal_distance_m']=result['component_goal_distance_m']
        result['parent_stop_request']=stop_requested(out,task['run_id'])
        result['passed']=bool(result['parent_stop_request']is None and status=='NATIVE_COMPLETE'and not result.get('secondary_errors')and ros.get('action_status')==4 and result.get('goal_distance_m',float('inf'))<=.45 and result.get('final_translation_speed_m_s',float('inf'))<=.03 and result.get('replay',{}).get('passed')and result.get('bad_contacts')==0)
        result['historical_prefix_replay_native']=task.get('origin_native_tick',0)
        result['new_branch_native']=None if result.get('actual_native')is None else max(0,result['actual_native']-task.get('origin_native_tick',0))
        result['own_full_trace_replay_native']=result.get('replay_native')
        if (out/'physics/PREFIX_FAILURE.json').exists():result['prefix_failure']=json.loads((out/'physics/PREFIX_FAILURE.json').read_text())
        dump(out/'RESULT.json',result)
        dump(out/'NATIVE_ACCOUNTING.json',dict(checkpoint,final=True,status=status,actual_native_exact=result.get('actual_native'),new_branch_native_exact=result.get('new_branch_native'),own_full_trace_replay_native_exact=result.get('replay_native'),replay_status=result.get('replay_status'),evidence_save_complete=result.get('evidence_save_complete',False),navigation_passed=result['passed']))
    return result

def main():
    task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text());result=run(task,receipt,file_sha(C/'SOURCE_FREEZE.json'));return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
