"""Success-dependent fresh original Python200; continuous state and memory."""
import copy
import importlib.util
from pathlib import Path
import time
import traceback
C=Path(__file__).resolve().parent
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rec=load('v1532_independent_records',C/'records.py');gates=load('v1532_independent_gates',C/'stop_checks.py');origins=load('v1532_independent_origin',C/'origin.py')
def audit(method,setup,defs,*,generation,receipt,authority,folder,writer,lock):
    import numpy as np
    result=dict(passed=False,closed=False,analytical_native=0,analytical_inflight_unknown=False,
                python_predictor_constructions=0,internal_Allocator_constructions=None,physical_native=0)
    states=[];controls=[];memory=[];modes=[];p=None
    try:
        assert generation['passed']and generation['closed']and generation['analytical_native']==200 and not generation['analytical_inflight_unknown']
        expected=rec.read_complete(folder,receipt,method)
        contract=load('v1532_python_runtime_authority',C/'contract.py')
        contract.runtime_guard(method,authority,lock,phase='PYTHON_AUDIT',completed=0)
        origin=origins.prepare(method,runtime=defs['runtime'],scope='ADMITTED_STOP_COMPONENT_ORIGIN',
                               authority=authority,lock=lock,save_proof=lambda value:rec.save_json(folder,'AUDIT_ORIGIN.json',value,writer))
        result['python_predictor_constructions']=None
        p=defs['model'].Predictor(setup,copy.deepcopy(origin));result['python_predictor_constructions']=1
        def append():
            states.append(p.state.copy());memory.append(np.r_[p.adapter.last,p.adapter.integral]);modes.append([int(p.coupled_episode),int(getattr(p.adapter,'_steering_motion_active',False)),int(p.steering_load_episode)])
        append()
        for index in range(200):
            contract.runtime_guard(method,authority,lock,phase='PYTHON_AUDIT',completed=index)
            assert time.time()<authority['absolute_deadline_unix']-15 and time.monotonic()<authority['hard_stop_monotonic']-15
            assert result['analytical_native']<authority['success_only_audit_native']==200
            result['analytical_inflight_unknown']=True
            _,u=p.step(0.,0.,False)
            result['analytical_native']+=1;result['analytical_inflight_unknown']=False
            controls.append(u.copy());append()
        arrays=dict(states=np.asarray(states),ctrl=np.asarray(controls),memory=np.asarray(memory),modes=np.asarray(modes,dtype=np.int64),
                    gear=gates.gear_trace(method,np.asarray(states),np.asarray(memory),[*origin['front_position'],*origin['front_velocity']]),
                    native=method['fixed_origin_native']+np.arange(201,dtype=np.int64),sim_time=method['fixed_origin_sim_time']+.01*np.arange(201),requests=np.zeros((200,3)))
        row=rec.save_arrays(folder,'PYTHON_COMPLETE_STOP.npz',arrays,writer)
        rec.save_json(folder,'PYTHON_BRANCH_SAVED.json',dict(complete=True,native=200,binding=rec.binding(method),arrays=row,stored_before_comparison_or_safety_gate=True),writer)
        differences={k:float(np.max(abs(arrays[k]-expected[k])))for k in arrays}
        geom,forecast=gates.geometry(method,setup);proof=gates.evaluate(arrays,method,setup,geom)
        comparison=dict(passed=all(value<=1e-8 for value in differences.values())and proof['passed'],maximum_errors=differences,
                        complete_fresh_python_native=200,cpp_native=200,source_binding=rec.binding(method),stop_proof=proof,
                        no_per_step_state_or_memory_reset=True,independent_physical_replay=False)
        rec.save_json(folder,'INDEPENDENT_COMPARISON.json',comparison,writer)
        assert comparison['passed'],'ORIGINAL_WE_CURRENT_CPP_PYTHON_AUDIT_REFUSED'
        result.update(passed=True,comparison=comparison)
    except BaseException as error:
        result.update(first_error=repr(error),traceback=traceback.format_exc())
        if states and len(controls)!=200:
            try:
                row=rec.save_arrays(folder,'PYTHON_PARTIAL_STOP.npz',dict(states=np.asarray(states),ctrl=np.asarray(controls).reshape((-1,4)),memory=np.asarray(memory),modes=np.asarray(modes,dtype=np.int64)),writer)
                rec.save_json(folder,'PYTHON_PARTIAL_RECEIPT.json',dict(complete=False,binding=rec.binding(method),arrays=row,confirmed_native=result['analytical_native'],native_unknown=result['analytical_inflight_unknown'],first_error=result['first_error']),writer)
            except BaseException as secondary:result.setdefault('secondary_errors',[]).append('partial:'+repr(secondary))
    finally:
        result['closed']=True
        try:rec.save_json(folder,'AUDIT.json',result,writer)
        except BaseException as secondary:
            result.setdefault('secondary_errors',[]).append('audit_result_save:'+repr(secondary));result['passed']=False
    return result
