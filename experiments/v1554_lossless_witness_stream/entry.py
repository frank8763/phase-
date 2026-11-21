"""One new lossless-stream/source target; software rows, zero model calls."""
import ast
import copy
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

C=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v1554_source_common',C/'common.py')
c=importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def main():
    start=time.monotonic()
    assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0),f)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,
        phase_FFI_loads=0,Allocator_recomputations=0,optimizer_calls=0,replay_native=0,old_policy_calls=0)

    class NoModels(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'jax','jaxlib','mujoco','torch','rclpy','runtime','bindings','kernel','prediction','coupled_model','vehicle','factory','gear_handoff'}:
                raise AssertionError('LOSSLESS_SOURCE_TARGET_NO_MODEL_IMPORT:'+name)
    finder=NoModels();sys.meta_path.insert(0,finder)
    def profile(frame,event,arg):
        if event=='call':
            path=Path(frame.f_code.co_filename)
            if path.is_absolute()and path.is_relative_to(c.R):
                assert frame.f_code.co_name not in {'step','select','simulate','compute','predict','expand','advance','load_definitions'}
                if frame.f_code.co_name=='__init__'and not path.is_relative_to(C):
                    assert path in {c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}
            assert time.monotonic()-start<120
    def audit_hook(event,args):
        if event=='ctypes.dlopen'and args and args[0]:
            path=Path(args[0]);assert not path.is_absolute()or not path.resolve().is_relative_to(c.R)
    sys.addaudithook(audit_hook);sys.setprofile(profile)
    try:
        bootstrap=c.bootstrap();c.guard()
        import numpy as np
        parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json')
        assert parent['active_round']is None and parent['active_math_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==10
        source=c.read(c.BASE)['files'].copy()
        assert all(c.sha(c.R/name)==value for name,value in source.items())
        model_freeze=c.read(c.R/'runs/v1552_complete_canonical_witness/ENTRY_QUALIFICATION.json')
        assert model_freeze['passed']and model_freeze['models']==0
        old=c.R/'experiments/v1552_complete_canonical_witness'
        for file in ['owner.py','source_owner.py']:
            assert(C/file).read_bytes()==(old/file).read_bytes()
        module=c.load('v1554_real_lossless_stream',C/'stream.py')
        phases=c.load('v1554_current_phase_source',C/'witness.py')
        owner=c.load('v1554_current_once_owner',C/'owner.py')
        driver=c.load('v1554_current_production_CLI',C/'driver.py')
        codec=c.load('v1554_original_codec',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
        wm=c.load('v1554_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
        io=c.load('v1554_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
        method=c.read(c.R/'runs/v1550_canonical_observer_policy/source_target/RESPONSE_METHOD.json')
        fixed=dict(response_method_file_sha256=c.sha(c.R/'runs/v1550_canonical_observer_policy/source_target/RESPONSE_METHOD.json'),response_method_sha256=method['response_method_sha256'],setup_sha256=c.sha(c.SETUP),base_method_file_sha256=c.sha(c.INPUT),immutable_response_not_regenerated=True)
        c.put(c.O/'FIXED_INPUTS.json',fixed)
        order=phases.names(method)
        binding=phases.binding(method,'PYTHON_GENERATION',codec)
        binding['software_storage_only']=True
        shapes=dict(states=(1,8),ctrl=(0,4),memory=(1,5),modes=(1,3),gear=(1,3),encoders=(1,4),parked=(1,2),native=(1,),sim_time=(1,),raw_rows=(0,3),requested_body=(0,2),applied_body=(0,2),gear_proof=(0,10))
        arrays={key:np.zeros(shape,dtype=np.int64 if key in {'modes','gear','native'}else np.float64)for key,shape in shapes.items()}
        arrays['states'][0,0]=-0.
        arrays['states'][0,1]=np.nextafter(0.,1.)
        arrays['states'][0,2]=float('nan')
        # Signedzero/subnormal/error-NaN are preserved exactly by storage;
        # software safety placeholders do NOT claim model safety.
        proof=dict(safety=dict(passed=True,software_storage_placeholder=True),comparison=None)
        target=c.O/'source_target';target.mkdir()
        folder=target/'full';folder.mkdir()
        writer=wm.WriterBudget(folder,role='PLANNER',maximum_bytes=32*1024**2,source_identity=c.digest(source))
        negative=[]
        with io.OutputBoundary(folder,writer.reserve)as boundary:
            stream=module.Stream(folder,writer=writer,boundary=boundary,binding=binding,ordered_names=order)
            try:stream.save_data(order[1],arrays,accounting=dict(models=0),complete=True)
            except AssertionError:negative.append('fixed_record_order')
            else:raise AssertionError('OUT_OF_ORDER_DATA_ACCEPTED')
            for name in order:
                stream.save_data(name,arrays,accounting=dict(models=0,new_native=0,software_zero_length=True),complete=True)
                stream.save_proof(name,proof)
            stream.seal(generation_result_sha256='1'*64)
            reader=module.Reader(folder,expected_binding=binding,expected_result_sha256='1'*64,ordered_names=order)
            restored=reader.arrays('nominal')
            assert all(restored[key].dtype==value.dtype and restored[key].shape==value.shape and restored[key].tobytes()==value.tobytes()for key,value in arrays.items())
            # Reuse the one software stream; tiny reversible corruption does
            # not generate model arrays or duplicate the complete evidence.
            path=folder/'WITNESSES.bin'
            where=reader.offsets[order[0]][0]
            with path.open('r+b')as raw:
                raw.seek(where);original=raw.read(1);raw.seek(where);raw.write(bytes([original[0]^1]))
            try:module.Reader(folder,expected_binding=binding,expected_result_sha256='1'*64,ordered_names=order)
            except AssertionError:negative.append('actual_payload_corruption')
            else:raise AssertionError('CORRUPT_PAYLOAD_ACCEPTED')
            with path.open('r+b')as raw:raw.seek(where);raw.write(original)
            changed=copy.deepcopy(binding);changed['response_method_sha256']='0'*64
            try:module.Reader(folder,expected_binding=changed,expected_result_sha256='1'*64,ordered_names=order)
            except AssertionError:negative.append('wrong_response_identity')
            else:raise AssertionError('CHANGED_BINDING_ACCEPTED')
            try:module.Reader(folder,expected_binding=binding,expected_result_sha256='0'*64,ordered_names=order)
            except AssertionError:negative.append('wrong_success_result_SHA')
            else:raise AssertionError('CHANGED_RESULT_ACCEPTED')
            verified=module.Reader(folder,expected_binding=binding,expected_result_sha256='1'*64,ordered_names=order)
            assert len(verified.offsets)==563
        partial=target/'partial';partial.mkdir()
        partial_writer=wm.WriterBudget(partial,role='PLANNER',maximum_bytes=32*1024**2,source_identity=c.digest(source))
        with io.OutputBoundary(partial,partial_writer.reserve)as boundary:
            stream=module.Stream(partial,writer=partial_writer,boundary=boundary,binding=binding,ordered_names=order)
            stream.save_data(order[0],arrays,accounting=dict(models=0,confirmed_native=0,inflight_unknown=True),complete=False,first_error='SOFTWARE_SOURCE_ERROR')
            stream.emergency(order[0],arrays,first_error='SOFTWARE_SOURCE_ERROR',accounting=dict(models=0,inflight_unknown=True),nominal_prefix=arrays)
            abort=stream.abort(first_error='SOFTWARE_SOURCE_ERROR',accounting=dict(models=0,inflight_unknown=True))
            assert abort['first_error']=='SOFTWARE_SOURCE_ERROR'and abort['pending_complete']is False
            assert abort['acknowledged_data']==1 and abort['acknowledged_proofs']==0
            try:stream.emergency(order[0],arrays,first_error='retry',accounting={})
            except AssertionError:negative.append('emergency_retry_forbidden')
            else:raise AssertionError('EMERGENCY_RETRY_ACCEPTED')
        # Production missing-admission close only. Old numerical/origin/OS,
        # parentprecharge and model namespace suites are inherited by SHA.
        answer=driver.execute()
        assert answer['closed']and not answer['passed']and 'CANONICAL_NONZERO_PRIVATE_NOT_ADMITTED'in answer['first_error']
        assert not answer['generation_executed']and not answer['audit_executed']and not answer['secondary_errors']
        assert c.read(c.O/'unadmitted/RESULT.json')==answer
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            for path in C.iterdir():
                if path.is_file():
                    if path.suffix=='.py':ast.parse(path.read_text())
                    source[str(path.relative_to(c.R))]=c.sha(path)
            source[str((c.O/'FIXED_INPUTS.json').relative_to(c.R))]=c.sha(c.O/'FIXED_INPUTS.json')
            assert all(c.sha(c.R/name)==value for name,value in source.items())
            c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,
                source_only=True,models_authorized=False,complete_numeric_response_qualified=False),maximum=4*1024**2)
        c.put(target/'QUALIFICATION.json',dict(passed=True,software_only=True,models=0,all563_DATA_PROOF_records_verified=True,
            exact13array_bitwise=True,signed_zero_subnormal_nonfinite_bytes_preserved=True,negative_cases=negative,
            one_emergency_with_nominal_prefix_and_accurate_unknown=True,partial_not_sealed=True,
            actual_stream_bytes=(folder/'WITNESSES.bin').stat().st_size,writer_charged_bytes=writer._read()['charged_bytes'],
            partial_writer_charged_bytes=partial_writer._read()['charged_bytes'],production_missing_admission_saved=True,
            cap22MiB_source_bound_only_no_full_filling_fixture=True,compression_of_actual_response_not_tested=True))
        result.update(passed=True,source_frozen=True,source_members=len(source),bootstrap=bootstrap,
            source_only=True,negative_cases=len(negative),writer_charged_bytes=writer._read()['charged_bytes'],
            stream_bytes=(folder/'WITNESSES.bin').stat().st_size)
    except BaseException as error:
        result.update(passed=False,first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder)
        result.update(closed=True,wall_s=time.monotonic()-start)
        c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
