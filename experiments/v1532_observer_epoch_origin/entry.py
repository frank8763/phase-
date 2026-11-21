"""Once new source/origin/API target; no model constructors, steps or FFI."""
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
s=importlib.util.spec_from_file_location('v1532_entry_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def main():
    assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
    start=time.monotonic();wall=time.time();assert wall+120<1795395600
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as stream:json.dump(dict(unix=wall,models=0),stream)
    result=dict(passed=False,closed=False,scope='CURRENT_ORIGIN_SOURCE_API_ONLY',models=0,analytical_native=0,
                physical_native=0,Allocator_recomputations=0,phase_FFI_library_loads=0,optimizer_calls=0,replay_native=0)
    class NoModels(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'jax','jaxlib','mujoco','torch','rclpy','vehicle','factory'}:raise AssertionError('NEW_ORIGIN_SOURCE_ONLY:'+name)
    finder=NoModels();sys.meta_path.insert(0,finder)
    def profile(frame,event,arg):
        if event=='call':
            path=Path(frame.f_code.co_filename)
            if path.is_absolute()and path.is_relative_to(c.R)and frame.f_code.co_name in {'__init__','step','compute','simulate','expand','predict'}:
                if not path.is_relative_to(C)and path not in {c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}:
                    raise AssertionError('ORIGIN_SOURCE_TARGET_NO_MODEL_CONSTRUCTOR_OR_STEP')
            assert time.monotonic()-start<120,'ORIGIN_SOURCE_TARGET_LIMIT'
    sys.setprofile(profile)
    try:
        bootstrap=c.bootstrap();c.guard()
        def audit_hook(event,args):
            if event=='ctypes.dlopen'and args and isinstance(args[0],str)and str(c.R)in args[0]:raise AssertionError('ORIGIN_SOURCE_TARGET_PHASE_FFI_FORBIDDEN')
            if event=='subprocess.Popen':raise AssertionError('ORIGIN_SOURCE_TARGET_CHILD_FORBIDDEN')
        sys.addaudithook(audit_hook)
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json')
            assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']and parent['scientific_revisions']==8
            base=c.read(c.BASE)['files'].copy();assert all(c.sha(c.R/n)==h for n,h in base.items())
            prior=c.R/'runs/v1530_explicit_we_private_binding';assert c.read(prior/'ENTRY_QUALIFICATION.json')['passed']and c.read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
            paths=dict(source_envelope='runs/v1528_fixed_we_evaluation_contract/source_content_target/SOURCE_ENVELOPE.json',content_proof='runs/v1528_fixed_we_evaluation_contract/source_content_target/saved_original_content_only.json',remote_index='runs/v1529_fixed_we_source_recovery/ARCHIVE_INDEX.json',remote_proof='runs/v1529_fixed_we_source_recovery/FULL_REMOTE_VERIFIED.json')
            source=base.copy()
            for path in [*[c.R/n for n in paths.values()],c.O/'SCIENTIFIC_REVISION_REGISTRATION.json',prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json',prior/'ENTRY_QUALIFICATION.json']:
                source[str(path.relative_to(c.R))]=c.sha(path)
            for path in C.iterdir():
                if path.is_file():source[str(path.relative_to(c.R))]=c.sha(path)
            original=c.load('v1532_new_method_source_contract',C/'source_contract.py');rec=c.load('v1532_new_source_records',C/'records.py')
            budget=c.load('v1532_source_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');boundary=c.load('v1532_source_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
            task=c.O/'source_target';task.mkdir();writer=budget.WriterBudget(task,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.digest(source));cases=[]
            with boundary.OutputBoundary(task,writer.reserve):
                method=original.prepare_saved_source(**paths,prepared_sources=source,save_proof=lambda value:rec.save_json(task,'SOURCE_METHOD_BINDING.json',value,writer))
                rec.save_json(task,'METHOD_INPUT.json',method,writer)
                bad=dict(source);bad[str((c.O/'SCIENTIFIC_REVISION_REGISTRATION.json').relative_to(c.R))]='0'*64
                saved=[]
                try:original.prepare_saved_source(**paths,prepared_sources=bad,save_proof=lambda value:(rec.save_json(task,'CHANGED_REGISTRATION.json',value,writer),saved.append(value)))
                except original.OriginSourceRefusal as error:assert saved and not saved[0]['passed']and error.secondary_save_error is None
                else:raise AssertionError('CHANGED_METHOD_REGISTRATION_ACCEPTED')
                # Production CLI refuses missing numerical admission before it
                # can bind definitions, call initial() or construct any model.
            fcntl.flock(lock,fcntl.LOCK_UN)
            try:
                driver=c.load('v1532_real_unadmitted_driver',C/'driver.py');refusal=driver.execute()
            finally:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            assert refusal['closed']and not refusal['passed']and 'CURRENT_ORIGIN_STOP_COMPONENT_NOT_ADMITTED'in refusal['first_error']
            assert not refusal['generation_executed']and not refusal['audit_executed']and refusal['generation_analytical_native']==refusal['audit_analytical_native']==0
            definition=c.load('v1532_frozen_definition_dependency',c.R/'experiments/v1530_explicit_we_private_binding/definitions.py')
            read_authority=dict(scope='ORIGINAL_WE_DEFINITIONS_ONLY',models_authorized=False,method_origin_authorized=False,
                                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),absolute_deadline_unix=wall+120,hard_stop_monotonic=start+120)
            defs,_=definition.load_definitions(source,authority=read_authority,lock=lock)
            # These unchanged definitions are a production dependency. No old
            # import qualification or namespace-negative suite is replayed.
            origin=c.load('v1532_new_origin_interface',C/'origin.py');ctx=dict(read_authority,scope='SOURCE_ORIGIN_ONLY',current_input_sha256=method['method_input_sha256'])
            with boundary.OutputBoundary(task,writer.reserve):
                def run(label,value,context,expected):
                    seen=[]
                    def save(proof):rec.save_json(task,label+'.json',proof,writer);seen.append(proof)
                    first=None
                    try:answer=origin.prepare(value,runtime=defs['runtime'],scope='SOURCE_ORIGIN_ONLY',authority=context,lock=lock,save_proof=save)
                    except origin.OriginRefusal as error:first=str(error);answer=None;assert error.secondary is None
                    assert len(seen)==1 and seen[0]['passed']is expected and(first is None)is expected
                    cases.append(dict(name=label,passed=expected,first_error=first,saved_before_refusal=True))
                    return answer,seen[0]
                value,proof=run('EXACT_CURRENT_ORIGIN',method,ctx,True)
                assert proof['initial_state_bytes']['shape']==[8]and proof['initial_last_ctrl_bytes']['shape']==[4]
                assert 'steering_load_episode'not in method['physical_source']['packet']and value['steering_load_episode']is False
                changed=copy.deepcopy(method);changed['method_memory']['steering_load_episode']=True;run('CHANGED_LOAD_EPOCH',changed,ctx,False)
                changed=copy.deepcopy(method);del changed['method_memory']['epoch_native'];run('MISSING_EPOCH',changed,ctx,False)
                changed=copy.deepcopy(ctx);changed['boot_id']='foreign';run('WRONG_BOOT',method,changed,False)
                changed=copy.deepcopy(ctx);changed['absolute_deadline_unix']=wall-1;run('EXPIRED_WALL',method,changed,False)
                changed=copy.deepcopy(ctx);changed['hard_stop_monotonic']=start-1;run('EXPIRED_MONOTONIC',method,changed,False)
                changed=copy.deepcopy(ctx);changed['current_input_sha256']='0'*64;run('CHANGED_INPUT_ID',method,changed,False)
                def fail_save(proof):raise OSError('V1532_SOURCE_SECONDARY_SAVE')
                try:origin.prepare({},runtime=defs['runtime'],scope='SOURCE_ORIGIN_ONLY',authority=ctx,lock=lock,save_proof=fail_save)
                except origin.OriginRefusal as error:
                    assert 'CURRENT_ORIGIN_CONVERSION_REFUSED'in str(error)and'V1532_SOURCE_SECONDARY_SAVE'in error.secondary
                    rec.save_json(task,'SECONDARY_SAVE_ERROR.json',dict(first_error=str(error),secondary=error.secondary,proof=error.proof,software_injection=True),writer)
                else:raise AssertionError('ORIGIN_SECONDARY_FAILURE_ACCEPTED')
                generator=c.load('v1532_new_partial_buffer_seam',C/'generate.py')
                import numpy as np
                # One acknowledged software row plus unacknowledged NaN tail:
                # test the new reader boundary, never simulate a model.
                local=dict(state=np.arange(8,dtype=float),ss=np.full((2,8),np.nan),uu=np.full((2,4),np.nan),mem=np.full((2,5),np.nan))
                local['ss'][0]=np.arange(8)+1.;local['uu'][0]=np.arange(4);local['mem'][0]=np.arange(5)
                partial=generator.partial_arrays(local,1,dict(last_ctrl=np.zeros(4),integral=0.))
                assert partial['states'].shape==(2,8)and partial['ctrl'].shape==(1,4)and partial['memory'].shape==(2,5)
                assert all(np.isfinite(v).all()for v in partial.values())
                rec.save_arrays(task,'ACKNOWLEDGED_SOFTWARE_PREFIX.npz',partial,writer)
                try:generator.partial_arrays(local,3,dict(last_ctrl=np.zeros(4),integral=0.))
                except AssertionError:pass
                else:raise AssertionError('PARTIAL_PREFIX_BEYOND_BUFFER_ACCEPTED')
                contract=c.load('v1532_new_dependency_gate',C/'contract.py')
                assert not contract.audit_allowed(dict(passed=False,closed=True,analytical_native=200,analytical_inflight_unknown=False),dict(complete=True,native=200))
                try:contract.runtime_guard(method,ctx,lock,phase='CPP_GENERATION',completed=0)
                except (FileNotFoundError,AssertionError):pass
                else:raise AssertionError('UNADMITTED_MODEL_API_ACCEPTED')
                # Both production error closures execute before any constructor.
                gen,receipt=generator.generate(method,c.read(c.SETUP),value,defs,authority=ctx,folder=task,writer=writer,lock=lock)
                assert not gen['passed']and gen['closed']and gen['analytical_native']==0 and not gen['analytical_inflight_unknown']and gen['cpp_engine_constructions']==0 and receipt is None
                auditor=c.load('v1532_new_audit_dependency_closure',C/'audit.py');aud=auditor.audit(method,c.read(c.SETUP),defs,generation=gen,receipt=receipt,authority=ctx,folder=task,writer=writer,lock=lock)
                assert not aud['passed']and aud['closed']and aud['analytical_native']==0 and aud['python_predictor_constructions']==0
            fixed=dict(method_input_file_sha256=c.sha(c.INPUT),method_input_sha256=method['method_input_sha256'],setup_sha256=c.sha(c.SETUP))
            c.put(c.O/'FIXED_INPUTS.json',fixed)
            source[str(c.INPUT.relative_to(c.R))]=c.sha(c.INPUT);source[str((c.O/'FIXED_INPUTS.json').relative_to(c.R))]=c.sha(c.O/'FIXED_INPUTS.json')
            assert all(c.sha(c.R/name)==identity for name,identity in source.items())
            c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,source_origin_interface_only=True,numerical_CPP_Python_branch_qualified=False),maximum=4*1024**2)
            c.put(c.O/'ORIGIN_API_QUALIFICATION.json',dict(passed=True,closed=True,cases=cases,changed_registration_rejected=True,
                  original_saved_origin_converted_without_model_constructor=True,source_packet_not_modified=True,raw_initial8state_and4control_bytes_saved=True,
                  acknowledged_software_prefix_no_model=True,production_unadmitted_driver_and_generation_audit_closures=True,
                  old_definition_and_byte_qualifications_reused_by_source_not_rerun=True,writer=writer._read(),models=0,phase_FFI_loads=0))
            result.update(passed=True,source_frozen=True,method_input_sha256=method['method_input_sha256'],new_origin_negative_cases=len(cases)-1,
                          complete_model_branch_or_actual_policy_qualified=False,bootstrap=bootstrap)
    except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start)
        c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
