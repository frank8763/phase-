"""Necessary complete-witness source/production-save qualification, zero models.

Only the new13array/scoped-writer/partial-error interface executes. No old
definition/origin/Gear/OS/ROS or closed numerical suite is requalified.
"""
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
spec=importlib.util.spec_from_file_location('v1552_target_common',C/'common.py')
c=importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def main():
    start=time.monotonic()
    assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as stream:
        json.dump(dict(unix=time.time(),models=0,revision=10),stream)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,
                phase_FFI_loads=0,Allocator_recomputations=0,optimizer_calls=0,replay_native=0)

    class NoModelImports(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'jax','jaxlib','mujoco','torch','rclpy','runtime','bindings','kernel','prediction','coupled_model','vehicle','factory','gear_handoff'}:
                raise AssertionError('COMPLETE_WITNESS_SOURCE_TARGET_NO_MODEL_IMPORT:'+name)
    finder=NoModelImports()
    sys.meta_path.insert(0,finder)
    def audit_hook(event,args):
        if event=='ctypes.dlopen'and args and args[0]:
            path=Path(args[0])
            assert not path.is_absolute()or not path.resolve().is_relative_to(c.R),'SOURCE_TARGET_PHASE_FFI_FORBIDDEN'
    sys.addaudithook(audit_hook)

    def profile(frame,event,arg):
        if event=='call':
            path=Path(frame.f_code.co_filename)
            if path.is_absolute()and path.is_relative_to(c.R):
                assert frame.f_code.co_name not in {'step','select','simulate','compute','predict','expand','advance','load_definitions'}, 'SOURCE_TARGET_NUMERICAL_CALL'
                if frame.f_code.co_name=='__init__'and not path.is_relative_to(C):
                    assert path in {c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}, 'SOURCE_TARGET_MODEL_CONSTRUCTOR'
            assert time.monotonic()-start<120

    sys.setprofile(profile)
    try:
        bootstrap=c.bootstrap()
        c.guard()
        import numpy as np
        parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json')
        assert parent['active_round']is None and parent['active_math_round']is None
        assert parent['models_now_authorized']is False and parent['scientific_revisions']==10
        source=c.read(c.BASE)['files'].copy()
        assert all(c.sha(c.R/name)==identity for name,identity in source.items())
        storage=c.load('v1552_real_multiscope_storage',C/'storage.py')
        evidence=c.load('v1552_real_response_array_storage',C/'evidence.py')
        owner=c.load('v1552_real_metadata_owner',C/'owner.py')
        capability=c.load('v1552_real_capability_definition',C/'capability.py')
        # Import only new interface definitions; no old model/FFI imports.
        for name in ['gates','witness','origin','driver']:
            c.load('v1552_definition_'+name,C/(name+'.py'))
        codec=c.load('v1552_original_codec',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
        io=c.load('v1552_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
        wm=c.load('v1552_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
        method=c.read(c.R/'runs/v1550_canonical_observer_policy/source_target/RESPONSE_METHOD.json')
        layout=storage.plan(method['fixed_boundaries'])
        limits=c.limits()
        assert limits['model_writer_bytes']==layout['model_writer_bytes']==1132503040
        assert len(layout['scopes'])==limits['maximum_scopes']==567
        assert max(layout['scopes'].values())<32*1024**2
        assert sum(limits[key]for key in ['initialization_s','generation_s','audit_s','closure_reserve_s','slack_s'])==5400
        assert sum(limits[key]for key in ['evidence_bytes','archive_bytes','download_bytes','root_reserve_bytes'])==2904637440
        fixed=dict(response_method_file_sha256=c.sha(c.R/'runs/v1550_canonical_observer_policy/source_target/RESPONSE_METHOD.json'),
                   response_method_sha256=method['response_method_sha256'],setup_sha256=c.sha(c.SETUP),
                   base_method_file_sha256=c.sha(c.INPUT),unchanged_base_input=True)
        c.put(c.O/'FIXED_INPUTS.json',fixed)
        target=c.O/'source_target'
        target.mkdir()
        writer=wm.WriterBudget(target,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.digest(source))
        with io.OutputBoundary(target,writer.reserve):
            codec.write_atomic(target/'STORAGE_PLAN.json',codec.encoded(dict(plan=layout,limits=limits,metadata_only=True,models=0)),writer)
        root=target/'model'
        root.mkdir()
        scoped=storage.Storage(root,source_identity=c.digest(source),fixed_plan=layout,purpose='SOURCE_STORAGE_ONLY')

        class SoftwareSnapshot:
            def snapshot(self):
                return dict(state=np.zeros(8),memory=np.zeros(5),modes=[0,0,0],gear=[1,6004,-1],
                            encoders=[0.,0.,0.,0.],parked_target=None,native=6005,sim_time=60.05)
        branch=evidence.Branch(SoftwareSnapshot())
        # Explicit two software rows exercise only NEW13array storage fields.
        # There is no predictor, Gear.select, simulated state or model counter.
        for index in range(2):
            before=copy.deepcopy(branch.origin if not branch.rows else branch.rows[-1]['after'])
            after=copy.deepcopy(before)
            after['native']+=1;after['sim_time']+=.01
            after['gear']=[1,before['native'],-1]
            branch.rows.append(dict(before=before,after=after,raw=(0.,0.,0),requested=(0.,0.),applied=(0.,0.),ctrl=np.zeros(4),
                gear_proof=dict(requested_gear=0,prior_gear=1,drive_gear=0,measured_body_gear=0,
                     brake_start=None,measured_rest=True,braking_native=0,mode='UNCHANGED',released=False)))
        negative=[]
        with io.OutputBoundary(root,scoped.reserve)as boundary:
            arrays,receipt=evidence.save_before_gate(branch,folder=root/'generation/b000',name='software_complete',
                 writer=scoped,method=method,expected_native=2,accounting=dict(models=0,analytical_native=0,software_only=True))
            assert receipt['complete']and receipt['acknowledged_saved_native']==2
            assert set(arrays)=={'states','memory','modes','gear','encoders','parked','native','sim_time','ctrl','raw_rows','requested_body','applied_body','gear_proof'}
            assert sum(value.nbytes for value in arrays.values())==storage.raw_bytes(2)
            # Re-saving the same completed branch is forbidden, including if a
            # receipt or gate later failed; this protects the fixed byte cap.
            try:
                evidence.save_before_gate(branch,folder=root/'generation/b000',name='duplicate',writer=scoped,method=method,expected_native=2,accounting={})
            except AssertionError as error:
                assert str(error)=='BRANCH_PERSISTENCE_ALREADY_ATTEMPTED'
                negative.append('duplicate_full_array_write')
            else:
                raise AssertionError('DUPLICATE_COMPLETE_ARRAY_SAVE_ACCEPTED')
            partial=evidence.Branch(SoftwareSnapshot())
            partial.rows=copy.deepcopy(branch.rows)
            _,partial_receipt=evidence.save_before_gate(partial,folder=root/'audit/b000',name='software_partial',
                 writer=scoped,method=method,expected_native=2,accounting=dict(models=0,confirmed_native=2,inflight_unknown=True),first_error='SOFTWARE_POSTSTEP_SNAPSHOT_FAILURE')
            assert partial_receipt['complete']is False and partial_receipt['acknowledged_saved_native']==2
            assert partial_receipt['model_counts']['inflight_unknown']is True
            try:
                (root/'undeclared'/'unexpected.bin').write_bytes(b'not permitted')
            except AssertionError as error:
                assert str(error)=='UNDECLARED_NONZERO_EVIDENCE_SCOPE'
                negative.append('undeclared_scope')
            else:
                raise AssertionError('UNDECLARED_SCOPE_WRITTEN')
            try:
                boundary.charge(root/'generation/b000'/'oversized.bin',layout['scopes']['generation/b000'])
            except AssertionError as error:
                assert str(error)=='CHILD_OUTPUT_BYTE_CAP_EXHAUSTED'
                negative.append('original_per_scope_cap_preserved')
            else:
                raise AssertionError('SCOPE_COUNTER_CAP_ACCEPTED')
        record=dict(passed=True,software_only=True,models=0,source_storage_only=True,negative_cases=negative,
                    fixed_all_scopes_reserved_bytes=layout['model_writer_bytes'],storage_accounting=scoped.accounting(),
                    complete13array_roundtrip=True,poststep_partial_counts_separate_from_saved_rows=True,
                    branch_error_with_equal_rows_is_incomplete=True)
        with io.OutputBoundary(target,writer.reserve):
            codec.write_atomic(target/'SCOPED_STORAGE_PROOF.json',codec.encoded(record),writer)
        # Exact new once-owner prepayment; no control file is actually written.
        charge_target=target/'parent_precharge'
        charge_target.mkdir()
        parent_writer=wm.WriterBudget(charge_target,role='SUPERVISOR_LOG',maximum_bytes=limits['parent_writer_bytes'],source_identity=c.digest(source))
        original=(c.O/'SOURCE_REVIEW_ORIGINAL.bin').read_bytes()
        assert __import__('hashlib').sha256(original).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
        owner.reserve_parent_budget(parent_writer,original,limits)
        assert parent_writer._read()['charged_bytes']<=limits['parent_writer_bytes']
        assert len(owner.parent_bytes(parent))+8192<=131072
        positive=dict(passed=True,closed=True,first_error=None,secondary_errors=[],generation_inflight_unknown=False,audit_inflight_unknown=False,
             generation_analytical_native=1263600,audit_analytical_native=1263600,cpp_engine_constructions=1,python_predictor_constructions=1,
             physical_native=0,replay_native=0,optimizer_calls=0,physical_capture_native=0,model_construction_inflight={'gen':None,'audit':None},
             accounting=dict(stages={stage:dict(nominal_native=13600,witness_native=1250000,copy=562)for stage in ['PYTHON_GENERATION','CPP_AUDIT']}))
        assert owner.runtime_passed(0,positive,[])
        damaged=copy.deepcopy(positive);damaged['model_construction_inflight']['audit']='Engine'
        assert not owner.runtime_passed(0,damaged,[])
        damaged=copy.deepcopy(positive);damaged['accounting']['stages']['CPP_AUDIT']['nominal_native']=0
        assert not owner.runtime_passed(0,damaged,[])
        # Run actual NEW production CLI in-process after releasing qualifier
        # locks. Missing admission must close before any numerical import.
        driver=c.load('v1552_actual_unadmitted_driver',C/'driver.py')
        answer=driver.execute()
        assert answer['closed']and answer['passed']is False
        assert 'CANONICAL_NONZERO_PRIVATE_NOT_ADMITTED'in answer['first_error']
        assert not answer['generation_executed']and not answer['audit_executed']
        assert answer['generation_analytical_native']==answer['audit_analytical_native']==0
        saved=c.read(c.O/'unadmitted/RESULT.json')
        assert saved==answer and answer['secondary_errors']==[]
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            for path in C.iterdir():
                if path.is_file():
                    if path.suffix=='.py':ast.parse(path.read_text())
                    source[str(path.relative_to(c.R))]=c.sha(path)
            source[str((c.O/'FIXED_INPUTS.json').relative_to(c.R))]=c.sha(c.O/'FIXED_INPUTS.json')
            assert all(c.sha(c.R/name)==identity for name,identity in source.items())
            c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,
                  source_only=True,models_authorized=False,complete_numeric_response_qualified=False),maximum=4*1024**2)
        result.update(passed=True,bootstrap=bootstrap,source_frozen=True,source_members=len(source),
                      new_storage_negatives=len(negative),source_writer_charged_bytes=writer._read()['charged_bytes'],
                      parent_prepaid_bytes=parent_writer._read()['charged_bytes'],production_missing_admission_saved=True,
                      original_suites_not_rerun=True)
    except BaseException as error:
        result.update(passed=False,first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None)
        sys.meta_path.remove(finder)
        result.update(closed=True,wall_s=time.monotonic()-start)
        c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1


if __name__=='__main__':
    raise SystemExit(main())
