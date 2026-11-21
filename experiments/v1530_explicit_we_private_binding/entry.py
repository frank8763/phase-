"""Once exact original-WE definition-import target; no model instances."""
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
import types

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R/'runs'/C.name


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    assert sorted(os.sched_getaffinity(0))==[2] and os.environ.get('PHASE_REPO')==str(R)
    started=time.monotonic();wall=time.time()
    assert wall+120<1795395600
    with(O/'ENTRY_ONCE_CLAIM.json').open('x')as stream:
        json.dump(dict(unix=wall,scope='ORIGINAL_WE_DEFINITIONS_ONLY',models=0),stream)
    common=load('v1530_original_immutable_guard_only',R/'experiments/v1504_priest_namespace_worker/common.py')
    result=dict(passed=False,closed=False,scope='ORIGINAL_WE_DEFINITIONS_ONLY',models=0,
                analytical_native=0,physical_native=0,Allocator_recomputations=0,replay_native=0,
                optimizer_calls=0,phase_FFI_library_loads=0,method_origin_authorized=False,
                numerical_or_physical_admission=False)

    class NoModels(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'jax','jaxlib','mujoco','torch','rclpy','vehicle','factory'}:
                raise AssertionError('WE_DEFINITION_TARGET_FORBIDDEN_IMPORT:'+name)
    finder=NoModels();sys.meta_path.insert(0,finder)
    allowed_initializers={C/'definitions.py',R/'experiments/v1436_pathlib_control_rename/writer_budget.py',
                          R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}
    forbidden=[]
    def profile(frame,event,arg):
        if event!='call':return
        path=Path(frame.f_code.co_filename)
        if path.is_absolute() and path.is_relative_to(R) and frame.f_code.co_name in {'__init__','step','compute','simulate','expand','predict'}:
            if path not in allowed_initializers:
                forbidden.append(dict(file=str(path.relative_to(R)),name=frame.f_code.co_name))
                raise AssertionError('WE_DEFINITION_TARGET_NO_CONSTRUCT_OR_NUMERICAL_CALL')
        assert time.monotonic()-started<120,'WE_DEFINITION_TARGET_MONOTONIC_LIMIT'
    sys.setprofile(profile)
    try:
        parent=common.read(R/'runs/v1382_weekend_campaign/LEDGER.json')
        assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
        with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            frozen=common.read(R/'runs/v1528_fixed_we_evaluation_contract/SOURCE_FREEZE.json')['files']
            remote=common.read(R/'runs/v1528_fixed_we_evaluation_contract/CURRENT_SOURCE_REMOTE_RECOVERY.json')
            assert remote['passed'] and remote['all_frozen_members_remote_chain_covered'] and not remote['uncovered_members']
            assert remote['source_freeze_sha256']==common.sha(R/'runs/v1528_fixed_we_evaluation_contract/SOURCE_FREEZE.json')
            assert all(common.sha(R/name)==identity for name,identity in frozen.items())
            definitions=load('phase_v1530_new_definitions_only',C/'definitions.py')
            negative=[]
            def rejects(label,fn):
                try:fn()
                except (AssertionError,KeyError)as error:negative.append(dict(name=label,error=repr(error)))
                else:raise AssertionError('WE_DEFINITION_NEGATIVE_ACCEPTED:'+label)
            changed=dict(frozen);changed[definitions.MODEL]='0'*64
            rejects('changed_original_model_source',lambda:definitions.preflight(changed,modules={}))
            rejects('foreign_existing_bindings',lambda:definitions.preflight(frozen,modules={'bindings':types.SimpleNamespace(__file__='/unrelated/bindings.py')}))
            rejects('foreign_existing_runtime',lambda:definitions.preflight(frozen,modules={'runtime':types.SimpleNamespace(__file__='/unrelated/runtime.py')}))
            rejects('foreign_existing_kernel',lambda:definitions.preflight(frozen,modules={'kernel':types.SimpleNamespace(__file__='/unrelated/kernel.py')}))
            rejects('method_origin_not_accepted',definitions.create_origin)
            rejects('predictor_not_admitted',definitions.construct_predictor)
            rejects('FFI_not_admitted',definitions.construct_engine)
            bootstrap=definitions.bootstrap(frozen)
            common.guard(O)
            def audit(event,args):
                if event=='ctypes.dlopen' and args and isinstance(args[0],str) and str(R)in args[0]:
                    raise AssertionError('WE_DEFINITION_TARGET_PHASE_FFI_DLOPEN_FORBIDDEN')
                if event=='subprocess.Popen':
                    raise AssertionError('WE_DEFINITION_TARGET_SUBPROCESS_FORBIDDEN_AFTER_BOOTSTRAP')
            sys.addaudithook(audit)
            authority=dict(scope='ORIGINAL_WE_DEFINITIONS_ONLY',models_authorized=False,method_origin_authorized=False,
                           boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                           absolute_deadline_unix=min(wall+120,1795395600),hard_stop_monotonic=started+120)
            prior_sys_path=list(sys.path)
            values,proof=definitions.load_definitions(frozen,authority=authority,lock=lock)
            assert list(sys.path)==prior_sys_path
            assert values['model'].Predictor is not values['bindings'].Predictor
            assert proof['original_V1159_V1118_V1114_inheritance'] and not forbidden
            proof.update(bootstrap=bootstrap,negative_cases=negative,forbidden_calls=forbidden,
                         sys_path_restored=True,loaded_exact_V1159_not_plain_or_scalar_subclass=True,
                         source_entry_not_response_generation=True)
            task=O/'definitions_target';task.mkdir()
            budgets=load('v1530_original_writer',R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
            boundary=load('v1530_original_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
            codec=load('v1530_original_qualified_json',R/'experiments/v1507_priest_response_evidence/branch_store.py')
            writer=budgets.WriterBudget(task,role='PLANNER',maximum_bytes=2*1024**2,source_identity=common.digest(frozen))
            with boundary.OutputBoundary(task,writer.reserve):
                codec.write_atomic(task/'DEFINITION_BINDING_PROOF.json',codec.encoded(proof),writer)
                assert common.read(task/'DEFINITION_BINDING_PROOF.json')==proof
            sources=frozen.copy()
            for path in C.iterdir():
                if path.is_file():sources[str(path.relative_to(R))]=common.sha(path)
            for path in [R/'runs/v1528_fixed_we_evaluation_contract/CURRENT_SOURCE_REMOTE_RECOVERY.json']:
                sources[str(path.relative_to(R))]=common.sha(path)
            assert all(common.sha(R/name)==identity for name,identity in sources.items())
            common.put(O/'SOURCE_FREEZE.json',dict(files=sources,definition_import_only_qualified=True,
                       numerical_body_unchanged=True,model_epoch_or_numeric_response_qualified=False,
                       phase_FFI_library_loaded=False))
            result.update(passed=True,source_frozen=True,new_negative_cases=len(negative),
                          exact_original_definition_chain=True,writer_charged_bytes=writer._read()['charged_bytes'],
                          full_dynamic_callgraph_qualified=False,method_epoch_qualified=False)
    except BaseException as error:
        result.update(first_error=repr(error),traceback=traceback.format_exc(),forbidden_calls=forbidden)
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder)
        result.update(closed=True,wall_s=time.monotonic()-started)
        common.put(O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
