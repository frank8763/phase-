"""Targeted original audit-hook scope and no-model OSMesa cache check."""
import ast
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class NoVehicle(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'vehicle','factory','torch','rclpy'}:raise AssertionError('GUARD_CONTEXT_QUALIFICATION_NO_VEHICLE:'+name)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'ENTRY_QUALIFICATION.json').exists()
 os.chdir(R);sys.meta_path.insert(0,NoVehicle())
 def profile(frame,event,arg):
  if event=='call'and Path(frame.f_code.co_filename).is_relative_to(R)and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py','vehicle_control.py'}:raise AssertionError('GUARD_CONTEXT_NO_RESEARCH_MODEL_OR_COMPUTE')
  if event=='c_call'and getattr(arg,'__name__','')in {'mj_step','mj_step1','mj_step2'}:raise AssertionError('GUARD_CONTEXT_NATIVE_STEP_FORBIDDEN')
 sys.setprofile(profile);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();entry=exact('v1445_guard_entry_CLI',C/'entry.py');entry.install_guard(O)
 init=exact('v1445_current_initializer_source',C/'initializer.py');contract=init.contract;guards=exact('v1445_actual_immutable_guard',C/'guard_binding.py');caches=exact('v1445_disabled_native_cache_scope',C/'task_cache.py');quota_module=exact('v1445_current32MiB_quota',C/'quota.py');boundary=exact('v1445_previous_output_boundary',R/'experiments/v1439_actual_ros_startup_close/bounded_io.py')
 prior=contract.read(R/'runs/v1443_task_local_initializer_cache/ENTRY_QUALIFICATION.json');assert prior['passed']and prior['models']==0
 for path,digest in prior['source_hashes'].items():assert contract.sha(R/path)==digest
 # The existing zero-step/CLI/once/quota implementations are reused by SHA
 # of their exact files after directory/module identifier normalization.
 same=[]
 for name in ['zero_steps.py','quota.py','entry.py']:
  old=(R/'experiments/v1443_task_local_initializer_cache'/name).read_text().replace('v1443_task_local_initializer_cache',C.name).replace('v1443_','v1445_')
  assert ast.dump(ast.parse(old),include_attributes=False)==ast.dump(ast.parse((C/name).read_text()),include_attributes=False),'CHANGED_ENTRY_SOURCE_CANNOT_REUSE:'+name
  same.append(name)
 parent_path=R/'runs/v1382_weekend_campaign/LEDGER.json';parent_before=parent_path.read_bytes();parent=json.loads(parent_before);assert parent['active_round']is None and not parent['models_now_authorized']
 negatives=[]
 def reject(label,fn,contains):
  try:fn()
  except (AssertionError,PermissionError,RuntimeError)as exc:
   assert contains in str(exc),(label,repr(exc));negatives.append(dict(case=label,error=repr(exc)));return
  raise AssertionError('IMMUTABLE_GUARD_NEGATIVE_ACCEPTED:'+label)
 reject('new_initializer_refuses_before_scope_binding',lambda:init.run({}, {}, {}),'INITIALIZER_ENTRY_PREREQUISITES_MISSING_MODELS_FORBIDDEN')
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out=O/'guard_entry';out.mkdir();quota=quota_module.EvidenceQuota(out,contract.read(C/'LIMITS.json'));quota.bind_external_names([]);quota.write_enforcement_active=True
  original=guards.ORIGINAL;node=next(x for x in ast.parse(original.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=out)
  exec(compile(ast.Module(body=[node],type_ignores=[]),str(original),'exec'),scope)
  # Install a real original-code audit hook fixed at this whole qualification
  # output. It must keep working after its original globals move elsewhere.
  with guards.bind_original_guard(O)as installed:
   sys.addaudithook(scope['write_guard'])
   reject('second_hook_refused',lambda:sys.addaudithook(scope['write_guard']),'MULTIPLE_INITIALIZER_WRITE_GUARDS')
  scope['OUT']=R/'runs/v858_nav2_verified'
  assert installed['installed_original_guard_count']==1
  with boundary.OutputBoundary(out,quota.charge_write):
   quota.prepare_grant(16*1024**2,phase='CANONICAL_INITIALIZER_ONLY',valid_for_s=180,external_writers=[])
   quota.atomic(out/'AFTER_MUTABLE_OUT_DRIFT.json',dict(passed=True,software_only=True,mutable_OUT=str(scope['OUT']),original_guard_scope_remained=str(O)),init.io.atomic)
   reject('original_immutable_hook_refuses_other_run',lambda:(R/'runs/v858_nav2_verified/FORBIDDEN_GUARD_TEST').write_text('no'),'BOUNDED_OUTPUT_PATH_ESCAPE')
   # Call the bound original code directly to verify its own limits as well
   # as the outer boundary, without attempting a real forbidden filesystem op.
   bound=guards.bind_function(scope['write_guard'],O)
   reject('original_guard_refuses_other_run',lambda:bound('open',(str(R/'runs/v858_nav2_verified/FORBIDDEN_GUARD_TEST'),'w',os.O_WRONLY|os.O_CREAT)),'Write outside isolated experiment')
   reject('Stage_read_restriction_retained',lambda:bound('open',(str(O/'training/e2e_forbidden.txt'),'r',0)),'Stage source excluded')
   reject('original_rename_restriction_retained',lambda:bound('os.rename',(str(out/'x'),str(R/'runs/v858_nav2_verified/x'))),'Filesystem mutation outside isolated experiment')
   def foreign(*_):return
   reject('unrecognized_hook_refused',lambda:guards.bind_function(foreign,O),'UNKNOWN_INITIALIZER_AUDIT_HOOK')
   quota.atomic(out/'FIRST_ERROR_AND_RESULT_SOFTWARE.json',dict(first_error='SOFTWARE_PRIMARY',secondary_errors=[dict(error='SOFTWARE_SECONDARY')],not_actual_failure=True),init.io.atomic)
   started=time.monotonic();before=set(p.relative_to(out)for p in out.rglob('*')if p.is_file())
   context=None
   with caches.TaskLocalCaches(out):
    assert os.environ['MESA_SHADER_CACHE_DISABLE']=='true'
    # Simulate the old runner resetting the cache directory while retaining
    # the native no-cache switch. No MuJoCo model/data object is created.
    os.environ['MESA_SHADER_CACHE_DIR']=str(out/'cache')
    import mujoco as mj
    class NoModelData:
     def __call__(self,*_,**__):raise AssertionError('GUARD_CONTEXT_MJMODEL_OR_DATA_FORBIDDEN')
     def __getattr__(self,name):raise AssertionError('GUARD_CONTEXT_MJMODEL_OR_DATA_FORBIDDEN:'+name)
    original_model,original_data=mj.MjModel,mj.MjData;mj.MjModel=NoModelData();mj.MjData=NoModelData()
    try:
     from mujoco.osmesa import GLContext
     context=GLContext(16,16);context.make_current()
     from OpenGL import GL
     GL.glClearColor(0.,0.,0.,1.);GL.glClear(GL.GL_COLOR_BUFFER_BIT);GL.glFinish()
     renderer=GL.glGetString(GL.GL_RENDERER).decode();version=GL.glGetString(GL.GL_VERSION).decode()
     assert 'llvmpipe'in renderer.lower()or'softpipe'in renderer.lower(),'OSMESA_SOFTWARE_RENDERER_NOT_VERIFIED'
    finally:
     if context is not None:context.free()
     mj.MjModel,mj.MjData=original_model,original_data
    assert not list(out.rglob('mesa_shader_cache*')),'NATIVE_MESA_CACHE_NOT_DISABLED'
    after=set(p.relative_to(out)for p in out.rglob('*')if p.is_file());assert after==before,'UNACCOUNTED_NATIVE_CACHE_FILES_AFTER_CONTEXT'
   quota.atomic(out/'OSMESA_NO_MODEL_RECEIPT.json',dict(renderer=renderer,version=version,context_module=GLContext.__module__,native_cache_disabled=True,unexpected_native_file_count=0,MjModel_constructions=0,MjData_constructions=0,model_integrations=0,context_closed=True),init.io.atomic)
  quota.retire_grant();quota.write_enforcement_active=False
  assert parent_path.read_bytes()==parent_before
  gates=dict(prior['entry_gates']);gates['immutable_original_guard_scope_and_native_Mesa_cache']=True
  proof=dict(passed=True,models=0,physical_native=0,analytical_integrations=0,allocator_recomputations=0,actual_replay_native=0,actual_cpu=[2],original_writeguard=True,original_writeguard_code_identical=True,immutable_OUT_real_audit_hook_installed=True,original_Stage_and_path_restrictions_retained=True,mutable_B_OUT_drift_did_not_change_guard=True,actual_OSMesa_context_without_model_or_data=True,OSMesa_renderer=renderer,native_cache_disabled_and_zero_native_files_verified=True,context_wall_s=time.monotonic()-started,entry_gates=gates,changed_runtime_source_checks_passed=True,reused_initializer_entry_qualification_SHA=contract.sha(R/'runs/v1441_initializer_definition_import/ENTRY_QUALIFICATION.json'),reused_task_local_cache_qualification_SHA=contract.sha(R/'runs/v1443_task_local_initializer_cache/ENTRY_QUALIFICATION.json'),unchanged_normalized_source_files=same,negative_cases=negatives,actual_native_C_save_executed=False,actual_canonical_initializer_called=False,initializer_runtime_qualified=False,physical_route_admission=False,all_runs_peak=contract.storage_preflight(),source_hashes={str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()})
  init.io.atomic(O/'ENTRY_QUALIFICATION.json',proof);print(json.dumps(proof));return 0

if __name__=='__main__':raise SystemExit(main())
