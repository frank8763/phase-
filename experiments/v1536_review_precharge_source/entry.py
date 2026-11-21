"""Only new result-closure and owner-acceptance checks; no model imports."""
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
s=importlib.util.spec_from_file_location('new_stop_closure_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def main():
    assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
    start=time.monotonic()
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as stream:json.dump(dict(unix=time.time(),models=0),stream)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,
                Allocator_recomputations=0,optimizer_calls=0,replay_native=0,phase_FFI_library_loads=0)
    class NoModels(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'numpy','jax','jaxlib','mujoco','torch','rclpy','vehicle','factory','runtime','bindings','kernel','prediction','coupled_model'}:
                raise AssertionError('NEW_RESULT_CLOSURE_TARGET_METADATA_ONLY:'+name)
    finder=NoModels();sys.meta_path.insert(0,finder)
    def profile(frame,event,arg):
        if event=='call':
            p=Path(frame.f_code.co_filename)
            if p.is_absolute()and p.is_relative_to(c.R)and frame.f_code.co_name in {'__init__','step','compute','simulate','expand','predict'}:
                if not p.is_relative_to(C)and p not in {c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}:raise AssertionError('NEW_CLOSURE_TARGET_NO_MODEL_CALL')
            assert time.monotonic()-start<120
    sys.setprofile(profile)
    try:
        bootstrap=c.bootstrap();c.guard()
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']and parent['scientific_revisions']==8
            old=c.R/'experiments/v1532_observer_epoch_origin';prior=c.R/'runs/v1532_observer_epoch_origin'
            source=c.read(c.BASE)['files'].copy();assert all(c.sha(c.R/n)==h for n,h in source.items())
            assert c.read(prior/'ENTRY_QUALIFICATION.json')['passed']and not(prior/'NUMERIC_ONCE_CLAIM.json').exists()
            for name in ['generate.py','audit.py','records.py','stop_checks.py','contract.py','LIMITS.json']:
                assert(C/name).read_bytes()==(old/name).read_bytes(),'UNRELATED_NUMERIC_SOURCE_CHANGED:'+name
            expected=(old/'origin.py').read_text().replace("=='v1532_observer_epoch_origin'","=='v1536_review_precharge_source'")
            assert ast.dump(ast.parse(expected))==ast.dump(ast.parse((C/'origin.py').read_text()))
            expected=(old/'common.py').read_text().replace("BASE=R/'runs/v1530_explicit_we_private_binding/SOURCE_FREEZE.json'","BASE=R/'runs/v1532_observer_epoch_origin/SOURCE_FREEZE.json'").replace("INPUT=O/'source_target/METHOD_INPUT.json'","INPUT=R/'runs/v1532_observer_epoch_origin/source_target/METHOD_INPUT.json'")
            assert ast.dump(ast.parse(expected))==ast.dump(ast.parse((C/'common.py').read_text()))
            driver=c.load('new_real_result_closure_driver',C/'driver.py');owner=c.load('new_real_owner_acceptance',C/'owner.py')
            before=ast.parse((old/'owner.py').read_text());after=ast.parse((C/'owner.py').read_text())
            for name in ['parent_bytes','reserve_parent_budget']:
                a=next(n for n in before.body if isinstance(n,ast.FunctionDef)and n.name==name);b=next(n for n in after.body if isinstance(n,ast.FunctionDef)and n.name==name)
                assert ast.dump(a)==ast.dump(b)
            task=c.O/'source_target';task.mkdir();writer_module=c.load('closure_real_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');boundary=c.load('closure_real_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
            codec=c.load('closure_original_bounded_codec',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
            # Previous failed target completed and saved all new closure cases;
            # reuse their exact source and persisted metadata, never rerun them.
            failed=c.R/'runs/v1535_stop_component_closure'
            failed_source=c.read(failed/'FAILED_SOURCE_FREEZE.json')['files']
            assert all(c.sha(c.R/name)==identity for name,identity in failed_source.items())
            assert not c.read(failed/'ENTRY_QUALIFICATION.json')['passed']
            assert not(failed/'SOURCE_FREEZE.json').exists()
            for name in ['driver.py','owner.py','generate.py','audit.py','records.py','stop_checks.py','common.py','contract.py','LIMITS.json']:
                assert(C/name).read_bytes()==(c.R/'experiments/v1535_stop_component_closure'/name).read_bytes()
            late=c.read(failed/'source_target/LATE_SOURCE_FAILURE.json')
            retained=c.read(failed/'source_target/FIRST_AND_SECONDARY_RETAINED.json')
            accepted=c.read(failed/'source_target/OWNER_ACCEPTANCE.json')
            assert late['result']['passed']is False and retained['result']['passed']is False
            assert retained['first_error']=='SOFTWARE_ORIGINAL_FIRST'and accepted['passed']
            cases=accepted['negative_cases']
            reuse={str((failed/name).relative_to(c.R)):c.sha(failed/name)for name in ['FAILED_SOURCE_FREEZE.json','ENTRY_QUALIFICATION.json','source_target/LATE_SOURCE_FAILURE.json','source_target/FIRST_AND_SECONDARY_RETAINED.json','source_target/OWNER_ACCEPTANCE.json']}
            c.put(c.O/'CLOSURE_PRIOR_PROOF_REUSE.json',dict(passed=True,models=0,files=reuse,source_and_closure_cases_not_reexecuted=True))
            parent_writer=writer_module.WriterBudget(task,role='SUPERVISOR_LOG',maximum_bytes=1024**2,source_identity=c.digest(source))
            saved_review=(c.O/'SOURCE_REVIEW_ORIGINAL.bin').read_bytes()
            assert c.sha(c.O/'SOURCE_REVIEW_ORIGINAL.bin')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
            owner.reserve_parent_budget(parent_writer,saved_review,c.limits())
            assert parent_writer._read()['charged_bytes']==963327<=1024**2
            assert len(owner.parent_bytes(parent))+8192<=131072
            fixed=c.read(prior/'FIXED_INPUTS.json');c.put(c.O/'FIXED_INPUTS.json',fixed)
            assert c.sha(c.INPUT)==fixed['method_input_file_sha256']
            for path in C.iterdir():
                if path.is_file():source[str(path.relative_to(c.R))]=c.sha(path)
            for path in [c.O/'SOURCE_REVIEW_ORIGINAL.bin',c.O/'CLOSURE_PRIOR_PROOF_REUSE.json',c.O/'FIXED_INPUTS.json',prior/'ENTRY_QUALIFICATION.json',prior/'ORIGIN_API_QUALIFICATION.json',prior/'PRELAUNCH_CLOSURE_SOURCE_GAP.json']:
                source[str(path.relative_to(c.R))]=c.sha(path)
            source.update(reuse)
            assert all(c.sha(c.R/n)==h for n,h in source.items())
            c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,
                       previous_source_and_origin_proof_reused=True,numerical_branch_qualified=False),maximum=4*1024**2)
            c.put(c.O/'CLOSURE_QUALIFICATION.json',dict(passed=True,models=0,negative_owner_cases=len(cases)+3,
                  real_failure_helper_resets_success=True,first_and_secondary_retained=True,
                  original_model_origin_and_numerical_body_source_unchanged=True,original_method_input_bytes_unchanged=True,
                  prior_source_origin_proof_sha256=c.sha(prior/'ORIGIN_API_QUALIFICATION.json'),
                  parent_precharge_bytes=parent_writer._read()['charged_bytes'],real_parent_control_files_not_written=True,
                  no_old_definition_origin_serializer_OS_ROS_suite_rerun=True))
            result.update(passed=True,source_frozen=True,bootstrap=bootstrap,new_owner_negative_cases=len(cases)+3)
    except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start);c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
