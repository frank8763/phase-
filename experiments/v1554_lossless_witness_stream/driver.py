"""Production private CLI with missing-admission and first-error persistence.

There is intentionally no once supervisor/admission file in this preparation.
"""
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import traceback

C=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v1552_cpu2_common',C/'common.py')
c=importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def execute():
    start=time.monotonic()
    result=dict(passed=False,closed=False,first_error=None,secondary_errors=[],
                generation_executed=False,audit_executed=False,
                physical_native=0,replay_native=0,optimizer_calls=0,
                physical_capture_native=0,
                whole_navigation_passed=False,actual_capture_qualified=False)
    guard=None
    writer=None
    codec=None
    boundary=None
    folder=None
    generation=None
    audit=None
    try:
        c.bootstrap()
        c.guard()
        with (c.R/'runs/v648_static_unknown/execution.lock').open() as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            # Refuse before loading any numerical definitions or origins.
            assert (c.O/'NONZERO_PRIVATE_ADMISSION.json').is_file(), 'CANONICAL_NONZERO_PRIVATE_NOT_ADMITTED'
            source=c.sources()
            saved='runs/v1550_canonical_observer_policy/source_target/RESPONSE_METHOD.json'
            index=c.read(c.R/'runs/v1551_canonical_observer_source_recovery/ARCHIVE_INDEX.json')
            row=next(row for row in index['files']if row['path']==saved)
            assert c.sha(c.R/saved)==row['sha256']
            method=c.read(c.R/saved)
            clean=method.copy()
            response_sha=clean.pop('response_method_sha256')
            assert c.digest(clean)==response_sha
            setup_path=c.R/'runs/v1479_retirement_scope_binding/first_event/bridge_events/event0000/SETUP.json'
            fixed=c.read(c.O/'FIXED_INPUTS.json')
            assert c.sha(setup_path)==fixed['setup_sha256']
            assert c.sha(c.R/saved)==fixed['response_method_file_sha256']
            assert response_sha==fixed['response_method_sha256']
            capability=c.load('v1552_real_admission',C/'capability.py')
            guard=capability.Guard(lock=lock,method_input_sha256=response_sha,prepared_sources=source)
            setup=c.read(setup_path)
            folder=c.O/'model'
            assert folder.is_dir() and not folder.is_symlink()
            budget=c.load('v1554_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
            io=c.load('v1554_original_io_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
            codec=c.load('v1554_original_evidence_codec',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
            writer=budget.WriterBudget(folder,role='PLANNER',maximum_bytes=c.limits()['root_writer_bytes'],source_identity=c.digest(source))
            boundary=io
            def save(name,value):
                with io.OutputBoundary(folder,writer.reserve):
                    codec.write_atomic(folder/name,codec.encoded(value),writer)
            definitions=c.load('v1554_same_original_definitions',c.R/'experiments/v1530_explicit_we_private_binding/definitions.py')
            a=guard.authority
            read_authority=dict(scope='ORIGINAL_WE_DEFINITIONS_ONLY',models_authorized=False,method_origin_authorized=False,
                                boot_id=a['boot_id'],absolute_deadline_unix=a['absolute_deadline_unix'],hard_stop_monotonic=a['hard_stop_monotonic'])
            defs,proof=definitions.load_definitions(source,authority=read_authority,lock=lock)
            save('DEFINITION_BINDING.json',proof)
            origins=c.load('v1554_same_current_origin',c.R/'experiments/v1552_complete_canonical_witness/origin.py')
            origin=origins.prepare(method,defs,guard,lambda proof:save('CURRENT_ORIGIN.json',proof))
            phases=c.load('v1554_streamed_witness_owner',C/'witness.py')
            phase_writers={}
            def phase(stage,name,expected=None):
                target=folder/name
                target.mkdir()
                phase_writer=budget.WriterBudget(target,role='PLANNER',maximum_bytes=c.limits()['phase_writer_bytes'],source_identity=c.digest(source))
                phase_writers[stage]=phase_writer
                guard.start_phase(stage)
                with io.OutputBoundary(target,phase_writer.reserve)as active_boundary:
                    answer=phases.run(method,setup,defs,origin,guard=guard,stage=stage,folder=target,
                        writer=phase_writer,boundary=active_boundary,expected_folder=expected)
                return target,answer
            result['generation_executed']=True
            target,generation=phase('PYTHON_GENERATION','generation')
            if not generation['passed']:result['first_error']=generation['first_error']
            assert generation['passed']and generation['secondary_errors']==[],'NONZERO_GENERATION_NOT_QUALIFIED'
            guard.finish_phase('PYTHON_GENERATION')
            guard.allow_saved_success_audit(target/'GENERATION.json',c.sha(target/'GENERATION.json'))
            result['audit_executed']=True
            _,audit=phase('CPP_AUDIT','audit',target)
            if not audit['passed']:result['first_error']=audit['first_error']
            assert audit['passed']and audit['secondary_errors']==[],'NONZERO_CPP_AUDIT_NOT_QUALIFIED'
            guard.finish_phase('CPP_AUDIT')
            assert c.sources()==source
            guard.check()
            result['passed']=True
    except BaseException as error:
        result['passed']=False
        result['first_error']=result['first_error'] or repr(error)
        result['traceback']=traceback.format_exc()
        if getattr(error,'secondary',None):
            result['secondary_errors'].append('origin_proof_save:'+error.secondary)
    finally:
        result.update(closed=True,wall_s=time.monotonic()-start)
        result['accounting']=guard.counts()if guard else dict(models=0,analytical_native=0,physical_native=0,replay_native=0,optimizer_calls=0)
        for label,stage in [('generation','PYTHON_GENERATION'),('audit','CPP_AUDIT')]:
            value=guard.account[stage] if guard else None
            result[label+'_analytical_native']=value['native'] if value else 0
            result[label+'_inflight_unknown']=value['inflight_unknown'] if value else False
        result['python_predictor_constructions']=guard.account['PYTHON_GENERATION']['Predictor']if guard else 0
        result['cpp_engine_constructions']=guard.account['CPP_AUDIT']['Engine']if guard else 0
        result['model_construction_inflight']={stage:value['construction_inflight']for stage,value in guard.account.items()}if guard else {}
        result['internal_Allocator_constructors']=None if guard and guard.phases_started else 0
        if writer is not None:
            result['storage_accounting']=dict(root=writer._read(),phase={key:value._read()for key,value in locals().get('phase_writers',{}).items()})
        if writer is not None:
            try:
                with boundary.OutputBoundary(folder,writer.reserve):
                    codec.write_atomic(folder/'RESULT.json',codec.encoded(result),writer)
            except BaseException as error:
                result['passed']=False
                result['secondary_errors'].append('result_save:'+repr(error))
                print('NONZERO_DRIVER_RESULT_SAVE_GAP:'+json.dumps(result,allow_nan=False),flush=True)
        else:
            try:
                target=c.O/'unadmitted'
                target.mkdir(exist_ok=True)
                budget=c.load('v1552_unadmitted_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
                io=c.load('v1552_unadmitted_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
                codec=c.load('v1552_unadmitted_codec',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
                identity=c.digest({str(path.relative_to(c.R)):c.sha(path)for path in C.iterdir()if path.is_file()})
                writer=budget.WriterBudget(target,role='PLANNER',maximum_bytes=1024**2,source_identity=identity)
                with io.OutputBoundary(target,writer.reserve):
                    codec.write_atomic(target/'RESULT.json',codec.encoded(result),writer)
            except BaseException as error:
                result['passed']=False
                result['secondary_errors'].append('unadmitted_result_save:'+repr(error))
                print('NONZERO_UNADMITTED_SAVE_GAP:'+json.dumps(result,allow_nan=False),flush=True)
    return result


if __name__=='__main__':
    answer=execute()
    print(json.dumps({key:answer[key]for key in ['passed','closed','first_error','generation_executed','audit_executed']},allow_nan=False))
    raise SystemExit(0 if answer['passed']else 1)
