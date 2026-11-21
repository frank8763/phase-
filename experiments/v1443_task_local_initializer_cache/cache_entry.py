"""Targeted real Torch configuration/cache I/O; no canonical factory or models."""
import ast
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class NoPhysical(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','rclpy'}:raise AssertionError('CACHE_QUALIFICATION_PHYSICAL_IMPORT_FORBIDDEN:'+name)

def function_AST(path,name):
 tree=ast.parse(path.read_text());node=next(x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))and x.name==name);return ast.dump(node,include_attributes=False)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'ENTRY_QUALIFICATION.json').exists()
 os.chdir(R);sys.meta_path.insert(0,NoPhysical())
 def profile(frame,event,arg):
  if event=='call':
   file=Path(frame.f_code.co_filename);name=frame.f_code.co_name
   if(name=='__init__'and '/torch/nn/modules/'in str(file))or(file.is_relative_to(R)and name in {'__init__','step','compute'}and file.name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py','vehicle_control.py'}):raise AssertionError('CACHE_QUALIFICATION_MODEL_OR_COMPUTE_FORBIDDEN')
 sys.setprofile(profile);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();entry=exact('v1443_exact_initializer_CLI',C/'entry.py');entry.install_guard(O)
 contract=exact('v1443_cache_contract',C/'contract.py');owner=exact('v1443_cache_owner',C/'owner.py');initializer=exact('v1443_cache_initializer',C/'initializer.py');cache=exact('v1443_actual_task_cache_scope',C/'task_cache.py');zeros=exact('v1443_repo_only_native_guard',C/'zero_steps.py');quota_module=exact('v1443_narrow_evidence',C/'quota.py');boundary=exact('v1443_original_IO_and_C_save',R/'experiments/v1439_actual_ros_startup_close/bounded_io.py')
 prior=R/'experiments/v1441_initializer_definition_import';proof_path=R/'runs/v1441_initializer_definition_import/ENTRY_QUALIFICATION.json';previous=contract.read(proof_path);assert previous['passed']and previous['models']==0
 reused=[('initializer.py','call_factory_once'),('initializer.py','save_error'),('owner.py','BoundedConsole'),('owner.py','claim_once'),('contract.py','check_window'),('contract.py','storage_preflight'),('quota.py','EvidenceQuota')]
 for name,fn in reused:assert function_AST(C/name,fn)==function_AST(prior/name,fn),'CHANGED_FUNCTION_CANNOT_REUSE_ENTRY_GATE:'+fn
 for name,digest in previous['source_hashes'].items():assert contract.sha(R/name)==digest
 negatives=[]
 try:initializer.run({}, {}, {})
 except RuntimeError as exc:assert str(exc)=='INITIALIZER_ENTRY_PREREQUISITES_MISSING_MODELS_FORBIDDEN';negatives.append('new_wrapper_refuses_before_cache_or_physical_binding')
 else:raise AssertionError('UNQUALIFIED_CACHE_INITIALIZER_ADMITTED')
 parent_path=R/'runs/v1382_weekend_campaign/LEDGER.json';parent_before=parent_path.read_bytes();parent=json.loads(parent_before);assert parent['active_round']is None and not parent['models_now_authorized']
 import fcntl
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  out=O/'cache_entry';out.mkdir();quota=quota_module.EvidenceQuota(out,contract.read(C/'LIMITS.json'));quota.bind_external_names([]);quota.write_enforcement_active=True
  prior_tempdir=tempfile.tempdir;old_env={name:os.environ.get(name)for name in ['TMPDIR','TEMP','TMP','XDG_CACHE_HOME','TORCHINDUCTOR_CACHE_DIR','TORCH_EXTENSIONS_DIR','TRITON_CACHE_DIR','MPLCONFIGDIR']}
  fake=SimpleNamespace(mj_step=lambda *_:None,mj_step1=lambda *_:None,mj_step2=lambda *_:None)
  started=time.monotonic()
  try:
   with cache.TaskLocalCaches(out),boundary.OutputBoundary(out,quota.charge_write),zeros.forbid_steps(fake)as attempts:
    quota.prepare_grant(16*1024**2,phase='CANONICAL_INITIALIZER_ONLY',valid_for_s=180,external_writers=[])
    assert Path(tempfile.gettempdir())==out/'tmp'
    with tempfile.NamedTemporaryFile()as stream:stream.write(b'cache-probe');stream.flush();assert Path(stream.name).is_relative_to(out/'tmp')
    # This is the exact library/config call that refused before V1441 could
    # build a vehicle. It imports no canonical factory and no nn.Module object.
    import torch
    torch.use_deterministic_algorithms(True)
    assert torch.are_deterministic_algorithms_enabled()
    import torch._inductor.runtime.cache_dir_utils as cache_utils
    actual_cache=Path(cache_utils.cache_dir());assert actual_cache==out/'cache/torch_inductor'
    paths={name:os.environ[name]for name in old_env};assert all(Path(path).is_relative_to(out)for path in paths.values())
    quota.atomic(out/'ACTUAL_CACHE_PATHS.json',dict(actual_torch_config_call=True,tempfile_dir=tempfile.gettempdir(),torch_cache=str(actual_cache),environment=paths,MuJoCo_imported=False,canonical_factory_called=False),initializer.io.atomic)
    # Exercise only the altered repository-path predicate, without invoking a
    # real Predictor or borrowing any saved numerical branch.
    scope={};exec(compile('def __init__():\n return 1\n',str(R/'experiments/v1114_coupled_steering_mode/coupled_model.py'),'exec'),scope)
    try:scope['__init__']()
    except RuntimeError as exc:assert str(exc)=='INITIALIZER_PREDICTOR_OR_ALLOCATOR_COMPUTE_FORBIDDEN';negatives.append('Phase_constructor_frame_refused')
    else:raise AssertionError('PHASE_CONSTRUCTOR_GUARD_LOST')
    scope={};exec(compile('def __init__():\n return 1\n',str(Path(torch.__file__).parent/'_inductor/kernel.py'),'exec'),scope);assert scope['__init__']()==1
    try:fake.mj_step(None)
    except RuntimeError as exc:assert str(exc)=='INITIALIZER_NATIVE_STEPS_FORBIDDEN';negatives.append('native_step_API_still_refused')
    else:raise AssertionError('NATIVE_GUARD_LOST')
   assert tempfile.tempdir==prior_tempdir and all(os.environ.get(name)==value for name,value in old_env.items())
  finally:quota.retire_grant();quota.write_enforcement_active=False
  assert parent_path.read_bytes()==parent_before
  # The CLI source now returns explicit integers for a launched completion.
  tree=ast.parse((C/'entry.py').read_text());main_node=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='main');assert any(isinstance(x,ast.Return)and isinstance(x.value,ast.IfExp)and isinstance(x.value.body,ast.Constant)and x.value.body.value==0 and isinstance(x.value.orelse,ast.Constant)and x.value.orelse.value==1 for x in ast.walk(main_node))
  gates=dict(previous['entry_gates']);gates.update(task_local_temp_and_torch_cache_write_path=True,actual_no_model_entry_refusal=True,forbidden_native_step_guard=True,whole_storage_peak=True)
  proof=dict(passed=True,models=0,physical_native=0,analytical_integrations=0,allocator_recomputations=0,actual_replay_native=0,actual_cpu=[2],original_writeguard=True,nn_Module_and_Phase_predictor_compute_profile_guard=True,actual_torch_deterministic_configuration_called=True,task_local_temp_and_cache_write_path_verified=True,changed_runtime_source_checks_passed=True,entry_gates=gates,reused_initializer_entry_qualification_SHA=contract.sha(proof_path),unchanged_function_AST_gates=[list(row)for row in reused],negative_cases=negatives,actual_native_C_save_executed=False,actual_canonical_initializer_called=False,initializer_runtime_qualified=False,physical_route_admission=False,all_runs_peak=contract.storage_preflight(),wall_s=time.monotonic()-started,source_hashes={str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()})
  initializer.io.atomic(O/'ENTRY_QUALIFICATION.json',proof);print(json.dumps(proof));return 0

if __name__=='__main__':raise SystemExit(main())
