"""New complete-comparison owner/CLI source target; no numerical imports."""
import ast
import copy
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
C=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v1571_source_common',C/'common.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


def main():
    start=time.monotonic()
    assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0),f)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,
        phase_FFI_loads=0,Allocator_recomputations=0,optimizer_calls=0,replay_native=0,old_policy_calls=0)
    class NoModels(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'numpy','jax','jaxlib','mujoco','torch','rclpy','runtime','bindings','kernel','prediction','coupled_model','vehicle','factory','gear_handoff'}:
                raise AssertionError('FULL_CPP_OWNER_SOURCE_ONLY_NO_NUMERICS:'+name)
    finder=NoModels();sys.meta_path.insert(0,finder)
    def profile(frame,event,arg):
        if event=='call':
            path=Path(frame.f_code.co_filename)
            if path.is_absolute()and path.is_relative_to(c.R):
                assert frame.f_code.co_name not in {'initial','step','select','simulate','compute','predict','expand','advance','load_definitions','fill_complete_stop','_fill_complete_stop','original_module','run','launch'}
                if frame.f_code.co_name=='__init__'and not path.is_relative_to(C):
                    assert path in {c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}
            assert time.monotonic()-start<120
    def hook(event,args):
        if event=='ctypes.dlopen'and args and args[0]:
            path=Path(args[0]);assert not path.is_absolute()or not path.resolve().is_relative_to(c.R)
    sys.addaudithook(hook);sys.setprofile(profile)
    child=None;child_identity=None
    try:
        bootstrap=c.bootstrap();c.guard()
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json')
            assert parent['active_round']is None and parent['active_math_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==10
            source=c.read(c.BASE)['files'].copy()
            assert len(source)==11755 and all(c.sha(c.R/n)==h for n,h in source.items())
            inherited=c.read(c.R/'runs/v1569_zero_tail_batch_backend/CURRENT_SOURCE_REMOTE_RECOVERY.json')
            assert inherited['all_frozen_members_remote_chain_covered']and inherited['source_freeze_sha256']==c.sha(c.BASE)
            for name in ['batch_account.py','batch_backend.py','batch_failure.py','capability.py','witness.py']:
                assert(C/name).read_bytes()==(c.R/'experiments/v1569_zero_tail_batch_backend'/name).read_bytes()
            owner=c.load('v1571_new_once_owner',C/'owner.py')
            driver=c.load('v1571_real_driver',C/'driver.py')
            wm=c.load('v1571_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
            io=c.load('v1571_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
            codec=c.load('v1571_original_json',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
            target=c.O/'source_target';target.mkdir()
            writer=wm.WriterBudget(target,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.digest(source))
            def save(name,value):
                with io.OutputBoundary(target,writer.reserve):codec.write_atomic(target/name,codec.encoded(value),writer)
            # These machine-shaped values are SOFTWARE predicate input only.
            machine=dict(passed=True,closed=True,first_error=None,secondary_errors=[],CPP_inflight_unknown=False,
                construction_inflight=None,CPP_analytical_native=1263600,Engine_constructions=1,
                saved_reference_is_development_input=True,python_generation_native=0,physical_native=0,
                replay_native=0,optimizer_calls=0,physical_capture_native=0,
                accounting=dict(stages={'CPP_AUDIT':dict(native=1263600,nominal_native=13600,
                    witness_native=1250000,copy=562,batch_calls=562,batch_native=1235838)}))
            assert owner.runtime_passed(0,machine,[])and not owner.work_unknown(machine)
            cases=[]
            for name,key,value in [('partial_work','CPP_analytical_native',1263599),('constructor_bool','Engine_constructions',True),
                ('unknown_work','CPP_inflight_unknown',True),('construction_pending','construction_inflight','Engine'),
                ('first_error','first_error','SOFTWARE_FIRST'),('new_generation','python_generation_native',1),('physical_forbidden','physical_native',1)]:
                bad=copy.deepcopy(machine);bad[key]=value
                assert not owner.runtime_passed(0,bad,[]),name;cases.append(name)
            bad=copy.deepcopy(machine);del bad['construction_inflight']
            assert owner.work_unknown(bad)and not owner.runtime_passed(0,bad,[]);cases.append('missing_construction_unknown')
            bad=copy.deepcopy(machine);del bad['first_error']
            assert not owner.runtime_passed(0,bad,[]);cases.append('missing_first_error')
            bad=copy.deepcopy(machine);bad['accounting']['stages']['CPP_AUDIT']['batch_native']-=1
            assert not owner.runtime_passed(0,bad,[]);cases.append('batch_denominator_changed')
            assert not owner.runtime_passed(1,machine,[])and not owner.runtime_passed(0,machine,['SOFTWARE_SECONDARY'])
            cases.extend(['child_nonzero','secondary_close_failure'])
            assert owner.work_unknown(None)and owner.work_unknown({})
            closed=dict(passed=True,first_error=None,secondary_errors=[])
            driver.record_failure(closed,RuntimeError('SOFTWARE_PRIMARY'),stage='source_final')
            first=closed['first_error'];driver.record_failure(closed,OSError('SOFTWARE_SECONDARY'),stage='save')
            assert closed['passed']is False and closed['first_error']==first and len(closed['secondary_errors'])==1
            save('SOFTWARE_OWNER_RESULT_GATES.json',dict(passed=True,SOFTWARE=True,models=0,negative_cases=cases,first_secondary=closed))
            # Exact new prepayment and compact parent closing reference only;
            # no actual parent/REVIEW control write takes place here.
            precharge=c.O/'parent_precharge';precharge.mkdir()
            budget=wm.WriterBudget(precharge,role='SUPERVISOR_LOG',maximum_bytes=1024**2,source_identity=c.digest(source))
            original=(c.O/'SOURCE_REVIEW_ORIGINAL.bin').read_bytes()
            assert __import__('hashlib').sha256(original).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
            owner.reserve_parent_budget(budget,original,c.limits())
            planned=copy.deepcopy(parent)
            planned['rounds'].append(dict(id=C.name,scope=c.limits()['scope'],started_unix=time.time(),status='CLOSED_REFUSED_OR_FAILED',
                models_actual_vehicle=0,physical_native=0,maximum_generation_native=0,success_only_maximum_audit_native=1263600,science_revision=10,
                result=dict(passed=False,CPP_native=1263600,model_work_unknown=False,Engine=None,
                    result_path=str((c.O/'COMPLETION.json').relative_to(c.R)),physical_native=0)))
            projected=len(owner.parent_bytes(planned));assert projected+8192<=131072
            save('PARENT_RESERVATION_PROOF.json',dict(passed=True,precharged_bytes=budget._read()['charged_bytes'],maximum=1024**2,
                original_parent_bytes=len(owner.parent_bytes(parent)),projected_closed_parent_bytes=projected,parent_cap=131072,close_reserve=8192,
                no_real_parent_control_mutation=True))
            # New exact owned start-identity close helper, a stdlib sleep child
            # only. This does not repeat old OS, ROS or numerical fixtures.
            child=subprocess.Popen([sys.executable,'-c',"import time;print('OWNED_SOURCE_ONLY',flush=True);time.sleep(5)"],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
            child_identity=owner.owned_identity(child)
            assert child.stdout.readline()==b'OWNED_SOURCE_ONLY\n'
            wrong=dict(child_identity,start_ticks=child_identity['start_ticks']+1)
            try:owner.close_owned(child,wrong)
            except AssertionError as error:assert 'IDENTITY_CHANGED'in str(error)
            else:raise AssertionError('WRONG_OWNED_IDENTITY_CLOSED')
            assert child.poll()is None
            rc=owner.close_owned(child,child_identity);assert rc==-15
            child.stdout.close();child.stdin.close()
            save('OWNED_SOURCE_CHILD_CLOSE.json',dict(passed=True,models=0,identity=child_identity,wrong_identity_refused=True,returncode=rc))
            # Real production CLI owns its own fd: release qualifier lock so
            # missing admission is the actual refusal, not a lock collision.
            fcntl.flock(lock,fcntl.LOCK_UN)
            refusal=driver.execute()
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            saved=c.read(c.O/'unadmitted/RESULT.json')
            assert saved==refusal and saved['closed']and not saved['passed']and 'FULL_CPP_BATCH_NOT_ADMITTED'in saved['first_error']
            assert saved['CPP_analytical_native']==saved['Engine_constructions']==0 and not saved['secondary_errors']
            save('REAL_CLI_MISSING_ADMISSION.json',dict(passed=True,models=0,first_error=saved['first_error'],result_sha256=c.sha(c.O/'unadmitted/RESULT.json')))
            # New expected-reference authority is source-hash only here. No
            # Reader, NPZ decoder, old model or numerical audit is reexecuted.
            index_path=c.R/'runs/v1565_complete_witness_runtime_recovery/ARCHIVE_INDEX.json'
            full_path=c.R/'runs/v1565_complete_witness_runtime_recovery/FULL_REMOTE_VERIFIED.json'
            assert c.read(full_path)['passed']and c.read(full_path)['every_member_SHA_and_link_text']
            rows={row['path']:row for row in c.read(index_path)['files']}
            reference={}
            for name in ['GENERATION.json','STREAM_SEAL.json','WITNESSES.bin']:
                path=c.R/'runs/v1563_lzma_lossless_witness/model/generation'/name
                relative=str(path.relative_to(c.R));assert c.sha(path)==rows[relative]['sha256']
                source[relative]=reference[name]=c.sha(path)
            for path in [index_path,full_path,c.R/'runs/v1569_zero_tail_batch_backend/ENTRY_QUALIFICATION.json',c.R/'runs/v1569_zero_tail_batch_backend/source_target/QUALIFICATION.json']:
                source[str(path.relative_to(c.R))]=c.sha(path)
            save('QUALIFICATION.json',dict(passed=True,source_only=True,models=0,old5productionmodules_exact=True,
                old_batch_source_cases_reused_by_SHA=True,numerical_batch_equivalence_qualified=False,
                live_current_reserve_qualified=False,whole_route_passed=False,reference_sha256=reference))
            fixed=c.read(c.R/'runs/v1569_zero_tail_batch_backend/FIXED_INPUTS.json');fixed['saved_reference_sha256']=reference
            c.put(c.O/'FIXED_INPUTS.json',fixed)
            source[str((c.O/'FIXED_INPUTS.json').relative_to(c.R))]=c.sha(c.O/'FIXED_INPUTS.json')
            for path in C.iterdir():
                if path.is_file():
                    if path.suffix=='.py':ast.parse(path.read_text())
                    source[str(path.relative_to(c.R))]=c.sha(path)
            assert all(c.sha(c.R/n)==h for n,h in source.items())
            c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,
                source_only=True,models_authorized=False,numerical_batch_equivalence_qualified=False),maximum=4*1024**2)
            result.update(passed=True,source_frozen=True,source_members=len(source),negative_result_cases=len(cases),
                writer_charged_bytes=writer._read()['charged_bytes'],parent_precharged_bytes=budget._read()['charged_bytes'],bootstrap=bootstrap)
    except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        if child is not None and child.poll()is None:
            try:owner.close_owned(child,child_identity)
            except BaseException as error:result['secondary_close_error']=repr(error)
        sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start)
        c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1

if __name__=='__main__':raise SystemExit(main())
