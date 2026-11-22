"""One complete CPP comparison; saved Python expected arrays are never inputs."""
import fcntl
import importlib.util
import json
from pathlib import Path
import time
import traceback
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1571_driver_common',C/'common.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)


def record_failure(result,error,*,stage):
    result['passed']=False
    first=stage+':'+repr(error)
    if result.get('first_error')is None:result['first_error']=first
    else:result['secondary_errors'].append(first)


def execute():
    start=time.monotonic();guard=None;writer=None;phase_writer=None;codec=None;boundary=None
    result=dict(passed=False,closed=False,first_error=None,secondary_errors=[],
        comparison_executed=False,origin_projection_attempted=False,origin_projection_returned=False,
        python_generation_native=0,physical_native=0,replay_native=0,optimizer_calls=0,
        physical_capture_native=0,whole_navigation_passed=False,
        saved_reference_is_development_input=True,live_current_reserve_qualified=False)
    folder=c.O/'model'
    try:
        c.bootstrap();c.guard()
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            assert(c.O/'FULL_CPP_BATCH_ADMISSION.json').is_file(),'FULL_CPP_BATCH_NOT_ADMITTED'
            source=c.sources();method,setup=c.inputs()
            capability=c.load('v1571_full_CPP_authority',C/'capability.py')
            guard=capability.Guard(lock=lock,method=method,prepared_sources=source)
            assert folder.is_dir()and not folder.is_symlink()
            budget=c.load('v1571_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
            boundary=c.load('v1571_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
            codec=c.load('v1571_original_json',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
            writer=budget.WriterBudget(folder,role='PLANNER',maximum_bytes=c.limits()['root_writer_bytes'],source_identity=c.digest(source))
            def save(name,value):
                with boundary.OutputBoundary(folder,writer.reserve):
                    codec.write_atomic(folder/name,codec.encoded(value),writer)
            definitions=c.load('v1571_original_definitions',c.R/'experiments/v1530_explicit_we_private_binding/definitions.py')
            a=guard.authority
            read_authority=dict(scope='ORIGINAL_WE_DEFINITIONS_ONLY',models_authorized=False,
                method_origin_authorized=False,boot_id=a['boot_id'],absolute_deadline_unix=a['absolute_deadline_unix'],
                hard_stop_monotonic=a['hard_stop_monotonic'])
            defs,proof=definitions.load_definitions(source,authority=read_authority,lock=lock)
            save('DEFINITION_BINDING.json',proof)
            origins=c.load('v1571_original_origin',c.R/'experiments/v1563_lzma_lossless_witness/origin.py')
            result['origin_projection_attempted']=True
            origin=origins.prepare(method,defs,guard,lambda value:save('CURRENT_ORIGIN.json',value))
            result['origin_projection_returned']=True
            assert time.time()<a['initialization_deadline_unix']and time.monotonic()<a['initialization_deadline_monotonic']
            phase=c.load('v1571_complete_batch_witness',C/'witness.py')
            target=folder/'audit';target.mkdir()
            phase_writer=budget.WriterBudget(target,role='PLANNER',maximum_bytes=c.limits()['phase_writer_bytes'],source_identity=c.digest(source))
            guard.start_phase('CPP_AUDIT');result['comparison_executed']=True
            with boundary.OutputBoundary(target,phase_writer.reserve)as active_boundary:
                audit=phase.run(method,setup,defs,origin,guard=guard,stage='CPP_AUDIT',folder=target,
                    writer=phase_writer,boundary=active_boundary,expected_folder=guard.reference)
            result['phase_first_error']=audit['first_error']
            if not audit['passed']:result['first_error']=audit['first_error']
            assert audit['passed']and audit['closed']and not audit['secondary_errors'],'FULL_CPP_BATCH_COMPARISON_REFUSED'
            guard.check();assert c.sources()==source
            result['passed']=True
    except BaseException as error:
        record_failure(result,error,stage='driver')
        result['traceback']=traceback.format_exc()
        if getattr(error,'secondary',None):result['secondary_errors'].append('origin_proof_save:'+error.secondary)
    finally:
        result.update(closed=True,wall_s=time.monotonic()-start)
        count=guard.ledger.counts()if guard else None
        result.update(CPP_analytical_native=count['native']if count else 0,
            CPP_inflight_unknown=count['inflight_unknown']if count else False,
            Engine_constructions=count['Engine']if count else 0,
            construction_inflight=count['construction_inflight']if count else None,
            internal_Allocator_constructors=None if count and(count['Engine']or count['construction_inflight']=='Engine')else 0,
            accounting=guard.counts()if guard else dict(models=0,native=0,physical_native=0,replay_native=0,optimizer_calls=0))
        if writer is not None:
            result['storage_accounting']=dict(root=writer._read(),phase=None if phase_writer is None else phase_writer._read())
            try:
                with boundary.OutputBoundary(folder,writer.reserve):codec.write_atomic(folder/'RESULT.json',codec.encoded(result),writer)
            except BaseException as error:
                record_failure(result,error,stage='result_save')
                print('FULL_CPP_BATCH_RESULT_SAVE_GAP:'+json.dumps(result,allow_nan=False),flush=True)
        else:
            try:
                target=c.O/'unadmitted';target.mkdir(exist_ok=True)
                budget=c.load('v1571_unadmitted_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
                boundary=c.load('v1571_unadmitted_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
                codec=c.load('v1571_unadmitted_json',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
                writer=budget.WriterBudget(target,role='PLANNER',maximum_bytes=1024**2,source_identity=c.digest({str(p.relative_to(c.R)):c.sha(p)for p in C.iterdir()if p.is_file()}))
                with boundary.OutputBoundary(target,writer.reserve):codec.write_atomic(target/'RESULT.json',codec.encoded(result),writer)
            except BaseException as error:
                record_failure(result,error,stage='unadmitted_result_save')
                print('FULL_CPP_BATCH_UNADMITTED_SAVE_GAP:'+json.dumps(result,allow_nan=False),flush=True)
    return result

if __name__=='__main__':
    answer=execute();print(json.dumps({k:answer[k]for k in ['passed','closed','first_error','CPP_analytical_native','Engine_constructions']},allow_nan=False))
    raise SystemExit(0 if answer['passed']else 1)
