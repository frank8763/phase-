"""Operational-only relay qualification. All physical/model imports blocked."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
from checkpoint import verify_checkpoint
from gates import main_gate,final_gate
import copy,subprocess,types,fcntl,ast,traceback

def main():
 start=time.monotonic();guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')==GUARD
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not read(O/'APPROVAL.json')['models_authorized']and not(O/'ROUND_WINDOW.json').exists()
 checkpoint=verify_checkpoint(require_remote=True)
 parent=R/'runs/v1228_terminal_reserve_confirmation';assert read(parent/'QUALIFICATION.json')['passed']and read(parent/'ISOLATED_QUALIFICATION.json')['passed']
 # Unchanged scientific adapters, all independent audits and worker per-native
 # statement bodies are text-identical after private namespace/output renaming.
 for name in ['live_entry.py','ns_live.py','ns_audit.py','audit_admission.py','ns_admission_audit.py','route_dispatch.py','native_audit.py','worker.py','audit_refusal.py']:
  assert (C/name).read_text()==(R/'experiments/v1228_terminal_reserve_confirmation'/name).read_text().replace('v1228','v1230').replace('V1228','V1230'),'SCIENCE_CHANGED '+name
 dump(O/'GOAL_AUDIT_QUALIFICATION.json',dict(passed=True,source_identical_parent='V1228',qualification_source_sha=sha(parent/'GOAL_AUDIT_QUALIFICATION.json'),no_repeated_science_work=True))
 dump(O/'NATIVE_AUDIT_QUALIFICATION.json',dict(passed=True,source_identical_parent='V1228',qualification_source_sha=sha(parent/'NATIVE_AUDIT_QUALIFICATION.json')))
 tasks=read(C/'TASKS.json');assert len(tasks)==21
 assert [t['slot']for t in tasks if t['role']=='main']==list(range(7,25))and [t['slot']for t in tasks if t['role']=='repeat']==[1,9,17]
 for t in tasks:task_contract(t)
 for p in C.glob('*.py'):ast.parse(p.read_text())
 env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
 cache=[]
 for case in ['legacy_then_prebind','prebind_then_legacy']:
  p=subprocess.run([sys.executable,'-B',str(C/'check_cached_runtime.py'),case],cwd=R,env=env,capture_output=True,text=True,timeout=20);assert p.returncode==0,(p.stdout,p.stderr);cache.append(json.loads(p.stdout.strip().splitlines()[-1]))
 now=time.time();mono=time.monotonic();w=dict(started_unix=now,absolute_deadline_unix=now+10800,started_monotonic=mono,hard_stop_monotonic=mono+10800,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 approval=dict(models_authorized=True,synthetic_qualification_only=True,stop_on_safety_evidence=True,automatic_new24=False,allowed_task_ids=[t['task_id']for t in tasks],window_seconds=10800,absolute_deadline_unix=w['absolute_deadline_unix'])
 for t in tasks:envelope(t,approval,w,entry_check=True)
 negative=[]
 for name,fn in [('changed_seed',lambda:task_contract(dict(tasks[0],seed=0))),('synthetic_physical',lambda:envelope(tasks[0],approval,w)),('extend_new_root',lambda:envelope(tasks[0],approval,dict(w,absolute_deadline_unix=w['absolute_deadline_unix']+1),entry_check=True))]:
  try:fn()
  except (AssertionError,KeyError):negative.append(name)
  else:raise AssertionError('BAD_INPUT_ACCEPTED '+name)
 # Combined unique24 denominator, no inherited dev or repeats in main denominator.
 imported=read(O/'CHECKPOINT_ROWS.json');newrows=[dict(role='main',slot=t['slot'],case_id=t['case_id'],direction=t['initial_axis_motion_direction'],functional_passed=True,safety_evidence_passed=True,result=dict(new_actual_native=1))for t in tasks if t['role']=='main']
 assert main_gate(imported)['successes']==6 and main_gate(imported)['full_denominator_success_rate']is None
 assert main_gate(imported+newrows)['passed']and main_gate(imported+newrows[:-1])['full_denominator_success_rate']is None
 try:main_gate(imported+newrows+[copy.deepcopy(newrows[0])])
 except AssertionError:negative.append('duplicate_slot')
 else:raise AssertionError('DUPLICATE_SLOT_ACCEPTED')
 assert not final_gate(imported+newrows,{})
 rrows=[dict(role='repeat',slot=s,functional_passed=True,safety_evidence_passed=True)for s in [1,9,17]]
 assert final_gate(imported+newrows+rrows,{str(s):dict(passed=True)for s in [1,9,17]})
 # Real retained parent baseline can be loaded by exact repeat checker, zero propagation.
 repeat_check=load('v1230_repeat_qualification',R/'experiments/v1180_fresh_recovery_chain/campaign.py').repeat_check
 baseline=R/'runs/v858_nav2_verified/v1228/main_slot01';pair=repeat_check(baseline,baseline);assert pair['passed']and pair['maximum_complete_state_ctrl_error']==0
 class BeforeStep(BaseException):pass
 prestep=[]
 for slot in [7,9,17]:
  t=next(t for t in tasks if t['task_id']=='main_slot'+str(slot).zfill(2));prior=R/'runs/v858_nav2_verified/v1228'/('t0_slot'+str(slot).zfill(2));p0=read(prior/'RESULT.json')['canonical_initial_packet'];setup=read(prior/'physics/SETUP.json');scan=read(prior/'INITIAL_SENSOR.json');requests=[]
  class Interface:
   count=0;d=types.SimpleNamespace(time=0.);adapter=types.SimpleNamespace(last=np.array(p0['controller_memory']['last_ctrl']),integral=p0['controller_memory']['integral'])
   def body(self):return p0['body']
   def steering_sample(self):return np.array(p0['steering']['position']+p0['steering']['velocity'])
   def scan(self):return copy.deepcopy(scan)
   def step(self,*r):requests.append(r);raise BeforeStep()
  out=O/('PRESTEP_'+str(slot));out.mkdir();owner=configure_owner(O,time.time()+300,w)
  try:owner.navigate(Interface(),setup,t,time.time()+300,out,{})
  except BeforeStep:pass
  else:raise AssertionError('FIRST_STEP_NOT_REACHED')
  plan=read(out/'00_STATIC_00_PLAN.json');assert plan['passed']and all(plan['checks'].values())and len(requests)==1;prestep.append(dict(slot=slot,request=requests[0]))
 cli=[]
 for entry,args,expected in [('worker.py',[str(C/'TASK_main_slot07.json')],'NO_NEW_MODEL_AUTHORITY'),('audit.py',[str(C/'TASK_main_slot07.json')],'AssertionError'),('campaign.py',[],'AssertionError'),('start.py',[],'AssertionError')]:
  p=subprocess.run([sys.executable,'-B',str(C/entry),*args],cwd=R,env=env,capture_output=True,text=True,timeout=20);assert p.returncode!=0 and expected in p.stdout+p.stderr and 'ModuleNotFoundError'not in p.stderr and 'ImportError'not in p.stderr,(entry,p.stdout,p.stderr);cli.append(entry)
 fixtures=O/'ENTRY_FIXTURES';fixtures.mkdir();dump(fixtures/'APPROVAL.json',approval);dump(fixtures/'WINDOW.json',w);fcntl.flock(lock,fcntl.LOCK_UN);isolated=[]
 try:
  (R/'REVIEW_PENDING').unlink()
  for task in [tasks[0],next(t for t in tasks if t['task_id']=='main_slot09'),next(t for t in tasks if t['task_id']=='main_slot17')]:
   p=subprocess.run([str(R/'run_phase.sh'),str(C/'worker.py'),str(C/('TASK_'+task['task_id']+'.json')),'--entry-check','--approval',str(fixtures/'APPROVAL.json'),'--window',str(fixtures/'WINDOW.json')],cwd=R,env=env,capture_output=True,text=True,timeout=30);assert p.returncode==0,(p.stdout,p.stderr);isolated.append(json.loads(p.stdout.strip().splitlines()[-1]))
 finally:(R/'REVIEW_PENDING').write_bytes(guard)
 result=dict(passed=True,operational_only=True,scientific_revisions=0,checkpoint=checkpoint,cache=cache,negative=negative,firststep=prestep,cli=cli,isolated=isolated,repeat1_parent_baseline_readable=True,pair_self_qualification=pair,models=0,new_mujoco_native=0,wall_s=time.monotonic()-start)
 dump(O/'QUALIFICATION.json',result);dump(O/'ISOLATED_QUALIFICATION.json',dict(passed=True,entries=isolated));dump(O/'READY_FOR_REVIEW.json',dict(preparation_gates_passed=True,physical_authorized=False));print(json.dumps(result))
if __name__=='__main__':
 try:main()
 except BaseException as e:dump(O/'PREPARATION_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),models=0,new_mujoco_native=0,unfinished_analytical_unknown=True));raise
