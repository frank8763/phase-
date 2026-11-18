"""Small fixed stimulus library and one full combined input qualification."""
from pathlib import Path
import json,sys,math,time,signal,fcntl,traceback,importlib.util,itertools
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1172_safe_gap_stimuli'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
q=load('v1172_fixed_analytical_bindings',R/'experiments/v1160_safe_terminal_connection/search.py');np=q.np;dump=q.dump;sha=q.sha
from kernel import ref
RATE=.6042696793941015;LATERAL=.026001030270743174;CAP=.42722137342572125
def library():
    out=[]
    for speed,sign,initial,n1,n2 in itertools.product([.12,.13],[-1,1],['turn','straight'],[200,400,600],[400,600]):
        rows=[(0.,0.,2200,0),(sign*CAP if initial=='turn'else 0.,speed,n1,0),(-sign*CAP,speed,n2,0),(0.,0.,2200,0)]
        out.append(dict(id=len(out),rows=rows,request_speed=speed,drive_native=n1+n2))
    assert len(out)==48;return out
def checks(setup,org,ss,uu,mem,raw):
    lim=np.array(setup['limits']);rate=np.array(setup['slew_per_second'])*.01
    return dict(finite=bool(np.isfinite(ss).all()and np.isfinite(uu).all()),raw=raw.min()>=q.REQUIRED,body=bool((abs(ss[:,3:6])<=[.13,.03,.16]).all()),ctrl=bool((uu>=lim[:,0]-1e-10).all()and(uu<=lim[:,1]+1e-10).all()),slew=bool((abs(np.diff(np.vstack([org['last_ctrl'],uu]),axis=0))<=rate+1e-10).all()),complete2200rest=bool(abs(ss[-50:,3:6]).max()<=.003 and abs(ss[-50:,7]).max()<=.015),memory=mem.shape==(len(ss),5)and np.array_equal(mem[1:,:4],uu))
