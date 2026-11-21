"""Single original CPP2200 call, before-gate complete or exact partial evidence."""
import copy
import importlib.util
from pathlib import Path
import sys
import time
import traceback
C=Path(__file__).resolve().parent
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rec=load('v1532_stop_records',C/'records.py');gates=load('v1532_stop_gates',C/'stop_checks.py')
def partial_arrays(local,work,origin):
    """Only C++ rows acknowledged after all three output writes are trusted."""
    import numpy as np
    assert type(work)is int and 0<=work<=2200
    assert local['ss'].ndim==local['uu'].ndim==local['mem'].ndim==2
    assert min(len(local[k])for k in ['ss','uu','mem'])>=work
    return dict(states=np.vstack([local['state'],local['ss'][:work]]),ctrl=local['uu'][:work].copy(),
                memory=np.vstack([np.r_[origin['last_ctrl'],origin['integral']],local['mem'][:work]]))
def generate(method,setup,origin,defs,*,authority,folder,writer,lock):
    import numpy as np
    result=dict(passed=False,closed=False,analytical_native=0,analytical_inflight_unknown=False,
                cpp_engine_constructions=0,internal_Allocator_constructions=None,nominal_native=0,physical_native=0)
    engine=None;frame_holder=[];previous=sys.getprofile();arrays=None;receipt=None
    try:
        contract=load('v1532_cpp_runtime_authority',C/'contract.py')
        contract.runtime_guard(method,authority,lock,phase='CPP_GENERATION',completed=0)
        assert time.time()<authority['absolute_deadline_unix']-30 and time.monotonic()<authority['hard_stop_monotonic']-30
        geom,forecast=gates.geometry(method,setup)
        rec.save_json(folder,'GENERATION_CAUSAL_SOURCE.json',forecast,writer)
        params=__import__('json').loads((C.parents[1]/'experiments/v1159_bounded_steering_load/PARAMETERS.json').read_text())
        result['cpp_engine_constructions']=None
        engine=defs['engine'].Engine(setup,params['coefficients']);result['cpp_engine_constructions']=1
        def observe(frame,event,arg):
            if previous is not None:previous(frame,event,arg)
            if event=='call'and frame.f_code is defs['engine'].Engine.simulate.__code__:frame_holder.append(frame)
        sys.setprofile(observe)
        contract.runtime_guard(method,authority,lock,phase='CPP_GENERATION',completed=0)
        result['analytical_inflight_unknown']=True
        s,u,m=engine.simulate(copy.deepcopy(origin),[(0.,0.,2200,0)])
        result['analytical_native']=engine.native;result['analytical_inflight_unknown']=False
        sys.setprofile(previous)
        assert engine.native==2200
        front=[*origin['front_position'],*origin['front_velocity']]
        arrays=dict(states=s,ctrl=u,memory=m,modes=np.zeros((2201,3),dtype=np.int64),
                    gear=gates.gear_trace(method,s,m,front),native=method['fixed_origin_native']+np.arange(2201,dtype=np.int64),
                    sim_time=method['fixed_origin_sim_time']+.01*np.arange(2201),requests=np.zeros((2200,3)))
        # Full arrays and source identity persist before any physical/safety or
        # code-comparison gate. The CPP mode trace follows its zero-mode loop,
        # not a new measurement or a simulated Python observer.
        row=rec.save_arrays(folder,'CPP_COMPLETE_STOP.npz',arrays,writer)
        receipt=dict(complete=True,native=2200,binding=rec.binding(method),arrays=row,
                     modes_source='ORIGINAL_CPP_KNOWN_FALSE_FLAGS_AND_ALL_ZERO_REQUESTS',
                     stored_before_safety_gate=True)
        rec.save_json(folder,'CPP_BRANCH_SAVED.json',receipt,writer)
        checks=gates.evaluate(arrays,method,setup,geom)
        rec.save_json(folder,'CPP_STOP_PROOF.json',checks,writer)
        assert checks['passed'],'ORIGINAL_WE_CURRENT_CPP_STOP_REFUSED'
        assert time.time()<authority['absolute_deadline_unix'] and time.monotonic()<authority['hard_stop_monotonic']
        result.update(passed=True,complete_stop_branches=1,stop_proof=checks)
    except BaseException as error:
        sys.setprofile(previous)
        result.update(first_error=repr(error),traceback=traceback.format_exc())
        # The original C++ completed_work increments only after writing all
        # state/control/memory rows. A failed call's retained Python frame gives
        # those allocated buffers without replaying or restarting any model.
        if arrays is None and engine is not None and frame_holder:
            try:
                local=frame_holder[-1].f_locals
                if engine.in_call or result['analytical_inflight_unknown']:
                    work=int(engine.lib.profile_work());assert 0<=work<=2200
                    result['analytical_native']=work;result['analytical_inflight_unknown']=False
                else:work=result['analytical_native']
                if all(k in local for k in ['state','ss','uu','mem']):
                    partial=partial_arrays(local,work,origin)
                    row=rec.save_arrays(folder,'CPP_PARTIAL_STOP.npz',partial,writer)
                    rec.save_json(folder,'CPP_PARTIAL_RECEIPT.json',dict(complete=False,confirmed_native=work,arrays=row,
                                  binding=rec.binding(method),first_error=result['first_error'],native_unknown=result['analytical_inflight_unknown']),writer)
            except BaseException as secondary:result.setdefault('secondary_errors',[]).append('partial:'+repr(secondary))
    finally:
        sys.setprofile(previous);frame_holder.clear();result['closed']=True
        try:rec.save_json(folder,'GENERATION.json',result,writer)
        except BaseException as secondary:
            result.setdefault('secondary_errors',[]).append('generation_result_save:'+repr(secondary));result['passed']=False
    return result,receipt
