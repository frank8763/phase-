"""Production stop-component CLI; no admission rejects before numerical binding."""
import fcntl
import importlib.util
import json
from pathlib import Path
import signal
import time
import traceback
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1532_driver_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def execute():
    c.bootstrap();c.guard();generation=None;audit=None;receipt=None;first=None;secondary=[]
    result=dict(passed=False,closed=False,generation_executed=False,audit_executed=False,
                physical_native=0,ownreplay_native=0,optimizer_calls=0,nominal_native=0,
                generation_analytical_native=0,audit_analytical_native=0,generation_inflight_unknown=False,
                audit_inflight_unknown=False,whole_route_passed=False,actual_capture_qualified=False)
    authority=None;folder=None;writer=None;rec=None;original_alarm=None;start=time.monotonic()
    try:
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            contract=c.load('v1532_narrow_contract',C/'contract.py')
            authority,source,method,setup=contract.admit(lock)
            folder=c.O/'model';assert folder.is_dir()and not folder.is_symlink()
            writer_module=c.load('v1532_model_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
            boundary_module=c.load('v1532_model_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
            rec=c.load('v1532_model_records',C/'records.py')
            writer=writer_module.WriterBudget(folder,role='PLANNER',maximum_bytes=authority['model_writer_bytes'],source_identity=c.digest(source))
            original_alarm=signal.getsignal(signal.SIGALRM)
            def stop(*_):raise TimeoutError('STOP_COMPONENT_MODEL_WINDOW_EXPIRED')
            signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.001,min(authority['absolute_deadline_unix']-time.time(),authority['hard_stop_monotonic']-time.monotonic())-15))
            with boundary_module.OutputBoundary(folder,writer.reserve):
                definitions=c.load('v1532_frozen_definition_dependency',c.R/'experiments/v1530_explicit_we_private_binding/definitions.py')
                read_authority=dict(scope='ORIGINAL_WE_DEFINITIONS_ONLY',models_authorized=False,method_origin_authorized=False,
                                    boot_id=authority['boot_id'],absolute_deadline_unix=authority['absolute_deadline_unix'],hard_stop_monotonic=authority['hard_stop_monotonic'])
                defs,binding=definitions.load_definitions(source,authority=read_authority,lock=lock)
                rec.save_json(folder,'EXACT_DEFINITION_BINDING.json',binding,writer)
                origin_module=c.load('v1532_current_origin',C/'origin.py')
                origin=origin_module.prepare(method,runtime=defs['runtime'],scope='ADMITTED_STOP_COMPONENT_ORIGIN',authority=authority,lock=lock,
                                             save_proof=lambda value:rec.save_json(folder,'GENERATION_ORIGIN.json',value,writer))
                generator=c.load('v1532_original_cpp_stop_generation',C/'generate.py');result['generation_executed']=True
                generation,receipt=generator.generate(method,setup,origin,defs,authority=authority,folder=folder,writer=writer,lock=lock)
                if not generation['passed']:first=generation.get('first_error')or'CURRENT_CPP_STOP_REFUSED'
                assert generation['passed']and not generation.get('secondary_errors'),'CURRENT_CPP_STOP_NOT_FULLY_SAVED_AND_QUALIFIED'
                assert contract.audit_allowed(generation,receipt),'STOP_COMPONENT_AUDIT_DEPENDENCY_REFUSED'
                auditor=c.load('v1532_independent_python_stop_audit',C/'audit.py');result['audit_executed']=True
                audit=auditor.audit(method,setup,defs,generation=generation,receipt=receipt,authority=authority,folder=folder,writer=writer,lock=lock)
                if not audit['passed']:first=audit.get('first_error')or'CURRENT_CPP_PYTHON_AUDIT_REFUSED'
                assert audit['passed']and not audit.get('secondary_errors'),'CURRENT_STOP_AUDIT_NOT_FULLY_QUALIFIED'
                result['passed']=True
                assert c.sources()==source,'STOP_COMPONENT_FINAL_SOURCE_CHANGED'
    except BaseException as error:
        first=first or repr(error);result['traceback']=traceback.format_exc()
        if getattr(error,'secondary',None):secondary.append('origin_save:'+str(error.secondary))
    finally:
        if original_alarm is not None:
            signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,original_alarm)
        result.update(closed=True,first_error=first,secondary_errors=secondary,wall_s=time.monotonic()-start)
        for prefix,value,executed in [('generation',generation,result['generation_executed']),('audit',audit,result['audit_executed'])]:
            result[prefix+'_analytical_native']=value['analytical_native']if value is not None else(None if executed else 0)
            result[prefix+'_inflight_unknown']=value['analytical_inflight_unknown']if value is not None else executed
        result['cpp_engine_constructions']=generation.get('cpp_engine_constructions')if generation else(None if result['generation_executed']else 0)
        result['python_predictor_constructions']=audit.get('python_predictor_constructions')if audit else(None if result['audit_executed']else 0)
        result['internal_Allocator_constructions']=None if result['generation_executed']or result['audit_executed']else 0
        if authority is None:
            # Real CLI missing-admission failure has no model directory or
            # frozen input access; this output is separate from numeric runs.
            target=c.O/'unadmitted';target.mkdir(exist_ok=True)
            writer_module=c.load('v1532_unadmitted_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
            boundary_module=c.load('v1532_unadmitted_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
            rec=c.load('v1532_unadmitted_records',C/'records.py')
            identity=c.digest({str(p.relative_to(c.R)):c.sha(p)for p in C.iterdir()if p.is_file()})
            writer=writer_module.WriterBudget(target,role='PLANNER',maximum_bytes=1024**2,source_identity=identity)
            with boundary_module.OutputBoundary(target,writer.reserve):rec.save_json(target,'RESULT.json',result,writer)
        elif folder is not None and rec is not None and writer is not None:
            try:
                boundary_module=c.load('v1532_close_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
                with boundary_module.OutputBoundary(folder,writer.reserve):rec.save_json(folder,'RESULT.json',result,writer)
            except BaseException as error:
                result['passed']=False;result['secondary_errors'].append('result_save:'+repr(error))
                print('STOP_COMPONENT_RESULT_SAVE_GAP:'+json.dumps(result,allow_nan=False),flush=True)
    return result
if __name__=='__main__':
    answer=execute();print(json.dumps({k:answer[k]for k in ['closed','passed','first_error','generation_analytical_native','audit_analytical_native']},allow_nan=False))
    raise SystemExit(0 if answer['passed']else 1)
