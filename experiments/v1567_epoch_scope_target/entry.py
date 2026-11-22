"""New current2200 source/epoch API only; no model construction or policy run."""
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
s=importlib.util.spec_from_file_location('v1566_source_common',C/'common.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)

def main():
    start=time.monotonic()
    assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0),f)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,
        phase_FFI_loads=0,Allocator_recomputations=0,optimizer_calls=0,replay_native=0,old_policy_calls=0)
    class NoNumerics(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'numpy','jax','jaxlib','mujoco','torch','rclpy','runtime','bindings','kernel','prediction','coupled_model','vehicle','factory','gear_handoff'}:
                raise AssertionError('CURRENT2200_SOURCE_API_NO_NUMERICS:'+name)
    finder=NoNumerics();sys.meta_path.insert(0,finder)
    def profile(frame,event,arg):
        if event=='call':
            path=Path(frame.f_code.co_filename)
            if path.is_absolute()and path.is_relative_to(c.R):
                assert frame.f_code.co_name not in {'initial','step','select','simulate','compute','predict','expand','advance','load_definitions'}
                if frame.f_code.co_name=='__init__'and not path.is_relative_to(C):
                    assert path in {c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}
            assert time.monotonic()-start<120
    def hook(event,args):
        if event=='ctypes.dlopen'and args and args[0]:
            path=Path(args[0]);assert not path.is_absolute()or not path.resolve().is_relative_to(c.R)
    sys.addaudithook(hook);sys.setprofile(profile)
    try:
        bootstrap=c.bootstrap();c.guard()
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json')
            assert parent['active_round']is None and parent['active_math_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==10
            source=c.read(c.BASE)['files'].copy()
            assert all(c.sha(c.R/n)==h for n,h in source.items())
            fixed=c.read(c.R/'runs/v1563_lzma_lossless_witness/FIXED_INPUTS.json')
            method=c.read(c.R/'runs/v1550_canonical_observer_policy/source_target/RESPONSE_METHOD.json')
            assert method['response_method_sha256']==fixed['response_method_sha256']
            packet=copy.deepcopy(method['base_method']['physical_source']['packet'])
            gear=copy.deepcopy(method['base_method']['physical_source']['gear_memory'])
            guard=c.load('v1566_current_source_guard',C/'reserve_guard.py')
            memory_module=c.load('v1566_method_epoch_store',C/'method_memory.py')
            reserve=c.load('v1566_current_reserve_definition',C/'current_reserve.py')
            wm=c.load('v1566_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
            io=c.load('v1566_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
            codec=c.load('v1566_original_json_codec',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
            target=c.O/'source_target';target.mkdir()
            writer=wm.WriterBudget(target,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.digest(source))
            with io.OutputBoundary(target,writer.reserve):
                def save(name,value):codec.write_atomic(target/name,codec.encoded(value),writer)
                prefix=c.R/'runs/v1566_canonical_live_schedule/source_target'
                prior_freeze=c.read(c.R/'runs/v1566_canonical_live_schedule/FAILED_SOURCE_FREEZE.json')['files']
                for name in ['method_memory.py','reserve_guard.py','current_reserve.py','policy.py','reference.py','native_step.py','execution.py']:
                    original=c.R/'experiments/v1566_canonical_live_schedule'/name
                    assert c.sha(original)==prior_freeze[str(original.relative_to(c.R))]
                    assert(C/name).read_bytes()==original.read_bytes()
                prefix_names=['SAVED_SOURCE_PROOF.json','FRESH_ROLE.json','WRONG_NATIVE.json','WRONG_CLOCK.json','WRONG_ENCODER_TIME.json','UNKNOWN_EPOCH.json','RESET_AT_ORIGIN.json','METHOD_COVERAGE_GAP.json','GEAR_CLOCK_GAP.json','CURRENT_SOURCE_NAN.json','MALFORMED_PACKET.json','FIRST_AND_SECONDARY.json']
                prefix_sha={}
                for name in prefix_names:
                    p=prefix/name;value=c.read(p);prefix_sha[str(p.relative_to(c.R))]=c.sha(p)
                    if name=='SAVED_SOURCE_PROOF.json':assert value['passed']and not value['models_authorized']and not value['physical_permission']
                    elif name=='FIRST_AND_SECONDARY.json':assert 'registered_source_role'in value['first_error']and 'SOFTWARE_EPOCH_PROOF_SAVE_DENIED'in value['secondary']
                    else:assert value['passed']is False and value['first_error']
                prior=c.read(prefix/'SAVED_SOURCE_PROOF.json');current=prior['current_method_memory']
                assert prior['complete_source']==packet and prior['current_gear_memory']==gear
                assert prior['response_method_sha256']==method['response_method_sha256']
                source.update(prefix_sha)
                for name in ['FAILED_SOURCE_FREEZE.json','ENTRY_QUALIFICATION.json','ENTRY_OUTER_CLOSED.json','CLOSED_REVIEW.json']:
                    p=c.R/'runs/v1566_canonical_live_schedule'/name;source[str(p.relative_to(c.R))]=c.sha(p)
                negative=[]
                def denied(value):raise OSError('SOFTWARE_EPOCH_PROOF_SAVE_DENIED')
                save('PREFIX_SOURCE_CASE_REUSE.json',dict(passed=True,source_only=True,models=0,original_entry_failed=True,
                    saved_positive_and10negative_andfirstsecondary_reused=True,prefix_sha256=prefix_sha,
                    old_prefix_cases_not_rerun=True,original_method_and_guard_sources_identical=True))
                # Three explicit SOFTWARE applied receipts test only new
                # durable method-state ownership, not the original schedule.
                original_current=copy.deepcopy(current);origin=current['covered_native']
                software_store=memory_module.MethodMemory(method,save_receipt=lambda value:save('SOFTWARE_EPOCH_'+str(value.get('after_native','anchor'))+'.json',value))
                entries=[];chain='0'*64;prior=False
                for index,(speed,parked_target)in enumerate([(.08,None),(0.,None),(-.03,None)]):
                    row=dict(before_native=origin+index,after_native=origin+index+1,epoch_native=origin,
                        load_before=prior,load_after=memory_module.next_load(prior,speed,parked_target),applied_body=[speed,0.],
                        parked_target=parked_target,actual_sensor_claim=False,response_method_sha256=method['response_method_sha256'],
                        decision_sha256='1'*64,source_packet_sha256='2'*64,source_full_state_sha256='3'*64,
                        after_full_state_sha256='4'*64,previous_chain_sha256=chain,software_input_not_actual=True)
                    row['chain_sha256']=c.digest(row)
                    software_store.applied(row);entries.append(row);prior=row['load_after'];chain=row['chain_sha256']
                assert software_store.current()['covered_native']==origin+3 and software_store.current()['steering_load_episode']is False
                save('SOFTWARE_METHOD_CHAIN.json',dict(rows=entries,current=software_store.current(),models=0,actual_actions=0))
                failed_store=memory_module.MethodMemory(method,save_receipt=lambda value:None)
                failed_store.save_receipt=denied
                try:failed_store.applied(entries[0])
                except OSError:
                    assert failed_store.covered==origin and failed_store.load is False and failed_store.failed
                else:raise AssertionError('FAILED_METHOD_SAVE_ADVANCED_STATE')
                try:failed_store.current()
                except AssertionError:pass
                else:raise AssertionError('FAILED_METHOD_STORE_PUBLISHED_STATE')
                save('METHOD_FAILED_SAVE.json',dict(failed=True,covered_native=failed_store.covered,
                    no_published_advance=True,actual_actions=0,models=0))
                assert current==original_current

                try:guard.Guard(method=method,lock=lock,prepared_sources=source,save_origin=denied,save_proof=denied,save_secondary=denied)
                except AssertionError as error:
                    assert str(error)=='CURRENT2200_RESERVE_NOT_ADMITTED'
                    save('PRODUCTION_MISSING_ADMISSION.json',dict(first_error=str(error),models=0,numerical_binding_executed=False))
                else:raise AssertionError('CURRENT_RESERVE_UNADMITTED_CONSTRUCTION')
                class RefusingGuard:
                    def require_current_reserve_components(self,*args,**kwargs):raise AssertionError('SOFTWARE_CURRENT_GUARD_REFUSAL')
                try:reserve.CurrentReserve(method=method,setup={},defs={},guard=RefusingGuard(),current_method_memory=lambda:current,current_gear=lambda:gear,save_complete=denied,save_partial=denied)
                except AssertionError as error:assert str(error)=='SOFTWARE_CURRENT_GUARD_REFUSAL'
                else:raise AssertionError('CURRENT_RESERVE_BOUND_NUMERICS_WITHOUT_GUARD')
                save('QUALIFICATION.json',dict(passed=True,source_only=True,models=0,new_integrations=0,
                    actual_actions=0,negative_cases=negative,software_method_transitions=3,
                    real_current_capture_qualified=False,model_origin_or_response_qualified=False,
                    whole_route_passed=False,original_numerical_or_fixture_suites_rerun=False))
            # Immutable old scientific code and numerical/OS/byte proofs are
            # reused by SHA; only the new source guard/API was executed.
            for p in C.iterdir():
                if p.is_file():
                    if p.suffix=='.py':ast.parse(p.read_text())
                    source[str(p.relative_to(c.R))]=c.sha(p)
            c.put(c.O/'FIXED_INPUTS.json',fixed)
            source[str((c.O/'FIXED_INPUTS.json').relative_to(c.R))]=c.sha(c.O/'FIXED_INPUTS.json')
            assert all(c.sha(c.R/n)==h for n,h in source.items())
            c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,
                source_only=True,models_authorized=False,actual_capture_qualified=False,complete_current2200_reserve_qualified=False),maximum=4*1024**2)
            result.update(passed=True,source_frozen=True,source_members=len(source),negative_cases=len(negative),
                software_method_transitions=3,prefix_cases_reused=12,bootstrap=bootstrap,writer_charged_bytes=writer._read()['charged_bytes'])
    except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start)
        c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1

if __name__=='__main__':raise SystemExit(main())
