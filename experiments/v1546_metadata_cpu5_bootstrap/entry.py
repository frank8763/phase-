"""One source-bound budget computation under original guard; no models."""
import ast
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import time
import traceback
C=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v1545_metadata_common',C/'common.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def main():
    start=time.monotonic();assert sorted(os.sched_getaffinity(0))==[5]and os.environ.get('PHASE_REPO')==str(c.R)
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0),f)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,
                Allocator_recomputations=0,optimizer_calls=0,replay_native=0,phase_FFI_loads=0)
    class NoNumerics(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'numpy','jax','jaxlib','mujoco','torch','rclpy','ctypes','runtime','bindings','kernel','prediction','coupled_model','vehicle','factory'}:raise AssertionError('WITNESS_BUDGET_NO_NUMERICAL_IMPORT:'+name)
    finder=NoNumerics();sys.meta_path.insert(0,finder)
    def profile(frame,event,arg):
        if event=='call':
            path=Path(frame.f_code.co_filename)
            if path.is_absolute()and path.is_relative_to(c.R)and frame.f_code.co_name in {'__init__','step','compute','simulate','predict','expand'}:
                if not path.is_relative_to(C)and path not in {c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}:raise AssertionError('WITNESS_BUDGET_FORBIDDEN_MODEL_CALL')
            assert time.monotonic()-start<120
    sys.setprofile(profile)
    try:
        bootstrap=c.bootstrap();c.guard()
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']and parent['scientific_revisions']==9
            source=c.read(c.BASE)['files'].copy();assert all(c.sha(c.R/n)==h for n,h in source.items())
            failed=c.R/'runs/v1545_observer_witness_budget'
            failed_source=c.read(failed/'FAILED_SOURCE_FREEZE.json')['files']
            assert all(c.sha(c.R/name)==identity for name,identity in failed_source.items())
            assert(C/'witness_budget.py').read_bytes()==(c.R/'experiments/v1545_observer_witness_budget/witness_budget.py').read_bytes()
            assert(C/'source_owner.py').read_bytes()==(c.R/'experiments/v1545_observer_witness_budget/source_owner.py').read_bytes()
            m=c.load('v1545_real_witness_budget',C/'witness_budget.py')
            wm=c.load('v1545_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');io=c.load('v1545_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py');codec=c.load('v1545_original_codec',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
            task=c.O/'source_target';task.mkdir();writer=wm.WriterBudget(task,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.digest(source))
            with io.OutputBoundary(task,writer.reserve):
                def save(name,value):codec.write_atomic(task/name,codec.encoded(value),writer)
                budget=m.analyze(prepared_sources=source,save_proof=lambda v:save('ORIGINAL_WITNESS_BUDGET.json',v))
                assert budget['passed']and budget['original_catalogue_entries']==42 and not budget['model_permission']and not budget['original_search_budget_complete']
                rows=c.read(c.R/m.TEMPLATE)['rows']
                # Independent metadata calculation: direct original-row counts,
                # no model states, generated control arrays or old worker import.
                for case in budget['cases']:
                    remain=case['source_cut'];boundaries=0;native=0
                    for row in rows:
                        n=min(remain,row[2]);remain-=n;native+=n
                        if n:boundaries+=1 if row[3]or row[1]==0. else(n+7)//8
                        if remain==0:break
                    assert remain==0
                    native+=2200;boundaries+=1
                    if case['stage_native']:native+=case['stage_native']+2200;boundaries+=(case['stage_native']+7)//8+1
                    assert case['nominal_native']==native and case['old_full_stop_boundaries']==boundaries
                    assert case['full_no_pruning_core_cpp_native']==2*native+4400*boundaries
                    assert case['explicit_endpoint_certify_reproduction_upper_cpp_native']==3*native+8800*boundaries
                    assert case['explicit_endpoint_certify_reproduction_upper_engine_calls']==1+4*boundaries
                assert struct.calcsize('d')==struct.calcsize('q')==8
                assert m.uncompressed_arrays(0)==168 and m.uncompressed_arrays(1)==392 and m.uncompressed_arrays(2200)==492968
                negative=[]
                for name in [m.CATALOGUE,m.TEMPLATE,m.STOP_SOURCE,m.ENDPOINT]:
                    changed=source.copy();changed[name]='0'*64;saved=[]
                    def sink(proof):save('BAD_SOURCE_'+str(len(negative))+'.json',proof);saved.append(proof)
                    try:m.analyze(prepared_sources=changed,save_proof=sink)
                    except m.BudgetRefusal as error:assert saved and saved[0]['passed']is False and error.proof==saved[0];negative.append(name)
                    else:raise AssertionError('BUDGET_CHANGED_SOURCE_ACCEPTED')
                for cut in [0,-1,True,14701]:
                    try:m.prefix_metadata(rows,cut)
                    except AssertionError:negative.append('cut:'+repr(cut))
                    else:raise AssertionError('BUDGET_INVALID_CUT_ACCEPTED')
                changed=source.copy();changed[m.TEMPLATE]='0'*64
                def failed_save(proof):raise OSError('SOFTWARE_BUDGET_PROOF_WRITE_ERROR')
                try:m.analyze(prepared_sources=changed,save_proof=failed_save)
                except m.BudgetRefusal as error:
                    assert 'ORIGINAL_WITNESS_BUDGET_SOURCE_CHANGED'in str(error)and 'SOFTWARE_BUDGET_PROOF_WRITE_ERROR'in error.secondary
                    save('FIRST_SECONDARY.json',dict(first=str(error),secondary=error.secondary,proof=error.proof,models=0))
                else:raise AssertionError('BUDGET_FIRST_SECONDARY_LOST')
                summary=dict(passed=True,models=0,original_catalogue_cases=42,
                    exact_core_metadata_independently_checked=True,source_and_cut_negative_cases=negative,
                    first_secondary_saved=True,explicit_CPP_upper_native=budget['explicit_CPP_callsite_upper_native'],
                    explicit_CPP_simulate_upper=budget['explicit_CPP_simulate_callsite_upper'],
                    explicit_CPP_Engine_constructor_upper=budget['explicit_CPP_Engine_constructor_upper'],
                    nominal_range=[min(v['nominal_native']for v in budget['cases']),max(v['nominal_native']for v in budget['cases'])],
                    per_candidate_boundary_range=[min(v['old_full_stop_boundaries']for v in budget['cases']),max(v['old_full_stop_boundaries']for v in budget['cases'])],
                    core_raw_payload_range=[min(v['complete8array_raw_payload_bytes']for v in budget['cases']),max(v['complete8array_raw_payload_bytes']for v in budget['cases'])],
                    no_original_worker_import_model_or_control_execution=True,raw_bytes_not_actual_disk_bound=True,
                    opaque_geometry_import_math_initialization_and_independent_audit_unknown=True,
                    original_search_complete_budget_or_model_admission=False)
                save('QUALIFICATION.json',summary)
            for p in C.iterdir():
                if p.is_file():source[str(p.relative_to(c.R))]=c.sha(p)
            for p in [failed/'FAILED_SOURCE_FREEZE.json',failed/'ENTRY_QUALIFICATION.json']:
                source[str(p.relative_to(c.R))]=c.sha(p)
            assert all(c.sha(c.R/n)==h for n,h in source.items())
            c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,no_numerical_or_physical_admission=True),maximum=4*1024**2)
            result.update(passed=True,bootstrap=bootstrap,source_frozen=True,negative_cases=len(negative),
                writer_charged_bytes=writer._read()['charged_bytes'],budget_summary=summary)
    except BaseException as error:result.update(passed=False,first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start);c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