def main():
    assert not(O/'COMPLETION.json').exists()and not(C/'SOURCE_FREEZE.json').exists()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')==q.GUARD
    start=time.monotonic();dump(O/'ROUND_WINDOW.json',dict(software_only=True,started_unix=time.time(),deadline_monotonic=start+600,models_authorized=False,old_windows_closed=True))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('STIMULUS_LIBRARY_600S')));signal.setitimer(signal.ITIMER_REAL,600)
    frozen={};engine=None;count=0;inside=False;rows=[];selected=None;combined=None;error=None
    try:
        fp=R/'experiments/v1139_afternoon_observer/STATIC_T0_SOURCE_FIXTURE.json';fixture=json.loads(fp.read_text());setup=fixture['setup'];org=dict(q.initial(fixture['packet']),steering_load_episode=False);assert not setup['dynamic']
        params=q.model.parameters();queue=library();dump(C/'TASKS.json',dict(proposals=queue,required_rate=RATE,required_lateral=LATERAL,low_speed=.006,low_steps=1000))
        dump(O/'INPUTS.json',dict(origin=org,setup=setup,model_parameters=params,original_raw=q.REQUIRED,original_response_bounds=[.04,.035,.015]))
        files=[*C.glob('*.py'),C/'PROTOCOL.md',C/'TASKS.json',fp,R/'runs/v1159_bounded_steering_load/profile.so',R/'experiments/v1159_bounded_steering_load/profile.cpp',R/'experiments/v1159_bounded_steering_load/PARAMETERS.json',R/'runs/v1171_gap_response_preparation/COMPLETION.json',R/'runs/v1171_gap_response_preparation/FINAL_SAVED_AUDIT.json']
        for module in list(sys.modules.values()):
            p=getattr(module,'__file__',None)
            if p and Path(p).resolve().is_relative_to(R)and Path(p).suffix=='.py':files.append(Path(p).resolve())
        frozen={str(f.relative_to(R)):sha(f)for f in set(files)};dump(C/'SOURCE_FREEZE.json',dict(files=frozen,fixed_library_before_prediction=True))
        engine=q.accelerator.Engine(setup,params['coefficients']);g=ref._old.Geometry(setup['known'],None)
        for candidate in queue:
            ss,uu,mem=engine.simulate(org,candidate['rows']);raw=g.clearances(ss[:,:3])[0];ch=checks(setup,org,ss,uu,mem,raw)
            ch.update(rate_coverage=abs(ss[:,7]).max()>=RATE-1e-8,lateral_coverage=abs(ss[:,4]).max()>=LATERAL-1e-8)
            result=dict(id=candidate['id'],passed=all(ch.values()),checks=ch,minimum_raw=float(raw.min()),maximum_lateral=float(abs(ss[:,4]).max()),maximum_rate=float(abs(ss[:,7]).max()),drive_native=candidate['drive_native'],request_speed=candidate['request_speed'],native=len(uu));rows.append(result)
        dump(O/'LIBRARY_RESULTS.json',rows);eligible=[r for r in rows if r['passed']]
        if eligible:
            best=min(eligible,key=lambda r:(r['drive_native'],-r['minimum_raw'],r['id']));selected=queue[best['id']]
            full=[*selected['rows'],(0.,.006,1000,0),(0.,0.,2200,0)]
            requests=q.requests_of(full);p=q.model.Predictor(setup,org);ss=[p.state.copy()];uu=[];mm=[np.r_[p.adapter.last,p.adapter.integral]]
            for v,w,stale in requests:
                inside=True;s,u=p.step(float(v),float(w),bool(stale));inside=False;count+=1;ss.append(s);uu.append(u);mm.append(np.r_[p.adapter.last,p.adapter.integral])
            ss,uu,mm=map(np.array,[ss,uu,mm]);cs,cu,cm=engine.simulate(org,full);err=max(float(abs(cs-ss).max()),float(abs(cu-uu).max()),float(abs(cm-mm).max()));assert err<=1e-8,'CPP_PYTHON_COMPLETE_PROFILE'
            raw=g.clearances(ss[:,:3])[0];ch=checks(setup,org,ss,uu,mm,raw);ch.update(rate_coverage=abs(ss[:,7]).max()>=RATE-1e-8,lateral_coverage=abs(ss[:,4]).max()>=LATERAL-1e-8,exact_low_speed=bool((requests[-3200:-2200]==[.006,0,0]).all()),cpp_python=err<=1e-8)
            combined=dict(passed=all(ch.values()),checks=ch,selected=selected,rows=full,native=len(uu),minimum_raw=float(raw.min()),maximum_lateral=float(abs(ss[:,4]).max()),maximum_rate=float(abs(ss[:,7]).max()),cpp_python_error=err,request_speed=selected['request_speed'],low_speed=.006,actual_response_verified=False)
            np.savez_compressed(O/'PLAN.npz',states=ss,controls=uu,memory=mm,requests=requests,raw=raw);dump(O/'SELECTED.json',combined)
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());dump(O/'ERROR.json',error)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        done=dict(closed=True,error=error,library_completed=len(rows),library_eligible=sum(r['passed']for r in rows),selected=selected,combined=combined,all_three_stimuli_qualified=bool(combined and combined['passed']),analytical_python_native=count,analytical_cpp_native=engine.native if engine else 0,python_inflight_unknown=inside,cpp_inflight_unknown=bool(engine and engine.in_call),models=0,physical_native=0,training_updates=0,physical_window_open=False,physical_worker_prepared=False,source_unchanged=all(sha(R/f)==h for f,h in frozen.items()),guard_original=sha(R/'REVIEW_PENDING')==q.GUARD,wall_s=time.monotonic()-start,stop_reason='SAFE_COMBINED_STIMULUS_QUALIFIED'if combined and combined['passed']and error is None else'INSUFFICIENT_FIXED_LIBRARY'if not error else'SOURCE_OR_EVIDENCE_ERROR')
        dump(O/'COMPLETION.json',done);print(json.dumps({k:v for k,v in done.items()if k not in ['selected','combined']}));fcntl.flock(lock,fcntl.LOCK_UN)
    return 0 if error is None else 1
if __name__=='__main__':sys.exit(main())
