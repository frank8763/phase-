"""Production admission through real guard/boundary with explicit fake metadata.

The software authority root is separate from the real component. No factory,
renderer, tensor library or scientific model is imported or constructed.
"""
from pathlib import Path
import os,sys,json,hashlib,importlib.util,fcntl,time,types
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
assert os.sched_getaffinity(0)=={2}and not(S/'LIVE_ADMISSION_CHECK.json').exists()
locks=[]
for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
 f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
class NoModels:
 def find_spec(self,fullname,path=None,target=None):
  assert fullname.split('.')[0]not in {'torch','mujoco','numpy','stable_baselines3'},'MODEL_LIBRARY_FORBIDDEN_IN_SOFTWARE_ADMISSION_TEST'
ban=NoModels();sys.meta_path.insert(0,ban)
def load(n,p):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
ctx=load('explicit_software_authority_context',C/'context.py')
root=S/'software_authority';o=root/'component';out=o/'output';out.mkdir(parents=True,exist_ok=False)
ctx.SOURCE=root;ctx.O=o
def write(p,v):p.write_text(json.dumps(dict(explicit_software_fixture=True,**v),sort_keys=True)+'\n')
safe=out/'runtime_source.txt';safe.write_text('EXPLICIT SOFTWARE SOURCE FIXTURE')
history=root/'history';history.mkdir();old=history/'BODY_COMMANDS.json';old.write_text('EXPLICIT SOFTWARE BASENAME FIXTURE NO PHYSICAL CONTROLS')
guard_path=R/'experiments/v1180_fresh_recovery_chain/chain_tools.py'
files={str(p.relative_to(R)):ctx.sha(p)for p in [safe,old,guard_path,C/'context.py',C/'source_scope.py']}
write(root/'SOURCE_FREEZE.json',dict(files=files));write(root/'SOURCE_QUALIFICATION.json',dict(passed=True,models=0));write(root/'CURRENT_SOURCE_REMOTE_RECOVERY.json',dict(all_frozen_members_remote_chain_covered=True,not_an_actual_remote_proof=True))
task=dict(component_not_navigation=True,maximum_control_native=10,stop_native=2200,task_id=ctx.RID,output=str(out))
write(o/'PILOT_ADMISSION.json',dict(scope='FILTER_CURRENT_VEHICLE_COMPONENT',models_authorized=True,assignment=task,independent_parallel_owner=True,source_freeze_sha256=ctx.sha(root/'SOURCE_FREEZE.json'),not_real_model_authorization=True))
write(o/'PILOT_WINDOW.json',dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),absolute_deadline_unix=time.time()+300,hard_stop_monotonic=time.monotonic()+300));write(o/'PILOT_ONCE_CLAIM.json',dict(not_an_actual_claim=True))
# Genuine production body validates and bootstraps BEFORE actual history guard.
initial=ctx.admission(task);assert initial[2]==files
assert set(ctx._SOURCE_SCOPE._files)==set(files)
history_module=load('unchanged_history_binding_only',C/'history_binding.py');history_module.install(out,files)
boundary=load('unchanged_output_boundary_only',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');emitted=[];negative=[]
def refused(name,fn,substring):
 try:fn()
 except AssertionError as e:assert substring in str(e),(name,str(e));negative.append(dict(case=name,error=str(e)))
 else:raise AssertionError('SOFTWARE_ADMISSION_NEGATIVE_ACCEPTED:'+name)
with boundary.OutputBoundary(out,lambda p,n:emitted.append(n)):
 write(out/'INITIALIZATION_ATTEMPT.json',dict(not_an_actual_initializer=True))
 assert ctx.admission(task)[2]==files
 # Cached metadata stays valid across the actual named live consumers' calls;
 # no consumer/model function is executed by this source-only regression.
 for name in ['union_sampler','policy107','policy186','private_snapshot0','private_snapshot5','private_snapshot10']:
  assert ctx.admission(task)[2]==files
 refused('old_direct_read_still_blocked',lambda:old.read_bytes(),'FRESH_HISTORY_READ_FORBIDDEN BODY_COMMANDS.json')
 from source_scope import SourceScope
 cached=ctx._SOURCE_SCOPE;ctx._SOURCE_SCOPE=SourceScope(R)
 refused('cold_actual_admission_after_initializer',lambda:ctx.admission(task),'SOURCE_BOOTSTRAP_AFTER_INITIALIZER_FORBIDDEN');ctx._SOURCE_SCOPE=cached
 # No granting a new component authority or writing outside its output occurs.
 refused('foreign_write_stays_blocked',lambda:(root/'FOREIGN_WRITE.txt').write_text('not allowed'),'OUTPUT')
 safe.write_text('EXPLICIT CHANGED RUNTIME SOURCE')
 refused('runtime_source_tamper_rejected',lambda:ctx.admission(task),'RUNTIME_READABLE_SOURCE_HASH_CHANGED')
assert not(S/'components/SCCR/PILOT_ADMISSION.json').exists()and not(S/'components/SCCR/actual').exists()
assert not any(n in sys.modules for n in ['torch','mujoco','numpy','stable_baselines3']);sys.meta_path.remove(ban)
v=dict(passed=True,closed=True,scope='PRODUCTION_CONTEXT_ADMISSION_WITH_REAL_ORIGINAL_HISTORY_GUARD_AND_OUTPUT_BOUNDARY',explicit_software_authority_fixture_only=True,real_component_never_authorized=True,preinitializer_full_source_bootstrap_passed=True,postinitializer_and_six_live_authority_metadata_calls_passed=True,original_history_guard_unchanged=True,negative_cases=negative,emitted_fixture_bytes=sum(emitted),models=0,NN_inference=0,renderer_constructors=0,physics=0,replay=0,source_once_claimed=False,source_SHA256={str(p.relative_to(R)):ctx.sha(p)for p in [Path(__file__),C/'context.py',C/'source_scope.py',C/'history_binding.py',guard_path]})
(S/'LIVE_ADMISSION_CHECK.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:x for k,x in v.items()if k not in ['negative_cases','source_SHA256']}))
