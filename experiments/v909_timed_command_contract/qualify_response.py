"""Fixed eighteen command/stop responses. Vehicle initialization only under run_phase."""
import fcntl,json,math,os,signal,sys,time,traceback
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v909_timed_command_contract'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from authority import root_authorized
from handshake import verify_sources,file_sha
from command_tube import nominal,POSITION_RESIDUAL_M,ANGLE_RESIDUAL_RAD,MAX_BODY_SPEED,MAX_BODY_YAW_RATE

def main():
    auth=root_authorized(time.time(),file_sha(C/'SOURCE_FREEZE.json'));verify_sources(R,C/'SOURCE_FREEZE.json')
    index=int(sys.argv[1]);assert 0<=index<18
    claim=O/('RESPONSE_%02d_CLAIM.json'%index);assert not claim.exists(),'RESPONSE_ALREADY_ATTEMPTED'
    claim.write_text(json.dumps(dict(pid=os.getpid(),at=time.time()))+'\n')
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cpus=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpus[min(3,len(cpus)-1)]})
    def halt(*_):raise InterruptedError('PLATFORM_DEADLINE_OR_TERMINATION')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,min(60.,auth['deadline_unix']-30-time.time()))
    sys.path.insert(0,str(C));from physical import create_vehicle,replay
    rows=[];vehicle=None;partial=None;result=dict(passed=False,private_native=0,actual_native=0,replay_native=0,models_attempted=0)
    tasks=json.loads((C/'PLATFORM_TASKS.json').read_text())
    try:
        for case in [tasks[index]]:
            assert time.time()<auth['deadline_unix']-60
            out=R/case['output'];assert not out.exists()
            result['models_attempted']+=1;vehicle=create_vehicle(out/'physics',case)
            body=[];begun=time.monotonic();initial=None
            for i in range(420):
                time.sleep(max(0.,begun+i*.01-time.monotonic()))
                assert time.time()<auth['deadline_unix']-20
                if i==200:initial=list(vehicle.body())
                v,w=case['warm'] if i<200 else (case['command'] if i<220 else [0.,0.])
                vehicle.step(v,w);body.append(list(vehicle.body()))
            finished=vehicle.finish();compare=replay(vehicle,auth['deadline_unix'],out/'physics')
            data=np.asarray(body);actual=data[200:];expected=nominal(initial,*case['command'],np.arange(1,221)*.01)
            position=np.linalg.norm(actual[:,:2]-expected[:,:2],axis=1)
            angle=abs(np.arctan2(np.sin(actual[:,2]-expected[:,2]),np.cos(actual[:,2]-expected[:,2])))
            checks=dict(complete420=finished['actual_native']==420 and finished['fully_recorded_native']==420,
                        all_native_safety=finished['minimum_actual_clearance_m']>=.15 and finished['bad_contacts']==0,
                        full_control_replay=compare['passed'] and compare['replay_native']==420,
                        bounded_position=float(position.max())<=POSITION_RESIDUAL_M,
                        bounded_rotation=float(angle.max())<=ANGLE_RESIDUAL_RAD,
                        measured_speed_bound=float(abs(data[:,3]).max())<=MAX_BODY_SPEED,
                        measured_yaw_bound=float(abs(data[:,4]).max())<=MAX_BODY_YAW_RATE,
                        settled_by_half_second=bool(np.max(abs(actual[69:,3:5]))<=.03))
            item=dict(case=case,passed=all(checks.values()),checks=checks,actual_native=420,replay_native=420,private_native=0,
                      position_residual_max_m=float(position.max()),angle_residual_max_rad=float(angle.max()),native=finished,replay=compare)
            (out/'QUALIFICATION.json').write_text(json.dumps(item,indent=2)+'\n');np.savez_compressed(out/'BODY_SAMPLES.npz',body=data,origin=initial,expected=expected)
            rows.append(item);(O/'PLATFORM_PROGRESS.json').write_text(json.dumps(dict(completed=len(rows),last=item),indent=2)+'\n');vehicle=None
            assert item['passed'],'FIRST_PLATFORM_QUALIFICATION_FAILURE'
        result['passed']=True
    except BaseException as e:
        result.update(error=repr(e),traceback=traceback.format_exc())
        if vehicle is not None:
            try:partial=vehicle.finish()
            except Exception:partial=dict(actual_native=None,fully_recorded_native=None)
            result['partial']=partial
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        # Completed case already in rows must not be double counted if its gate failed.
        result.update(rows=rows,actual_native=sum(x['actual_native']for x in rows)+(0 if partial is None else partial['actual_native']) if partial is None or partial['actual_native'] is not None else None,
                      replay_native=sum(x['replay_native']for x in rows) if partial is None else None,
                      unexecuted_cases=1-len(rows),closed_unix=time.time(),empirical_only=True)
        (O/('RESPONSE_%02d_RESULT.json'%index)).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='rows'}),flush=True)
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
