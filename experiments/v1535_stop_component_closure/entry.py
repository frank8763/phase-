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
            expected=(old/'origin.py').read_text().replace("=='v1532_observer_epoch_origin'","=='v1535_stop_component_closure'")
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
            writer=writer_module.WriterBudget(task,role='PLANNER',maximum_bytes=1024**2,source_identity=c.digest(source));cases=[]
            with boundary.OutputBoundary(task,writer.reserve):
                def put(name,value):codec.write_atomic(task/name,codec.encoded(value),writer)
                # Actual new production helper handles a late failure after
                # success; every count below is explicitly software metadata.
                value=dict(passed=True,software_metadata_only=True);secondary=[]
                first=driver.record_failure(value,AssertionError('SOFTWARE_LATE_SOURCE_CHANGED'),None,secondary)
                assert value['passed']is False and 'SOFTWARE_LATE_SOURCE_CHANGED'in first
                put('LATE_SOURCE_FAILURE.json',dict(result=value,first_error=first,secondary=secondary,models=0))
                value=dict(passed=True);secondary=[];error=AssertionError('SOFTWARE_LATER_ERROR');error.secondary='SOFTWARE_SECONDARY_SAVE_ERROR'
                first=driver.record_failure(value,error,'SOFTWARE_ORIGINAL_FIRST',secondary)
                assert value['passed']is False and first=='SOFTWARE_ORIGINAL_FIRST'and secondary==['origin_save:SOFTWARE_SECONDARY_SAVE_ERROR']
                put('FIRST_AND_SECONDARY_RETAINED.json',dict(result=value,first_error=first,secondary=secondary,models=0))
                good=dict(closed=True,passed=True,first_error=None,secondary_errors=[],generation_inflight_unknown=False,audit_inflight_unknown=False,
                          generation_analytical_native=200,audit_analytical_native=200,cpp_engine_constructions=1,python_predictor_constructions=1,
                          physical_native=0,ownreplay_native=0,optimizer_calls=0,nominal_native=0,software_metadata_only=True)
                assert owner.runtime_passed(0,good,[])
                for key,new in [('first_error','SOFTWARE_FIRST'),('secondary_errors',['SOFTWARE_SAVE']),('generation_inflight_unknown',True),('audit_inflight_unknown',True),('audit_analytical_native',199),('generation_analytical_native',200.),('cpp_engine_constructions',None),('python_predictor_constructions',True),('physical_native',1),('closed',False)]:
                    changed=copy.deepcopy(good);changed[key]=new;assert not owner.runtime_passed(0,changed,[]);cases.append(dict(field=key,rejected=True))
                for key in ['first_error','secondary_errors','generation_inflight_unknown','audit_inflight_unknown']:
                    changed=copy.deepcopy(good);del changed[key];assert not owner.runtime_passed(0,changed,[]);cases.append(dict(missing=key,rejected=True))
                assert not owner.runtime_passed(1,good,[])and not owner.runtime_passed(0,good,['SOFTWARE_PARENT_SAVE'])and not owner.runtime_passed(False,good,[])
                put('OWNER_ACCEPTANCE.json',dict(passed=True,negative_cases=cases,exit_and_parent_secondary_rejected=True,
                    software200_values_not_executed_model_work=True,models=0))
            parent_writer=writer_module.WriterBudget(task,role='SUPERVISOR_LOG',maximum_bytes=1024**2,source_identity=c.digest(source))
            owner.reserve_parent_budget(parent_writer,(c.R/'REVIEW_PENDING').read_bytes(),c.limits())
            assert parent_writer._read()['charged_bytes']==963327<=1024**2
            assert len(owner.parent_bytes(parent))+8192<=131072
            fixed=c.read(prior/'FIXED_INPUTS.json');c.put(c.O/'FIXED_INPUTS.json',fixed)
            assert c.sha(c.INPUT)==fixed['method_input_file_sha256']
            for path in C.iterdir():
                if path.is_file():source[str(path.relative_to(c.R))]=c.sha(path)
            for path in [c.O/'FIXED_INPUTS.json',prior/'ENTRY_QUALIFICATION.json',prior/'ORIGIN_API_QUALIFICATION.json',prior/'PRELAUNCH_CLOSURE_SOURCE_GAP.json']:
                source[str(path.relative_to(c.R))]=c.sha(path)
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
