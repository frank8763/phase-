"""New batch counter/raw-return error interface only; all arrays SOFTWARE."""
import ast
import copy
import fcntl
import importlib.abc
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import time
import traceback
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1569_source_common',C/'common.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)

def main():
    start=time.monotonic()
    assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0),f)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,
        phase_FFI_loads=0,Allocator_recomputations=0,optimizer_calls=0,replay_native=0,old_policy_calls=0)
    class NoModels(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'jax','jaxlib','mujoco','torch','rclpy','runtime','bindings','kernel','prediction','coupled_model','vehicle','factory','gear_handoff'}:
                raise AssertionError('CPP_BATCH_SOURCE_ONLY_NO_MODELS:'+name)
    finder=NoModels();sys.meta_path.insert(0,finder)
    def profile(frame,event,arg):
        if event=='call':
            path=Path(frame.f_code.co_filename)
            if path.is_absolute()and path.is_relative_to(c.R):
                assert frame.f_code.co_name not in {'initial','step','select','simulate','compute','predict','expand','advance','load_definitions','fill_complete_stop','_fill_complete_stop','original_module','run'}
                if frame.f_code.co_name=='__init__'and not path.is_relative_to(C):
                    assert path in {c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}
            assert time.monotonic()-start<120
    def hook(event,args):
        if event=='ctypes.dlopen'and args and args[0]:
            path=Path(args[0]);assert not path.is_absolute()or not path.resolve().is_relative_to(c.R)
    sys.addaudithook(hook);sys.setprofile(profile)
    try:
        bootstrap=c.bootstrap();c.guard()
        import numpy as np
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json')
            assert parent['active_round']is None and parent['active_math_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==10
            source=c.read(c.BASE)['files'].copy()
            assert len(source)==11744 and all(c.sha(c.R/n)==h for n,h in source.items())
            account=c.load('v1569_native_claim_api',C/'batch_account.py')
            raw=c.load('v1569_raw_return_save',C/'batch_failure.py')
            # Production imports stay inert; no old carrier/model is imported.
            batch=c.load('v1569_batch_definition',C/'batch_backend.py')
            capability=c.load('v1569_guard_definition',C/'capability.py')
            witness=c.load('v1569_complete_witness_definition',C/'witness.py')
            wm=c.load('v1569_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
            boundary=c.load('v1569_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
            codec=c.load('v1569_original_json',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
            target=c.O/'source_target';target.mkdir()
            writer=wm.WriterBudget(target,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.digest(source))
            with boundary.OutputBoundary(target,writer.reserve):
                def save(name,value):codec.write_atomic(target/name,codec.encoded(value),writer)
                negative=[]
                def refuse(name,fn):
                    try:fn()
                    except AssertionError as error:negative.append(name);return repr(error)
                    raise AssertionError('EXPECTED_BATCH_API_REFUSAL:'+name)
                work=account.WorkLedger();work.bucket('witness')
                refuse('wrong_batch_length',lambda:work.claim(2198,batch=True))
                work.claim(2199,batch=True)
                unknown=work.counts();assert unknown['native']==0 and unknown['inflight_unknown']and unknown['inflight_claimed_native']==2199
                refuse('second_claim_while_unknown',lambda:work.claim(2199,batch=True))
                refuse('wrong_ack_length',lambda:work.acknowledge(1))
                work.acknowledge(2199,batch=True)
                assert work.counts()['native']==work.counts()['batch_native']==2199
                refuse('duplicate_ack',lambda:work.acknowledge(2199,batch=True))
                work.bucket('nominal');refuse('batch_on_nominal',lambda:work.claim(2199,batch=True))
                work.bucket('witness');work.value['native']=1263600-2198
                refuse('full_cap_preclaim',lambda:work.claim(2199,batch=True))
                work.value['native']=0;work.value['witness_native']=1250000-2198
                refuse('category_cap_preclaim',lambda:work.claim(2199,batch=True))
                save('SOFTWARE_NATIVE_CLAIMS.json',dict(passed=True,SOFTWARE=True,models=0,unknown_at_failed_call=unknown,
                    negative_cases=negative,native_work_not_FFI_count=True))
                class Carrier:pass
                carrier=Carrier()
                arrays=(np.arange(2200*8,dtype=np.float64).reshape(2200,8),
                    np.zeros((2199,4),dtype=np.float64),np.zeros((2200,5),dtype=np.float64))
                def pending():return dict(returned=arrays,start_native=12345,claimed_native=2199,
                    engine_before=100,engine_after=2299,engine_in_call=False,acknowledged=True,
                    reconstructed_native=36,raw_return_available=True)
                carrier.batch_return=pending()
                a=dict(SOFTWARE=True,model_native=0,illustrative_claim=2199,illustrative_receipt_prefix=36)
                proof=raw.preserve(carrier,save_bytes=lambda n,b:codec.write_atomic(target/n,b,writer),save_proof=save,accounting=a)
                assert proof['arrays_durable']and proof['first_error']is None and not proof['secondary_errors']and not proof['complete_certificate']
                blob=(target/'BATCH_RETURN_RAW.npz').read_bytes()
                with np.load(io.BytesIO(blob),allow_pickle=False)as stored:
                    assert all(stored[k].dtype==v.dtype and stored[k].shape==v.shape and stored[k].tobytes()==v.tobytes()for k,v in zip(('states','ctrl','memory'),arrays))
                refuse('raw_save_not_retried',lambda:raw.preserve(carrier,save_bytes=lambda *a:None,save_proof=save,accounting=a))
                def denied(*args):raise OSError('SOFTWARE_RAW_SAVE_DENIED')
                carrier.batch_return=pending()
                failure=raw.preserve(carrier,save_bytes=denied,save_proof=denied,accounting=a)
                assert not failure['arrays_durable']and 'SOFTWARE_RAW_SAVE_DENIED'in failure['first_error']and len(failure['secondary_errors'])==1
                save('FIRST_AND_SECONDARY.json',dict(SOFTWARE=True,enclosing_first_error='SOFTWARE_RECEIPT_RECONSTRUCTION_FIRST',raw_save=failure,first_not_replaced=True))
                carrier.batch_return=dict(pending(),returned=None,acknowledged=False,raw_return_available=False,engine_after=117)
                unavailable=raw.preserve(carrier,save_bytes=denied,save_proof=lambda n,v:save('UNKNOWN_RETURN_PROOF.json',v),accounting=dict(SOFTWARE=True,inflight_unknown=True,native=0))
                assert not unavailable['arrays_durable']and unavailable['first_error']and unavailable['acknowledged']is False
                # The exact missing-admission productionGuard refuses before
                # method access/original_module/any old numerical imports.
                error=refuse('production_missing_admission',lambda:capability.Guard(lock=lock,method={},prepared_sources=source))
                assert 'FULL_CPP_BATCH_NOT_ADMITTED'in error
                save('PRODUCTION_MISSING_ADMISSION.json',dict(first_error=error,numerical_binding_executed=False,models=0))
                # Callshape/source ownership inspection, no simulated Gear or
                # numerical carrier fixture. Old suites are reused by SHA.
                tree=ast.parse((C/'batch_backend.py').read_text())
                ffi=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='simulate']
                assert len(ffi)==1 and ast.unparse(ffi[0].args[0])=='origin'
                assert ast.literal_eval(ffi[0].args[1].elts[0].elts[0])==0.
                assert 'child.fill_complete_stop(active)'in(C/'witness.py').read_text()
                assert "count['batch_native']==1235838"in(C/'witness.py').read_text()
                save('QUALIFICATION.json',dict(passed=True,source_only=True,models=0,SOFTWARE_arrays=True,
                    negative_cases=negative,raw_return_bytes=len(blob),numerical_batch_equivalence_qualified=False,
                    complete_numerical_witness_executed=False,old_fixture_or_model_suites_rerun=False,whole_route_passed=False))
            for p in C.iterdir():
                if p.is_file():
                    if p.suffix=='.py':ast.parse(p.read_text())
                    source[str(p.relative_to(c.R))]=c.sha(p)
            fixed=c.read(c.R/'runs/v1567_epoch_scope_target/FIXED_INPUTS.json')
            c.put(c.O/'FIXED_INPUTS.json',fixed)
            source[str((c.O/'FIXED_INPUTS.json').relative_to(c.R))]=c.sha(c.O/'FIXED_INPUTS.json')
            assert all(c.sha(c.R/n)==h for n,h in source.items())
            c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,
                source_only=True,models_authorized=False,numerical_batch_equivalence_qualified=False),maximum=4*1024**2)
            result.update(passed=True,source_frozen=True,source_members=len(source),negative_cases=len(negative),
                bootstrap=bootstrap,writer_charged_bytes=writer._read()['charged_bytes'])
    except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start)
        c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1

if __name__=='__main__':raise SystemExit(main())
