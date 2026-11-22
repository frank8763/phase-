"""One new receipt-content/source-seam target. All inputs here are SOFTWARE.

No estimator update, original gear or origin qualification, numerical model,
live source acquisition, ROS, control application, replay or old suite runs.
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
from types import SimpleNamespace

C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1574_target_common',C/'common.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)


def main():
    start=time.monotonic()
    assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as stream:json.dump(dict(unix=time.time(),models=0),stream)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,
                replay_native=0,phase_FFI_loads=0,Allocator_recomputations=0,optimizer_calls=0,
                actual_capture_qualified=False,old_suite_runs=0,causal_tracker_updates=0)
    class NoNumerics(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'numpy','jax','jaxlib','mujoco','torch','rclpy','runtime','bindings','kernel','prediction','coupled_model','vehicle','factory'}:
                raise AssertionError('SOURCE_RECEIPTS_NO_NUMERICS:'+name)
    finder=NoNumerics();sys.meta_path.insert(0,finder)
    def profile(frame,event,arg):
        if event=='call':
            path=Path(frame.f_code.co_filename)
            if path.is_absolute()and path.is_relative_to(c.R):
                assert frame.f_code.co_name not in {'initial','step','select','simulate','compute','predict','advance','load_definitions','all_future','compare'}
                if frame.f_code.co_name=='__init__'and not path.is_relative_to(C):
                    assert path in {c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}
            assert time.monotonic()-start<120
    def audit(event,args):
        if event=='ctypes.dlopen'and args and args[0]:
            p=Path(args[0]);assert not p.is_absolute()or not p.resolve().is_relative_to(c.R)
    sys.addaudithook(audit);sys.setprofile(profile)
    try:
        resources=c.bootstrap();c.guard()
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json')
            assert parent['active_round']is None and parent['active_math_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==10
            source=c.read(c.BASE)['files'].copy()
            assert len(source)==11775 and all(c.sha(c.R/n)==h for n,h in source.items())
            recovery=c.read(c.R/'runs/v1571_complete_batch_comparison/CURRENT_SOURCE_REMOTE_RECOVERY.json')
            assert recovery['all_frozen_members_remote_chain_covered']and recovery['source_freeze_sha256']==c.sha(c.BASE)
            owner=c.load('v1574_real_source_owner',C/'canonical_owner.py')
            pump=c.load('v1574_real_source_pump',C/'pump.py')
            lifecycle=c.load('v1574_real_source_lifecycle',C/'lifecycle.py')
            context=c.load('v1574_real_source_route_context',C/'route_context.py')
            provider=c.load('v1574_real_provider_storage',C/'causal_provider.py')
            assert Path(owner.native_module.NativeStep.packet.__code__.co_filename).resolve()==c.R/'experiments/v1567_epoch_scope_target/native_step.py'
            assert 'model_peer'not in pump.Pump.__init__.__code__.co_varnames
            assert not hasattr(owner,'transaction_module')and not hasattr(owner,'reserve_module')
            wm=c.load('v1574_bounded_source_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
            boundary=c.load('v1574_bounded_source_output',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
            codec=c.load('v1574_existing_source_json',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
            target=c.O/'source_target';target.mkdir()
            writer=wm.WriterBudget(target,role='PLANNER',maximum_bytes=2*1024**2,source_identity=provider.io.digest(source))
            def save(path,value):
                path.parent.mkdir(parents=True,exist_ok=True)
                with boundary.OutputBoundary(target,writer.reserve):codec.write_atomic(path,codec.encoded(value),writer)
            fixed=c.read(c.O/'SOURCE_INPUT.json');request=fixed['request'];wire=request['actual']['wire'];snapshot=fixed['causal_snapshot']
            # This is a software storage adapter, not an original tracker. It
            # copies the previously saved snapshot and never updates a model or
            # periodic estimator. No positive actual-provider claim is made.
            class SoftwareTracker:
                def __init__(self):self.records=[];self.last_tick=-1
                def snapshot(self):return copy.deepcopy(snapshot)
                def update(self,**kwargs):self.last_tick=kwargs['native_tick'];return False
            adapter=object.__new__(provider.ObservedTracker)
            adapter._tracker=SoftwareTracker();adapter.run_id=wire['run_id'];adapter.output=target
            adapter.save=save;adapter.receipts=[];adapter.head=None;adapter.last_sequence=-1;adapter.poisoned=False
            assert adapter.observe(wire)is False
            source_record=adapter.event_source(request['actual'],request)
            native=SimpleNamespace(run_id=wire['run_id'],vehicle=SimpleNamespace(count=wire['native_tick']),sent={wire['sequence']:wire})
            proof=provider.verify(source_record,native,wire,request,prepared_sources=source,output=target)
            save(target/'SOFTWARE_CONTENT_ROUNDTRIP.json',dict(passed=True,scope='SOFTWARE_STORED_INPUT_NOT_LIVE_CAPTURE',proof=proof))
            negatives=[]
            def refused(name,fn):
                try:fn()
                except (AssertionError,KeyError,ValueError,RuntimeError)as error:
                    negatives.append(name);save(target/(name+'.json'),dict(passed=True,scope='SOFTWARE_SOURCE_API',refusal=repr(error)))
                else:raise AssertionError('SOURCE_NEGATIVE_NOT_REFUSED:'+name)
            for name,key,value in [('wrong_current_tick','covered_native',wire['native_tick']+1),
                ('changed_snapshot_SHA','snapshot_sha256','0'*64),('self_reported_complete_sensing','all_published_scans_observed',True),
                ('wrong_receipt_head','receipt_head_sha256','0'*64)]:
                bad=copy.deepcopy(source_record);bad[key]=value
                refused(name,lambda bad=bad:provider.verify(bad,native,wire,request,prepared_sources=source,output=target))
            bad=copy.deepcopy(source_record);bad['observation_receipts'][0]['file_sha256']='0'*64
            refused('changed_receipt_file',lambda:provider.verify(bad,native,wire,request,prepared_sources=source,output=target))
            bad_native=SimpleNamespace(run_id=wire['run_id'],vehicle=native.vehicle,sent={wire['sequence']:dict(wire,body=[0]*5)})
            refused('unbound_actual_wire',lambda:provider.verify(source_record,bad_native,wire,request,prepared_sources=source,output=target))
            refused('duplicate_observation',lambda:adapter.observe(wire))
            assert adapter.poisoned
            refused('poisoned_adapter_no_retry',lambda:adapter.observe(dict(wire,sequence=wire['sequence']+1)))
            # Real producer save failure: mutation is private; no receipt/head
            # is published and any subsequent attempt refuses.
            failing=object.__new__(provider.ObservedTracker);failing.__dict__.update(adapter.__dict__)
            failing._tracker=SoftwareTracker();failing.receipts=[];failing.head=None;failing.last_sequence=-1;failing.poisoned=False
            def denied(*args):raise RuntimeError('SOFTWARE_DURABLE_RECEIPT_DENIED')
            failing.save=denied
            refused('producer_save_failure',lambda:failing.observe(wire))
            assert failing.poisoned and failing.head is None and not failing.receipts
            refused('producer_save_no_retry',lambda:failing.observe(wire))
            # Capture first error and save error remain separately available.
            try:owner.capture_module.capture(object(),wire,run_id=wire['run_id'],prepared_sources=source,
                    causal_source=source_record,request=request,output=target,setup={},save_proof=denied)
            except owner.capture_module.CaptureRefusal as error:
                assert 'CANONICAL_CURRENT_CAPTURE_REFUSED'in str(error)and 'SOFTWARE_DURABLE_RECEIPT_DENIED'in error.secondary
                save(target/'FIRST_SECONDARY.json',dict(passed=True,first=str(error),secondary=error.secondary))
            else:raise AssertionError('CAPTURE_FIRST_SECONDARY_NOT_PRESERVED')
            refused('actual_lifecycle_not_admitted',lambda:lifecycle.run())
            refused('live_component_not_installed',lambda:owner.unavailable())
            save(target/'QUALIFICATION.json',dict(passed=True,source_only=True,software_scope=True,
                receipt_content_cases=len(negatives),strict2200_definition_bound=True,
                no_old_plain200_installer_or_modeled_peer=True,original_projection_source_reused_by_SHA=True,
                actual_capture_qualified=False,causal_tracker_updates=0,models=0,whole_route_passed=False))
            source[str((c.O/'SOURCE_INPUT.json').relative_to(c.R))]=c.sha(c.O/'SOURCE_INPUT.json')
            for p in C.iterdir():
                if p.is_file():
                    if p.suffix=='.py':ast.parse(p.read_text())
                    source[str(p.relative_to(c.R))]=c.sha(p)
            assert all(c.sha(c.R/n)==h for n,h in source.items())
            c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,
                source_only=True,models_authorized=False,actual_capture_qualified=False),maximum=4*1024**2)
            result.update(passed=True,source_members=len(source),source_frozen=True,
                negative_cases=len(negatives),writer_charged_bytes=writer._read()['charged_bytes'],resources=resources)
    except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder)
        result.update(closed=True,wall_s=time.monotonic()-start)
        c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
