"""Actual OS identity positives/negatives plus dry pipeline until first model boundary."""
import ast,hashlib,importlib.abc,json,os,subprocess,sys,time
from pathlib import Path
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('QUALIFICATION_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;ROOT=R/'runs/v842_os_identity_continuation_20261106';ROOT.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'experiments/staged_audit_completion_20261106'));from evidence_rules import read,dump,sha
claim=read(R/'runs/staged_audit_completion_20261106/DEVELOPMENT12_WINDOW_CLAIM.json');assert time.time()+6500<claim['absolute_deadline_unix']
assert not(R/'runs/v842_staged_long_navigation/development12').exists()
pid=os.getpid();entry=str(Path(__file__).resolve());commands=[(['--entrypoint',entry,'--deadline',str(time.time()+60)],True),(['--entrypoint',str(R/'experiments/staged_90_then12_20261106/campaign.py'),'--deadline',str(time.time()+60)],False),(['--entrypoint',entry,'--deadline',str(time.time()-1)],False)];records=[]
for i,(args,expected)in enumerate(commands):
 out=subprocess.run([sys.executable,'-B',str(C/'os_watch.py'),'--probe-only','--pid',str(pid),*args],capture_output=True,text=True,timeout=5);(ROOT/f'identity_final_case{i}.console').write_text(out.stdout+out.stderr);assert(out.returncode==0)==expected;records.append(dict(case=i,exit=out.returncode,expected_pass=expected))
import engine
saved=(engine.O,engine.unchanged);engine.O=ROOT/'dry_run_full_fixture';engine.O.mkdir();(engine.O/'pilot90').mkdir();(engine.O/'pilot90/PREFLIGHTS.json').write_bytes((R/'runs/v842_staged_long_navigation/pilot90/PREFLIGHTS.json').read_bytes());engine.unchanged=lambda:None;calls=[]
original_process=engine.subprocess.Popen
class BoundaryReached(BaseException):pass
class Fake:
 def __init__(self,cmd,*args,**kwargs):
  calls.append(list(map(str,cmd)))
  assert not any('run_static.py'in x for x in cmd),'NO_MODEL_CALL_BEFORE_PREFLIGHT'
  phase=engine.O/'development12'
  if 'audit_field_preflight.py'in cmd:dump(phase/'PREFLIGHT_INDEPENDENT_AUDIT.json',dict(status='PASS'))
  self.pid=-1
 def wait(self,timeout):return 0
 def poll(self):return 0
def intercept(cmd,*args,**kwargs):
 if any('run_static.py'in str(x)for x in cmd):
  assert '--name'in cmd and cmd[cmd.index('--name')+1]=='long_repeat02','WRONG_FIRST_MODEL_TASK'
  raise BoundaryReached('EXPECTED_FIRST_NAVIGATION_BOUNDARY_NO_MODELS')
 if any(str(x).endswith('/finalize.py')for x in cmd):raise RuntimeError('QUALIFICATION_FINALIZER_BLOCKED')
 return Fake(cmd,*args,**kwargs)
engine.subprocess.Popen=intercept
guard=(R/'REVIEW_PENDING').read_bytes()
try:
 # stage_run catches all exceptions and finalizes. Fake finalizer must not claim completion.
 try:engine.stage_run('development12',claim['absolute_deadline_unix'],read(R/'runs/staged_audit_completion_20261106/SUPPLEMENT_FINALIZED.json'))
 except RuntimeError as e:assert str(e)=='QUALIFICATION_FINALIZER_BLOCKED'
 error=read(engine.O/'development12/ERROR.json');assert error['type']=='BoundaryReached'and'EXPECTED_FIRST_NAVIGATION_BOUNDARY'in error['message']
 assert not any('audit_field_discovery.py'in x for cmd in calls for x in cmd),'SECOND_TASK_T0_MUST_FOLLOW_COMPLETE_REPEAT'
finally:engine.O,engine.unchanged=saved;engine.subprocess.Popen=original_process;(R/'REVIEW_PENDING').write_bytes(guard)
assert not(R/'runs/v842_staged_long_navigation/development12').exists()
for p in C.glob('*.py'):ast.parse(p.read_text())
original=read(R/'experiments/staged_audit_completion_20261106/DEVELOPMENT_FREEZE.json');assert all(sha(R/p)==h for p,h in original['files'].items())
authorization=dict(user_instruction='下一步开始',operation='One OS identity startup continuation, frozen scientific engine unchanged',prior_startup_failed_before_any_model=True,original_claim=str(Path('runs/staged_audit_completion_20261106/DEVELOPMENT12_WINDOW_CLAIM.json')),absolute_deadline_unix=claim['absolute_deadline_unix'],deadline_reset=False,scientific_revisions=0,new_navigation_max=3,new_pilot_main=0,new24=0,training=0,network=0,Stage=0,no_further_repairs=True)
dump(ROOT/'AUTHORIZATION.json',authorization);dump(ROOT/'QUALIFICATION.json',dict(passed=True,identity_cases=records,actual_frozen_engine_preflight_to_first_navigation_boundary=True,no_new_models=True,no_new_integrations=True,review_pending_restored=True))
files={str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()};files.update({str((ROOT/n).relative_to(R)):sha(ROOT/n)for n in ['AUTHORIZATION.json','QUALIFICATION.json']});files[str(Path('experiments/staged_audit_completion_20261106/DEVELOPMENT_FREEZE.json'))]=sha(R/'experiments/staged_audit_completion_20261106/DEVELOPMENT_FREEZE.json');files[str(Path('runs/staged_audit_completion_20261106/DEVELOPMENT12_WINDOW_CLAIM.json'))]=sha(R/'runs/staged_audit_completion_20261106/DEVELOPMENT12_WINDOW_CLAIM.json')
dump(C/'OPERATIONS_FREEZE.json',dict(files=files,frozen_unix=time.time(),root_deadline_unchanged=claim['absolute_deadline_unix']));print(json.dumps(dict(passed=True,identity_cases=3,dry_engine=True,models=0,integrations=0,deadline=claim['absolute_deadline_unix'])))
