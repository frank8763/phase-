"""One saved-input/source conditional gear obligation target, no policy run."""
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
spec=importlib.util.spec_from_file_location('v1549_source_common',C/'common.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def main():
    start=time.monotonic();assert sorted(os.sched_getaffinity(0))==[5]and os.environ.get('PHASE_REPO')==str(c.R)
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0),f)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,Allocator_recomputations=0,
                optimizer_calls=0,replay_native=0,phase_FFI_loads=0,original_policy_calls=0)
    class NoNumerics(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'numpy','jax','jaxlib','mujoco','torch','rclpy','ctypes','runtime','bindings','kernel','prediction','coupled_model','vehicle','factory','gear_handoff'}:raise AssertionError('GEAR_OBLIGATION_SOURCE_ONLY_NO_POLICY:'+name)
    finder=NoNumerics();sys.meta_path.insert(0,finder)
    def profile(frame,event,arg):
        if event=='call':
            p=Path(frame.f_code.co_filename)
            if p.is_absolute()and p.is_relative_to(c.R)and frame.f_code.co_name in {'__init__','select','step','compute','simulate','predict','expand'}:
                if not p.is_relative_to(C)and p not in {c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}:raise AssertionError('GEAR_OBLIGATION_FORBIDDEN_POLICY_OR_MODEL_CALL')
            assert time.monotonic()-start<120
    sys.setprofile(profile)
    try:
        bootstrap=c.bootstrap();c.guard()
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            p=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json');assert p['active_round']is None and p.get('active_math_round')is None and not p['models_now_authorized']and p['scientific_revisions']==9
            source=c.read(c.BASE)['files'].copy();assert all(c.sha(c.R/n)==h for n,h in source.items())
            m=c.load('v1549_real_source_obligation',C/'obligation.py');wm=c.load('v1549_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');io=c.load('v1549_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py');codec=c.load('v1549_original_codec',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
            task=c.O/'source_target';task.mkdir();writer=wm.WriterBudget(task,role='PLANNER',maximum_bytes=1024**2,source_identity=c.digest(source))
            with io.OutputBoundary(task,writer.reserve):
                def save(name,value):codec.write_atomic(task/name,codec.encoded(value),writer)
                proof=m.prove(prepared_sources=source,save_proof=lambda v:save('CONDITIONAL_GEAR_OBLIGATION.json',v))
                assert proof['passed']and proof['source_conditional_only']and not proof['model_permission']and not proof['physical_permission']and not proof['actual_response_tested']
                assert proof['known_conditional_base_catalogue_indices']==[0,1]and proof['other40cases_unknown_without_response_history']
                assert proof['saved_gear']['gear']==1 and proof['saved_gear']['brake_start']is None and proof['canonical_brake_native']==200
                assert proof['first_original_template_signed_request']==dict(offset_native=956,requested_speed=-.03,parked=False)
                assert proof['raw_versus_filtered_controls_identical']is False and proof['actual_transition_release_and_rest_unknown']
                negative=[]
                for i,name in enumerate([m.GEAR,m.ROWS,m.METHOD,m.CATALOGUE]):
                    changed=source.copy();changed[name]='0'*64;saved=[]
                    def sink(v):save('SOURCE_REFUSAL_'+str(i)+'.json',v);saved.append(v)
                    try:m.prove(prepared_sources=changed,save_proof=sink)
                    except m.ObligationRefusal as error:assert saved and not saved[0]['passed']and saved[0]==error.proof;negative.append(name)
                    else:raise AssertionError('GEAR_OBLIGATION_CHANGED_SOURCE_ACCEPTED')
                changed=source.copy();del changed[m.METHOD];saved=[]
                def missing(v):save('MISSING_METHOD_SOURCE.json',v);saved.append(v)
                try:m.prove(prepared_sources=changed,save_proof=missing)
                except m.ObligationRefusal as error:assert saved and not saved[0]['passed']and 'KeyError'in str(error);negative.append('missing_method_identity')
                else:raise AssertionError('GEAR_OBLIGATION_MISSING_SOURCE_ACCEPTED')
                changed=source.copy();changed[m.GEAR]='0'*64
                def failed(v):raise OSError('SOFTWARE_GEAR_OBLIGATION_SAVE_ERROR')
                try:m.prove(prepared_sources=changed,save_proof=failed)
                except m.ObligationRefusal as error:
                    assert 'CATALOGUE_GEAR_SOURCE_CHANGED'in str(error)and 'SOFTWARE_GEAR_OBLIGATION_SAVE_ERROR'in error.secondary
                    save('FIRST_AND_SECONDARY.json',dict(first_error=str(error),secondary=error.secondary,proof=error.proof,models=0))
                else:raise AssertionError('GEAR_OBLIGATION_FIRST_SAVE_ERROR_LOST')
                save('QUALIFICATION.json',dict(passed=True,models=0,original_policy_calls=0,source_negatives=negative,first_secondary_saved=True,
                    no_future_feedback_or_actual_gear_recomputation=True,conditional_indices=[0,1],other40unknown=True,
                    no_model_or_actual_admission=True,original_request_catalogue_not_modified=True))
            for path in C.iterdir():
                if path.is_file():source[str(path.relative_to(c.R))]=c.sha(path)
            assert all(c.sha(c.R/n)==h for n,h in source.items())
            c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,no_policy_model_or_physical_authority=True),maximum=4*1024**2)
            result.update(passed=True,bootstrap=bootstrap,source_frozen=True,negative_cases=len(negative),writer_charged_bytes=writer._read()['charged_bytes'],conditional_only=True,nonzero_method_permission=False)
    except BaseException as error:result.update(passed=False,first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start);c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
