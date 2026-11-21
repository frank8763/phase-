"""New response-identity/API target only; no original policy/model calls."""
import ast
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
spec=importlib.util.spec_from_file_location('v1550_source_common',C/'common.py')
c=importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def main():
    start=time.monotonic()
    assert sorted(os.sched_getaffinity(0))==[5] and os.environ.get('PHASE_REPO')==str(c.R)
    with (c.O/'ENTRY_ONCE_CLAIM.json').open('x') as stream:
        json.dump(dict(unix=time.time(),models=0,revision=10),stream)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,
                phase_FFI_loads=0,Allocator_recomputations=0,original_policy_calls=0,
                optimizer_calls=0,replay_native=0,nonzero_response_executed=False)

    class NoNumerics(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0] in {'numpy','jax','jaxlib','mujoco','torch','rclpy','ctypes','runtime','bindings','kernel','prediction','coupled_model','vehicle','factory','gear_handoff'}:
                raise AssertionError('NONZERO_SOURCE_TARGET_NO_NUMERICAL_IMPORT:'+name)

    finder=NoNumerics()
    sys.meta_path.insert(0,finder)

    def profile(frame,event,arg):
        if event=='call':
            path=Path(frame.f_code.co_filename)
            forbidden={'select','step','compute','simulate','predict','expand','advance','fork','create','load_definitions'}
            if path.is_absolute() and path.is_relative_to(c.R):
                assert frame.f_code.co_name not in forbidden, 'NONZERO_SOURCE_TARGET_POLICY_OR_MODEL_CALL'
                if frame.f_code.co_name=='__init__' and not path.is_relative_to(C):
                    assert path in {c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}
            assert time.monotonic()-start<120

    sys.setprofile(profile)
    try:
        bootstrap=c.bootstrap()
        c.guard()
        with (c.R/'runs/v648_static_unknown/execution.lock').open() as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json')
            assert parent['scientific_revisions']==10 and parent['active_round'] is None
            assert parent['active_math_round'] is None and parent['models_now_authorized'] is False
            source=c.read(c.BASE)['files'].copy()
            assert all(c.sha(c.R/name)==identity for name,identity in source.items())
            reg='runs/v1550_canonical_observer_policy/SCIENTIFIC_REVISION_REGISTRATION.json'
            registration_sha=c.sha(c.R/reg)
            m=c.load('v1550_new_method_identity',C/'method.py')
            cap=c.load('v1550_real_production_capability',C/'capability.py')
            # Import definitions only, while the numerical-call ban is active.
            c.load('v1550_new_continuous_trajectory_definitions',C/'trajectory.py')
            c.load('v1550_new_evidence_definitions',C/'evidence.py')
            wm=c.load('v1550_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
            io=c.load('v1550_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
            codec=c.load('v1550_original_codec',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
            target=c.O/'source_target'
            target.mkdir()
            writer=wm.WriterBudget(target,role='PLANNER',maximum_bytes=1024**2,source_identity=c.digest(source))
            with io.OutputBoundary(target,writer.reserve):
                def save(name,value):
                    codec.write_atomic(target/name,codec.encoded(value),writer)
                method=m.prepare(prepared_sources=source,registration_sha256=registration_sha,
                                 save_proof=lambda value:save('METHOD_BINDING_PROOF.json',value))
                save('RESPONSE_METHOD.json',method)
                assert method['base_method_semantic_sha256']==m.BASE_SEMANTIC_SHA
                assert method['base_method_file_sha256']==m.BASE_FILE_SHA
                assert method['scientific_integration_revision']==10
                assert method['model_permission'] is method['physical_permission'] is method['replay_permission'] is False
                assert method['extra_gear_hold_ticks']==0 and method['raw_requests_are_not_applied_controls']
                assert method['plan']['compressed_evidence_or_archive_peak_bound'] is None
                negatives=[]
                # New response-method registration and immutable base binding,
                # not a rerun of old Gear/definition/origin qualification.
                for label,changed,regsha in [
                    ('wrong_registration',source,'0'*64),
                    ('changed_base_method',{**source,m.BASE:'0'*64},registration_sha),
                    ('changed_scalar_source',{**source,m.FEEDBACK:'0'*64},registration_sha)]:
                    saved=[]
                    def refusal(value):
                        save(label+'.json',value)
                        saved.append(value)
                    try:
                        m.prepare(prepared_sources=changed,registration_sha256=regsha,save_proof=refusal)
                    except m.MethodRefusal as error:
                        assert saved and not saved[0]['passed'] and saved[0]==error.proof
                        negatives.append(label)
                    else:
                        raise AssertionError('NONZERO_METHOD_CHANGED_BINDING_ACCEPTED')
                def unavailable(value):
                    raise OSError('NEW_NONZERO_METHOD_PROOF_SAVE_ERROR')
                try:
                    m.prepare(prepared_sources=source,registration_sha256='0'*64,save_proof=unavailable)
                except m.MethodRefusal as error:
                    assert 'NONZERO_METHOD_REGISTRATION_CHANGED' in str(error)
                    assert 'NEW_NONZERO_METHOD_PROOF_SAVE_ERROR' in error.secondary
                    save('FIRST_SECONDARY.json',dict(first_error=str(error),secondary=error.secondary,proof=error.proof))
                else:
                    raise AssertionError('NONZERO_METHOD_FIRST_ERROR_LOST')
                try:
                    cap.Guard(lock=lock,method_input_sha256=method['response_method_sha256'],prepared_sources=source)
                except AssertionError as error:
                    assert str(error)=='CANONICAL_NONZERO_PRIVATE_NOT_ADMITTED'
                    save('PRODUCTION_ADMISSION_REFUSAL.json',dict(passed=True,first_error=str(error),models=0,
                         reached_before_CPU2_or_numerical_binding=True,not_model_or_response_qualification=True))
                else:
                    raise AssertionError('NONZERO_PRIVATE_MISSING_ADMISSION_ACCEPTED')
                save('QUALIFICATION.json',dict(passed=True,models=0,original_policy_calls=0,
                     new_method_binding_negatives=negatives,first_secondary_saved=True,
                     explicit_method_revision=10,not_scalar_numerical_equivalence=True,
                     complete_response_witness_numeric_qualified=False,physical_navigation=False,
                     original_definition_origin_Gear_OS_ROS_suites_reused_not_rerun=True))
            source[reg]=registration_sha
            for path in C.iterdir():
                if path.is_file():
                    if path.suffix=='.py':
                        ast.parse(path.read_text())
                    source[str(path.relative_to(c.R))]=c.sha(path)
            assert all(c.sha(c.R/name)==identity for name,identity in source.items())
            c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,
                  no_nonzero_model_or_physical_admission=True),maximum=4*1024**2)
            result.update(passed=True,source_frozen=True,bootstrap=bootstrap,
                          source_only=True,source_members=len(source),negative_cases=len(negatives),
                          writer_charged_bytes=writer._read()['charged_bytes'])
    except BaseException as error:
        result.update(passed=False,first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None)
        sys.meta_path.remove(finder)
        result.update(closed=True,wall_s=time.monotonic()-start)
        c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
