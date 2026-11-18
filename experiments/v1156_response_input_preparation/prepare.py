"""One fixed static response/capture input qualification; original predictor."""
from pathlib import Path
import fcntl
import importlib.util
import math
import signal
import sys
import time
import traceback

C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1156_response_input_preparation'
spec=importlib.util.spec_from_file_location('v1156_original_qualified_tools',R/'experiments/v1151_retained_recovery_qualification/qualify.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
np=q.np
spec=importlib.util.spec_from_file_location('v1156_original_capture',R/'experiments/v1152_terminal_capture_qualification/capture.py')
capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
CAP=.42722137342572125
GUARD='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'


def gate(ss,uu,rr,memory,setup,low):
    limits=np.array(setup['limits']);rates=np.array(setup['slew_per_second'])*.01
    checks=dict(finite=bool(np.isfinite(ss).all() and np.isfinite(uu).all()),
        complete_shapes=len(ss)==len(uu)+1==len(rr)+1,
        raw=low>=q.REQUIRED,body_caps=bool((abs(ss[:,3:6])<=[.13,.03,.16]).all()),
        ctrl=bool((uu>=limits[:,0]-1e-10).all() and (uu<=limits[:,1]+1e-10).all()),
        slew=bool((abs(np.diff(np.vstack([memory[:4],uu]),axis=0))<=rates+1e-10).all()),
        full2200_stop=bool((rr[-2200:]==0).all()),
        terminal_rest=bool(abs(ss[-50:,3:6]).max()<=.003 and abs(ss[-50:,7]).max()<=.015))
    return dict(passed=all(checks.values()),checks=checks,minimum_raw_m=low)


def main():
    assert not O.exists(), 'ONE_FIXED_PREPARATION_ONLY'
    O.mkdir(parents=True)
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert q.sha(R/'REVIEW_PENDING')==GUARD
    start=time.monotonic();q.dump(O/'ROUND_WINDOW.json',dict(started_unix=time.time(),started_monotonic=start,
        absolute_deadline_unix=time.time()+600,hard_stop_monotonic=start+600,
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),software_only=True,models_authorized=False))
    def halt(*_):raise TimeoutError('FIXED_RESPONSE_SOFTWARE_600S')
    signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,600)
    error=None;result={};engine=None;cpp=0;python=0;inside=False;frozen={}
    try:
        fixture_path=R/'experiments/v1139_afternoon_observer/STATIC_T0_SOURCE_FIXTURE.json'
        fixture=q.json.loads(fixture_path.read_text());setup=fixture['setup'];packet=fixture['packet']
        origin=q.initial(packet);origin['coupled_episode']=False;origin['steering_motion_active']=False
        rows=[(0.,0.,2200,0),(0.,.12,500,0),(CAP,.12,500,0),(-CAP,.12,500,0),(0.,.12,500,0),(0.,0.,2200,0)]
        assert sum(r[2]for r in rows)==6400
        paths=[*C.glob('*.py'),C/'PROTOCOL.md',fixture_path,
            R/'experiments/v1152_terminal_capture_qualification/capture.py',
            R/'runs/v1118_coupled_live_qualification/profile.so']
        for m in list(sys.modules.values()):
            file=getattr(m,'__file__',None)
            if file and Path(file).resolve().is_relative_to(R) and Path(file).suffix=='.py':paths.append(Path(file).resolve())
        frozen={str(p.relative_to(R)):q.sha(p)for p in set(paths)}
        q.dump(C/'SOURCE_FREEZE.json',dict(files=frozen,rows=rows,candidate_model='original_V1118_not_V1155'))
        from kernel import ref
        geometry=ref._old.Geometry(setup['known'],None)
        engine=q.Engine(setup)
        ss,uu=engine.simulate(origin,rows);cpp=engine.native
        inside=True;ps,pu,pm,episodes,active=q.python_replay(setup,origin,rows);inside=False;python+=6400
        error_max=max(float(abs(ss-ps).max()),float(abs(uu-pu).max()))
        assert error_max<=1e-8, 'ORIGINAL_CPP_PYTHON'
        state=ss[-1];target=state[:3].copy();target[:2]+=.04*np.array([math.cos(state[2]),math.sin(state[2])])
        tail_origin=dict(state=state.copy(),last_ctrl=pm[-1,:4].copy(),integral=float(pm[-1,4]),
                         coupled_episode=False,steering_motion_active=False)
        p=q.Predictor(setup,tail_origin)
        schedule=[];states=list(ps);controls=list(pu);memory=list(pm);status='UNASSESSED';capture_count=0
        requests=[[v,0. if not v else v*math.tan(t)/.6,0.] for t,v,n,mode in rows for _ in range(n)]
        for k in range(600):
            v,w,status=capture.request(p.state,target)
            if status=='CAPTURED':break
            assert status=='CAPTURING', 'FIXED_CAPTURE_REFUSED'
            inside=True;s,u=p.step(v,w,False);inside=False;python+=1
            schedule.append((math.atan(.6*w/v),v,1,0));states.append(s);controls.append(u)
            requests.append([v,w,0.]);memory.append(np.r_[p.adapter.last,p.adapter.integral]);capture_count+=1
        assert status=='CAPTURED', 'FIXED_CAPTURE_600_CAP'
        for _ in range(2200):
            inside=True;s,u=p.step(0.,0.,False);inside=False;python+=1
            states.append(s);controls.append(u);requests.append([0.,0.,0.]);memory.append(np.r_[p.adapter.last,p.adapter.integral])
        schedule.append((0.,0.,2200,0))
        ts,tu=engine.simulate(tail_origin,schedule);cpp=engine.native
        states,controls,requests,memory=map(np.array,[states,controls,requests,memory])
        tail_difference=max(float(abs(ts-states[6400:]).max()),float(abs(tu-controls[6400:]).max()))
        assert tail_difference<=1e-8,'CAPTURE_REQUEST_CPP_PYTHON'
        a,_=geometry.clearances(states[:,:3]);full=gate(states,controls,requests,memory[0],setup,float(a.min()))
        full['checks']['capture_target_position']=float(np.linalg.norm(states[-1,:2]-target[:2]))<=.025
        full['checks']['capture_target_heading']=abs(math.atan2(math.sin(states[-1,2]-target[2]),math.cos(states[-1,2]-target[2])))<=.1
        full['passed']=all(full['checks'].values())
        np.savez_compressed(O/'PLAN.npz',states=states,controls=controls,requests=requests,memory=memory,capture_target=target)
        q.dump(O/'FIXED_PROFILE.json',dict(rows=rows,capture_rows=schedule,capture_target_nominal=target,
            actual_capture_target_rule='actual complete-stop XY + .04*[cos(actual yaw),sin(actual yaw)]',
            component_not_original_route_goal=True,continuous_drive_native=2000))
        q.dump(O/'FULL_SOURCE_PROOF.json',full)
        assert full['passed'],'FIXED_STATIC_INPUT_UNQUALIFIED'
        indices=sorted(set([*range(2200,4201,8),*range(6400,6400+capture_count+1,8),6400+capture_count]))
        proofs=[]
        for i in indices:
            origin=dict(state=states[i].copy(),last_ctrl=memory[i,:4].copy(),integral=float(memory[i,4]),
                        coupled_episode=False,steering_motion_active=False)
            stop_s,stop_u=engine.simulate(origin,[(0.,0.,2200,0)]);cpp=engine.native
            a,_=geometry.clearances(stop_s[:,:3]);proof=gate(stop_s,stop_u,np.zeros((2200,3)),memory[i],setup,float(a.min()))
            proofs.append(dict(native=i,**proof))
            assert proof['passed'],('STATIC_COMPLETE_STOP_UNQUALIFIED',i,proof)
        q.dump(O/'ALL8_STOPS.json',dict(passed=True,count=len(proofs),rows=proofs,static_only=True))
        result=dict(passed=True,scope='fixed response input nominal software qualification only',
            continuous_drive_s=20.,capture_native=capture_count,capture_seconds=capture_count*.01,
            final_capture_position_error_m=float(np.linalg.norm(states[-1,:2]-target[:2])),
            complete_source_native=len(controls),minimum_raw_m=full['minimum_raw_m'],
            cpp_python_max_error=max(error_max,tail_difference),complete_stop_cases=len(proofs),
            actual_response_verified=False,physical_worker_qualified=False,physical_eligible=False,
            new_physical_window_opened=False,original_goal_passed=False,three_routes=False,new24=False)
    except BaseException as e:
        error=dict(error=repr(e),traceback=traceback.format_exc());q.dump(O/'ERROR.json',error)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        result.update(closed=True,error=error,analytical_cpp_native=engine.native if engine else cpp,
            analytical_python_native=python,analytical_inflight_unknown=inside or bool(engine and getattr(engine,'in_call',False)),
            models=0,physical_native=0,training_updates=0,guard_original=q.sha(R/'REVIEW_PENDING')==GUARD,
            source_unchanged=all(q.sha(R/p)==h for p,h in frozen.items()),wall_s=time.monotonic()-start)
        q.dump(O/'COMPLETION.json',result);print(q.json.dumps(result,ensure_ascii=False))
    return 0 if result.get('passed') else 1


if __name__=='__main__':sys.exit(main())
