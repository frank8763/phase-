from pathlib import Path
import sys,json,math,time,signal,fcntl,importlib.util,traceback
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1175_low_speed_input_entry'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
s=importlib.util.spec_from_file_location('v1175_fixed_input_gates',R/'experiments/v1172_safe_gap_stimuli/run.py');h=importlib.util.module_from_spec(s);sys.modules[s.name]=h;s.loader.exec_module(h)
q=h.q;np=h.np;dump=q.dump;sha=q.sha
def main():
    assert not(O/'COMPLETION.json').exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')==q.GUARD
    begin=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('LOW_INPUT_120S')));signal.setitimer(signal.ITIMER_REAL,120)
    count=0;inside=False;engine=None;frozen={};error=None;result=None
    try:
        inp=json.loads((R/'runs/v1173_rate_preconditioned_input/INPUTS.json').read_text());org=inp['origin'];setup=inp['setup'];rows=[(0.,0.,2200,0),(0.,.006,1000,0),(0.,0.,2200,0)];params=q.model.parameters()
        before=json.loads((R/'runs/v1174_response_input_bundle/COMPLETION.json').read_text());assert before['error']and'float64'in before['error']['error']and before['analytical_cpp_native']==5000 and len(before['components'])==2
        dump(C/'TASKS.json',dict(rows=rows,unchanged_low_speed=.006,source_scope='NS static canonical',reuse_only=before['components']))
        paths=[*C.glob('*.py'),C/'PROTOCOL.md',C/'TASKS.json',R/'runs/v1173_rate_preconditioned_input/INPUTS.json',R/'runs/v1174_response_input_bundle/COMPLETION.json',R/'runs/v1174_response_input_bundle/run.console',R/'runs/v1173_rate_preconditioned_input/positive.npz',R/'runs/v1174_response_input_bundle/lateral.npz',R/'runs/v1159_bounded_steering_load/profile.so',R/'experiments/v1159_bounded_steering_load/engine.py',R/'experiments/v1159_bounded_steering_load/PARAMETERS.json']
        for mod in list(sys.modules.values()):
            p=getattr(mod,'__file__',None)
            if p and Path(p).resolve().is_relative_to(R)and Path(p).suffix=='.py':paths.append(Path(p).resolve())
        frozen={str(p.relative_to(R)):sha(p)for p in set(paths)};dump(C/'SOURCE_FREEZE.json',dict(files=frozen,before_all_prediction=True))
        req=q.requests_of(rows);p=q.model.Predictor(setup,org);ss=[p.state.copy()];uu=[];mm=[np.r_[p.adapter.last,p.adapter.integral]]
        for v,w,stale in req:
            inside=True;st,u=p.step(float(v),float(w),False);inside=False;count+=1;ss.append(st);uu.append(u);mm.append(np.r_[p.adapter.last,p.adapter.integral])
        ss,uu,mm=map(np.array,[ss,uu,mm]);engine=q.accelerator.Engine(setup,params['coefficients']);cs,cu,cm=engine.simulate(org,rows)
        err=max(float(abs(cs-ss).max()),float(abs(cu-uu).max()),float(abs(cm-mm).max()));assert err<=1e-8
        geometry=h.ref._old.Geometry(setup['known'],None);raw=geometry.clearances(ss[:,:3])[0];ch=h.checks(setup,org,ss,uu,mm,raw);ch.update(exact_speed=bool((req[2200:3200]==[.006,0.,0.]).all()),cpp_python=err<=1e-8)
        assert all(ch.values());plan=O/'LOW.npz';np.savez_compressed(plan,states=ss,controls=uu,memory=mm,requests=req,raw=raw)
        # Saved-array/control audit after plan is written, no new model step.
        with np.load(plan)as z:assert np.array_equal(z['states'],ss)and np.array_equal(z['memory'][1:,:4],z['controls'])
        owner=q.model.Predictor(setup,org).adapter;controlerr=0.
        for i,(v,w,stale)in enumerate(req):
            controlerr=max(controlerr,float(abs(owner.last-mm[i,:4]).max()),abs(owner.integral-mm[i,4]));u=owner.compute(v,w,ss[i,3],ss[i,5],False);controlerr=max(controlerr,float(abs(u-uu[i]).max()))
        assert controlerr<=1e-10
        component=dict(name='low',passed=True,checks=ch,plan=str(plan.relative_to(R)),plan_sha256=sha(plan),native=len(uu),minimum_raw=float(raw.min()),needed_feature='request_v',required=.006,model_feature_value=.006,request_speed_max=.006,cpp_python_error=err,independent_controller_memory_error=controlerr)
        components=[*before['components'],component]
        for row in components:assert row['passed']and sha(R/row['plan'])==row['plan_sha256']
        result=dict(components=components,all_inputs_qualified=True,independent_canonical_initials=True,physical_worker_prepared=False,physical_window_open=False,actual_response_verified=False)
        dump(O/'BUNDLE.json',result);dump(O/'FINAL_SAVED_AUDIT.json',dict(passed=True,all3_plan_hashes_verified=True,low_full_controller_memory_error=controlerr,low_geometry_recomputed=True,new_state_prediction=0,source_files=len(frozen),models=0,physical_native=0))
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());dump(O/'ERROR.json',error)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);done=dict(closed=True,error=error,all_inputs_qualified=result is not None,analytical_python_native=count,analytical_cpp_native=engine.native if engine else 0,python_inflight_unknown=inside,cpp_inflight_unknown=bool(engine and engine.in_call),models=0,physical_native=0,training_updates=0,source_unchanged=all(sha(R/p)==v for p,v in frozen.items()),guard_original=sha(R/'REVIEW_PENDING')==q.GUARD,physical_worker_prepared=False,physical_window_open=False,wall_s=time.monotonic()-begin);dump(O/'COMPLETION.json',done);print(json.dumps(done));fcntl.flock(lock,fcntl.LOCK_UN)
    return 0 if error is None else 1
if __name__=='__main__':sys.exit(main())
