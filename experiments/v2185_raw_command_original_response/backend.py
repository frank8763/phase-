"""Admitted original analytic bindings; no old owner, factory or entrypoint."""
import hashlib,importlib.abc,importlib.machinery,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace as NS
from context import R,sha,require_admission
Q='experiments/v1160_safe_terminal_connection/search.py'
RESPONSE='experiments/v1922_dwa_five_admission_checked/response.py'
ALIASES={'kernel':'experiments/v1067_causal_replan_brake_reserve/kernel.py','runtime':'experiments/v1118_coupled_live_qualification/runtime.py','bindings':'experiments/v1121_coupled_route_night/bindings.py','prediction':'experiments/rpccr_execution_core/prediction.py'}
class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,path=None,target=None):
        assert name.split('.')[0]not in {'mujoco','torch','jax','gym','gymnasium','stable_baselines3','vehicle','factory'},'ANALYTIC_SCOPE_PHYSICAL_IMPORT_REFUSED:'+name
        return None

def bind():
    admission,window,source=require_admission()  # Before NumPy or analytic module loading.
    import numpy as np
    guard=NoPhysical();sys.meta_path.insert(0,guard);loaded={};before_path=sys.path[:]
    original_exec=importlib.machinery.SourceFileLoader.exec_module
    def checked_exec(loader,module):
        path=Path(loader.path).resolve()
        if path.is_relative_to(R):
            name=str(path.relative_to(R));assert source.get(name)==sha(path),'UNPINNED_ANALYTIC_MODULE:'+name
            assert not any(x in name for x in ['/scene_binding.py','/physical.py','/driver.py','/owner.py','/vehicle.py']), 'FORBIDDEN_ANALYTIC_SCOPE_MODULE:'+name
            loaded[name]=sha(path)
        return original_exec(loader,module)
    importlib.machinery.SourceFileLoader.exec_module=checked_exec
    def load(name,relative):
        p=R/relative;assert source[relative]==sha(p)
        spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
    try:
        # Same frozen binding sequence as original runtime_binding.science(),
        # without configure_owner(), an old task/window or a physical factory.
        sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
        sys.path.insert(0,str(R/'experiments/v1121_coupled_route_night'))
        q=load('v2185_original_analytic_q',Q)
        for name,relative in ALIASES.items():assert Path(sys.modules[name].__file__).resolve()==R/relative,'ANALYTIC_ALIAS_MISMATCH:'+name
        assert Path(q.model.__file__).resolve()==R/'experiments/v1159_bounded_steering_load/model.py'
        assert Path(q.initial.__code__.co_filename).resolve()==R/'experiments/v1118_coupled_live_qualification/runtime.py'
        assert Path(q.helper.checks.__code__.co_filename).resolve()==R/'experiments/v1035_signed_timed_input_source/whole_input.py'
        response=load('v2185_exact_original_response',RESPONSE)
    except BaseException:
        importlib.machinery.SourceFileLoader.exec_module=original_exec
        raise
    finally:
        sys.path[:]=before_path
    # The original prove function resolves kernel from sys.modules; retain all
    # already bound module objects for the two fixed cases. No science() call.
    return NS(q=q,response=response,source=source,loaded_module_SHA256=loaded,physical_import_guard=guard,admission=admission,window=window,np=np,restore_import_guard=lambda:setattr(importlib.machinery.SourceFileLoader,'exec_module',original_exec))
