"""One software SOURCE pass, no native loader or model imports."""
from context import C,O,R,read,sha,put
import ast,copy,time,subprocess
from authority import validate

def main():
 assert not(O/'SOURCE_ONCE_CLAIM.json').exists();put(O/'SOURCE_ONCE_CLAIM.json',dict(unix=time.time(),DLL_loads=0,models=0))
 prior=R/'runs/v1954_rpp_lock_held_component_owner';assert read(prior/'SOURCE_QUALIFICATION.json')['passed']and read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']and read(prior/'POST_SOURCE_STORAGE_BARRIER.json')['passed']
 kwargs=dict(now=10.,mono=10.,boot='b',freeze_sha='f',fixture_sha='i',recovery_sha='r');good=dict(scope='RPP_SYNTHETIC_STRAIGHT_API_ONLY',controller_constructor_cap=1,valid_solver_cap=1,physics_authorized=False,boot_id='b',absolute_deadline_unix=20.,hard_stop_monotonic=20.,source_freeze_sha256='f',fixture_sha256='i',source_recovery_sha256='r');assert validate(good,**kwargs);neg=[]
 for k,v in [('scope','WHOLE_NAVIGATION'),('controller_constructor_cap',2),('valid_solver_cap',2),('physics_authorized',True),('boot_id','bad'),('absolute_deadline_unix',9.),('hard_stop_monotonic',9.),('source_freeze_sha256','bad'),('fixture_sha256','bad'),('source_recovery_sha256','bad')]:
  a=copy.deepcopy(good);a[k]=v
  try:validate(a,**kwargs)
  except AssertionError:neg.append(k)
  else:raise AssertionError('UNADMITTED_SCOPE_ACCEPTED:'+k)
 probe='import sys;sys.path.insert(0,'+repr(str(C))+');from context import C,O;import authority,binding;assert C.name=='+repr(C.name)+';print(\"ISOLATED_CONTEXT_OK_NO_DLL\")'
 p=subprocess.run(['/usr/bin/python3.12','-I','-B','-S','-c',probe],capture_output=True,text=True,timeout=5);assert p.returncode==0 and p.stdout.strip()=='ISOLATED_CONTEXT_OK_NO_DLL';put(O/'ISOLATED_ENTRY_SOFTWARE_PROOF.json',dict(passed=True,DLL_loads=0,controller_constructors=0,stdout=p.stdout.strip()))
 old_component=R/'runs/v1952_rpp_component_entry_checked';assert read(old_component/'COMPONENT_POST_STORAGE_BARRIER.json')['passed']and read(old_component/'RESULT.json')['valid_solver_attempts']==0
 observed=read(old_component/'CONSTRUCTOR_DEPENDENCY_DIAGNOSIS.json')['extra_exact_ELF_files'];pins=read(O/'CONSTRUCTOR_DEPENDENCY_PINS.json');assert len(observed)==24 and all(pins['namespace_ELF_files_SHA256'].get(n)==h for n,h in observed.items())
 fixture=read(O/'FIXTURE.json');assert sha(R/fixture['original_parameter_file'])==fixture['original_parameter_sha256'];params=read(R/fixture['original_parameter_file']);assert len(__import__('json').loads(params['local_costmap']['local_costmap']['ros__parameters']['footprint']))==36
 frozen=read(prior/'SOURCE_FREEZE.json')['files'].copy();frozen.update(read(O/'CONSTRUCTOR_DEPENDENCY_PINS.json')['files'])
 for p in C.iterdir():
  if p.is_file():
   if p.suffix=='.py':ast.parse(p.read_text())
   frozen[str(p.relative_to(R))]=sha(p)
 for p in [O/'FIXTURE.json',O/'CONSTRUCTOR_DEPENDENCY_PINS.json',O/'ISOLATED_ENTRY_SOFTWARE_PROOF.json',O/'AUTHORIZATION.json']:frozen[str(p.relative_to(R))]=sha(p)
 assert all(sha(R/n)==h for n,h in frozen.items());put(O/'SOURCE_FREEZE.json',dict(files=frozen,models_authorized=False,namespace_ELF_files_SHA256=read(O/'CONSTRUCTOR_DEPENDENCY_PINS.json')['namespace_ELF_files_SHA256']))
 put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(prior.relative_to(R)),freeze_sha256=sha(prior/'SOURCE_FREEZE.json'),recovery_path=str((prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
 result=dict(passed=True,closed=True,models=0,DLL_loads=0,controller_constructors=0,solver_calls=0,physical_native=0,replay_native=0,negative_cases=neg,source_members=len(frozen),extra_exact_observed_ELFs=24,lifetime_execution_lock_in_entry=True,synthetic_fixture_only=True,numerical_admission=False)
 put(O/'SOURCE_QUALIFICATION.json',result);put(O/'SOURCE_OUTER_CLOSED.json',dict(passed=True,closed=True,models=0,software_only=True));print(__import__('json').dumps(result))
if __name__=='__main__':main()
