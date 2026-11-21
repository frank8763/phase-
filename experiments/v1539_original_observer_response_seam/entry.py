"""One metadata-only current-component scope and receipt target."""
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
s=importlib.util.spec_from_file_location('v1539_source_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def main():
    start=time.monotonic();assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as stream:json.dump(dict(unix=time.time(),models=0),stream)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,
                phase_FFI_loads=0,Allocator_recomputations=0,optimizer_calls=0,replay_native=0)
    class NoNumerics(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'numpy','jax','jaxlib','mujoco','torch','rclpy','vehicle','factory','runtime','bindings','kernel','prediction','coupled_model'}:
                raise AssertionError('COMPONENT_RECEIPT_METADATA_ONLY:'+name)
    finder=NoNumerics();sys.meta_path.insert(0,finder)
    def profile(frame,event,arg):
        if event=='call':
            path=Path(frame.f_code.co_filename)
            if path.is_absolute()and path.is_relative_to(c.R)and frame.f_code.co_name in {'__init__','step','compute','simulate','expand','predict'}:
                if not path.is_relative_to(C)and path not in {c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}:
                    raise AssertionError('COMPONENT_RECEIPT_NO_NUMERIC_CALL')
            assert time.monotonic()-start<120
    sys.setprofile(profile)
    try:
        bootstrap=c.bootstrap();c.guard()
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json')
            assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']and parent['scientific_revisions']==8
            source=c.read(c.BASE)['files'].copy();assert all(c.sha(c.R/n)==h for n,h in source.items())
            prepared=source.copy()
            roots=['runs/v1536_review_precharge_source/CURRENT_SOURCE_REMOTE_RECOVERY.json',
                   'runs/v1536_review_precharge_source/SOURCE_FREEZE.json',
                   'runs/v1537_stop_closure_source_recovery/FULL_REMOTE_VERIFIED.json',
                   'runs/v1538_stop_runtime_recovery/FULL_REMOTE_VERIFIED.json',
                   'runs/v1538_stop_runtime_recovery/ARCHIVE_INDEX.json',
                   'runs/v1536_review_precharge_source/COMPLETION.json',
                   'runs/v1536_review_precharge_source/model/RESULT.json',
                   'runs/v1536_review_precharge_source/model/INDEPENDENT_COMPARISON.json',
                   'runs/v1536_review_precharge_source/model/CPP_BRANCH_SAVED.json',
                   'runs/v1536_review_precharge_source/model/PYTHON_BRANCH_SAVED.json',
                   'runs/v1536_review_precharge_source/model/CPP_COMPLETE_STOP.npz',
                   'runs/v1536_review_precharge_source/model/PYTHON_COMPLETE_STOP.npz']
            for n in roots:prepared[n]=c.sha(c.R/n)
            module=c.load('v1539_real_component_receipt',C/'component_receipt.py')
            wm=c.load('v1539_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
            io=c.load('v1539_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
            codec=c.load('v1539_original_codec',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
            task=c.O/'source_target';task.mkdir()
            writer=wm.WriterBudget(task,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.digest(prepared))
            with io.OutputBoundary(task,writer.reserve):
                def save(name,value):codec.write_atomic(task/name,codec.encoded(value),writer)
                positive=module.read_component(prepared_sources=prepared,requested_scope='READ_CLOSED_COMPONENT_ONLY',save_proof=lambda value:save('COMPONENT_FACTS.json',value))
                assert positive['passed']and positive['component_generation_native']==positive['component_independent_audit_native']==200
                assert all(positive[k]is False for k in ['original_observer_search_authorized','models_authorized','physical_authorized','freshwire_authorized','whole_route_qualified','complete_original_stop_permission'])
                assert all(p['original_complete_stop_native']==2200 for p in positive['original_stop_requirements'])
                cases=[]
                def refused(name,values,scope):
                    saved=[]
                    def sink(proof):save(name+'.json',proof);saved.append(proof)
                    try:module.read_component(prepared_sources=values,requested_scope=scope,save_proof=sink)
                    except module.ComponentDomainRefusal as error:
                        assert saved and saved[0]['passed']is False and error.proof==saved[0]and error.secondary is None
                        cases.append(dict(name=name,first_error=str(error),saved_before_refusal=True))
                    else:raise AssertionError('COMPONENT_SCOPE_NEGATIVE_ACCEPTED:'+name)
                for scope in ['ORIGINAL_OBSERVER_SEARCH','ORIGINAL2200_STOP','FRESHWIRE','ACTUAL_CONTROL']:
                    refused('SCOPE_'+scope,prepared,scope)
                for name,key in [('CHANGED_ARRAY','runs/v1536_review_precharge_source/model/CPP_COMPLETE_STOP.npz'),
                                 ('CHANGED_RESULT','runs/v1536_review_precharge_source/model/RESULT.json'),
                                 ('CHANGED_ORIGINAL','experiments/v1186_live_observer_regeneration/stop_certificates.py'),
                                 ('CHANGED_REMOTE_INDEX','runs/v1538_stop_runtime_recovery/ARCHIVE_INDEX.json')]:
                    values=prepared.copy();values[key]='0'*64;refused(name,values,'READ_CLOSED_COMPONENT_ONLY')
                values=prepared.copy();del values['runs/v1536_review_precharge_source/model/PYTHON_COMPLETE_STOP.npz'];refused('MISSING_ARRAY_IDENTITY',values,'READ_CLOSED_COMPONENT_ONLY')
                # Exact first plus secondary save failure is a new target of
                # this receipt permission seam, no old suite is rerun.
                def fail_save(proof):raise OSError('SOFTWARE_COMPONENT_PROOF_SAVE_ERROR')
                try:module.read_component(prepared_sources=prepared,requested_scope='ACTUAL_CONTROL',save_proof=fail_save)
                except module.ComponentDomainRefusal as error:
                    assert 'COMPONENT200_NOT_ORIGINAL2200'in str(error)and 'SOFTWARE_COMPONENT_PROOF_SAVE_ERROR'in error.secondary
                    assert error.proof['passed']is False
                    save('FIRST_AND_SECONDARY.json',dict(first_error=str(error),secondary=error.secondary,proof=error.proof,models=0))
                else:raise AssertionError('COMPONENT_FIRST_SAVE_FAILURE_LOST')
                try:module.read_component(prepared_sources=prepared,requested_scope='READ_CLOSED_COMPONENT_ONLY',save_proof=fail_save)
                except module.ComponentDomainRefusal as error:
                    assert str(error)=='COMPONENT_RECEIPT_PROOF_SAVE_FAILED'and error.proof['passed']is False
                    save('POSITIVE_PROOF_SAVE_FAILURE.json',dict(first_error=str(error),secondary=error.secondary,models=0))
                else:raise AssertionError('COMPONENT_POSITIVE_SAVE_FAILURE_ACCEPTED')
                save('QUALIFICATION.json',dict(passed=True,models=0,negative_cases=cases,secondary_cases=2,
                     readonly_saved_arrays_not_model_replay=True,no_original_source_import=True,new_model_steps=0))
            source.update({n:prepared[n]for n in roots})
            for p in C.iterdir():
                if p.is_file():source[str(p.relative_to(c.R))]=c.sha(p)
            assert all(c.sha(c.R/n)==h for n,h in source.items())
            c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,
                     numerical_or_original2200_domain_qualified=False),maximum=4*1024**2)
            result.update(passed=True,bootstrap=bootstrap,source_frozen=True,negative_cases=len(cases),
                          secondary_save_cases=2,writer_charged_bytes=writer._read()['charged_bytes'],
                          original2200_stop_unexecuted=True,no_search_or_actual_authority=True)
    except BaseException as error:result.update(passed=False,first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start);c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
