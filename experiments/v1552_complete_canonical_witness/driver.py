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
            budget=c.load('v1552_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
            io=c.load('v1552_original_io_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
            codec=c.load('v1552_original_evidence_codec',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
            writer=budget.WriterBudget(folder,role='PLANNER',maximum_bytes=guard.authority['model_writer_bytes'],source_identity=c.digest(source))
            boundary=io
            with io.OutputBoundary(folder,writer.reserve):
                def save(name,value):
                    codec.write_atomic(folder/name,codec.encoded(value),writer)
                definitions=c.load('v1552_exact_original_definitions',c.R/'experiments/v1530_explicit_we_private_binding/definitions.py')
                a=guard.authority
                read_authority=dict(scope='ORIGINAL_WE_DEFINITIONS_ONLY',models_authorized=False,method_origin_authorized=False,
                                    boot_id=a['boot_id'],absolute_deadline_unix=a['absolute_deadline_unix'],hard_stop_monotonic=a['hard_stop_monotonic'])
                defs,proof=definitions.load_definitions(source,authority=read_authority,lock=lock)
                save('DEFINITION_BINDING.json',proof)
                origins=c.load('v1552_current_origin',C/'origin.py')
                origin=origins.prepare(method,defs,guard,lambda proof:save('CURRENT_ORIGIN.json',proof))
                phases=c.load('v1552_finite_witness_owner',C/'witness.py')
                result['generation_executed']=True
                generation=phases.run(method,setup,defs,origin,guard=guard,stage='PYTHON_GENERATION',folder=folder,writer=writer)
                if not generation['passed']:
                    result['first_error']=generation['first_error']
                assert generation['passed'] and generation['secondary_errors']==[], 'NONZERO_GENERATION_NOT_QUALIFIED'
                guard.allow_saved_success_audit(folder/'GENERATION.json',c.sha(folder/'GENERATION.json'))
                target=folder/'audit'
                target.mkdir()
                result['audit_executed']=True
                audit=phases.run(method,setup,defs,origin,guard=guard,stage='CPP_AUDIT',folder=target,writer=writer,expected_folder=folder)
                if not audit['passed']:
                    result['first_error']=audit['first_error']
                assert audit['passed'] and audit['secondary_errors']==[], 'NONZERO_CPP_AUDIT_NOT_QUALIFIED'
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
