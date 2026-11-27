"""Two original predictive response calls, no controller or physical factory."""
import copy,hashlib,json,signal,time,traceback
from types import SimpleNamespace as NS
from context import R,S,sha,read
from fixture import fixed
from store import save_json,stored_arrays
from profiles import plans as fixed_plans,shadow_refused

def execute(admission,window,source):
    from backend import bind
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('RESPONSE_MATH120S')));signal.alarm(120)
    results=[];first=None;loaded={};b=None;active_case=None;start=time.monotonic();out=S/'RUNTIME'
    try:
        b=bind();q=b.q;np=b.np;loaded=b.loaded_module_SHA256;inputs=fixed(source)
        # Full source response stays byte-identical. Proxy only counts/mirrors
        # original outer Predictor operations; internal constructors remain unknown.
        plans=fixed_plans(inputs['cases'])
        blocked=set()
        for index,case in enumerate(plans):
            if case['method']in blocked:
                skipped=dict(method=case['method'],profile=case['profile'],passed=False,complete_prediction=False,disposition='UNEXECUTED_SAME_METHOD_SHADOW_REFUSED',counts=dict(Predictor_constructor_attempts=0,Predictor_constructor_returns=0,step_attempts=0,step_returns=0,internal_factory_and_total_model_work=None))
                save_json(out/(str(index)+'_RESPONSE.json'),skipped);results.append(skipped);continue
            expected=2200+case['command_native']
            active_case=dict(method=case['method'],profile=case['profile'])
            counts=dict(Predictor_constructor_attempts=0,Predictor_constructor_returns=0,step_attempts=0,step_returns=0,step_inflight=False,internal_factory_and_total_model_work=None)
            active_case['counts']=counts
            states=[];controls=[];memory=[];requests=[];error=None;proof=None;arr_path=out/(str(index)+'_FULL_PREDICTION.npz')
            class CountedPredictor:
                def __init__(self,*args,**kwargs):
                    counts['Predictor_constructor_attempts']+=1
                    self.original=q.model.Predictor(*args,**kwargs);counts['Predictor_constructor_returns']+=1
                    states.append(self.original.state.copy());memory.append(np.r_[self.original.adapter.last,self.original.adapter.integral])
                def __getattr__(self,name):return getattr(self.original,name)
                def step(self,v,w,stale=False):
                    assert counts['step_attempts']<expected,'FIXED_RESPONSE_STEP_CAP'
                    counts['step_attempts']+=1;counts['step_inflight']=True
                    s,u=self.original.step(v,w,stale);counts['step_inflight']=False;counts['step_returns']+=1
                    states.append(s.copy());controls.append(u.copy());memory.append(np.r_[self.original.adapter.last,self.original.adapter.integral]);requests.append([v,w,stale]);return s,u
            proxy=NS(np=np,initial=q.initial,model=NS(Predictor=CountedPredictor),helper=q.helper)
            schedule=[case['request'][:]for _ in range(case['command_native'])]+[[0.,0.,False]for _ in range(2200)]
            try:
                proof,ss,uu,mm=b.response.prove(proxy,copy.deepcopy(inputs['setup']),copy.deepcopy(inputs['packet']),schedule,np.asarray(inputs['goal_xy']),None)
                assert counts['step_returns']==expected and np.array_equal(np.asarray(states),ss)and np.array_equal(np.asarray(controls),uu)and np.array_equal(np.asarray(memory),mm),'COUNTER_OR_ARRAY_MIRROR_MISMATCH'
                assert proof['native']==expected and proof['checks']['full2200']and proof['checks']['memory_shape']
            except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
            arrays=dict(states=np.asarray(states,dtype=np.float64).reshape(-1,8),controls=np.asarray(controls,dtype=np.float64).reshape(-1,4),memory=np.asarray(memory,dtype=np.float64).reshape(-1,5),requests=np.asarray(requests,dtype=np.float64).reshape(-1,3))
            size=stored_arrays(np,arr_path,arrays)
            row=dict(method=case['method'],profile=case['profile'],command_native=case['command_native'],passed=error is None and proof is not None and proof['passed'],first_error=error,proof=proof,counts=counts,arrays_path=arr_path.name,arrays_sha256=sha(arr_path),arrays_bytes=size,complete_prediction=counts['step_returns']==expected,missing_step_or_constructor_work_unknown=bool(counts['step_inflight']or counts['Predictor_constructor_attempts']!=counts['Predictor_constructor_returns']),original_controller_queries=0,original_plant_factory_calls=0,original_physics_native=0,original_replay_native=0,whole_goal_or_physical_capability=False)
            save_json(out/(str(index)+'_RESPONSE.json'),row);results.append(row);active_case=None
            if error is None and proof is not None:shadow_refused(case,proof['passed'],blocked)
            assert all(sha(R/n)==h for n,h in source.items()),'SOURCE_CHANGED_AFTER_PREDICTIVE_CASE'
            if error is not None:raise AssertionError('PREDICTIVE_EXCEPTION_SCOPE_CLOSED_NO_NEXT_CASE')
    except BaseException as e:first=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        if b is not None:b.restore_import_guard()
    result=dict(closed=True,scope='FIXED_RAW_OUTPUT_ORIGINAL_RESPONSE_PREDICTIONS_NOT_PHYSICAL_NAVIGATION',passed=first is None and len(results)==4 and all(r['passed']for r in results),first_error=first,methods=[dict(method=r['method'],profile=r['profile'],disposition=r.get('disposition','EVALUATED'),passed=r['passed'],complete_prediction=r['complete_prediction'],counts=r['counts'],proof_sha256=sha(out/(str(i)+'_RESPONSE.json')))for i,r in enumerate(results)],loaded_analytic_module_SHA256=loaded,original_plant_actual_replay_formal_newmechanism=0,planned_profile_count=4,started_profile_not_fully_saved=active_case,remaining_profile_count=4-len(results)-(1 if active_case else 0),unknown_total_internal_model_work=True,physical_capability_or_mechanism_gain=False,wall_s=time.monotonic()-start)
    save_json(out/'RESULT.json',result);print(json.dumps(dict(passed=result['passed'],methods=result['methods'],first_error=first,whole_goal_success=False)),flush=True)
    return 0 if result['passed']else 1
