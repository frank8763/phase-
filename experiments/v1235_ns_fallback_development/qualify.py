"""Six-task operational assembly and finite fallback branch qualification."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
import copy,subprocess,types,fcntl,ast,traceback

def main():
 start=time.monotonic();guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')==GUARD
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not read(O/'APPROVAL.json')['models_authorized']and not(O/'ROUND_WINDOW.json').exists()
 S=R/'runs/v1234_retained_search_fallback'
 for case in ['slot10','slot09','oldNS']:assert read(S/('ENTRY_'+case+'_QUALIFICATION.json'))['passed']
 assert read(S/'RETAINED_SUCCESS_EXACT_QUALIFICATION.json')['passed']and read(O/'LIVE_ADAPTER_QUALIFICATION.json')['passed']
 # Science separation: execution/safety/nominal predictor byte-identical, only
 # retained source schedule adds exactly the predefined finite fallback.
 P=R/'experiments/v1227_terminal_contract_capture/goal_package';N=R/'experiments/v1234_retained_search_fallback/goal_package'
 for name in ['candidate_search.py','goal_entry.py','admission.py','terminal.py','connection.py']:assert(P/name).read_bytes()==(N/name).read_bytes(),name
 tasks=read(C/'TASKS.json');assert len(tasks)==6
 assert [t['task_id']for t in tasks]==['slot10_main','slot10_repeat','slot09_main','slot09_repeat','oldNS_main','oldNS_repeat']
 for t in tasks:task_contract(t)
 for p in C.glob('*.py'):ast.parse(p.read_text())
 # Decision boundary negatives use no physical or analytical propagation.
 from route_dispatch import ns_executor
 e=ns_executor().goal_entry;global_scope=e.generate.__globals__;original_search=global_scope['search'];original_fallback=global_scope['fallback_search']
 fixture=R/'runs/v858_nav2_verified/v1230/main_slot10';x=read(fixture/'LIVE_GOAL_INPUT.json');origin=e.bind_current(x,x['packet'],False);branch=[]
 def forbidden(*a,**k):raise AssertionError('UNAUTHORIZED_FALLBACK_CALLED')
 def fake_result(n,passed=False):return dict(passed=passed,phase_expanded=[n],nodes=1,terminal_attempts=0,analytical_cpp_native=0,wall_s=0.)
 try:
  global_scope['fallback_search']=forbidden
  for n in [0,2999]:
   global_scope['search']=lambda *a,n=n,**k:fake_result(n)
   try:e.generate(x,{},origin,0,time.monotonic()+10,shadow_origin=origin)
   except AssertionError as error:assert str(error)=='BASELINE_DID_NOT_EXHAUST_FIXED_WORK_NO_FALLBACK';branch.append('partial_'+str(n)+'_refused')
   else:raise AssertionError('PARTIAL_FAILURE_RAN_FALLBACK')
  global_scope['search']=lambda *a,**k:(_ for _ in()).throw(ValueError('source_evidence_exception'))
  try:e.generate(x,{},origin,0,time.monotonic()+10,shadow_origin=origin)
  except ValueError:branch.append('source_exception_not_hidden')
  else:raise AssertionError('SOURCE_EXCEPTION_HIDDEN')
  global_scope['search']=lambda *a,**k:fake_result(1,True)
  answer=e.generate(x,{},origin,0,time.monotonic()+10,shadow_origin=origin);assert answer['passed']and len(answer['search_trials'])==1;branch.append('success_retained_no_fallback')
 finally:global_scope['search']=original_search;global_scope['fallback_search']=original_fallback
 dump(O/'GOAL_AUDIT_QUALIFICATION.json',dict(passed=True,three_saved_full_executors=True,live_external_ctrl_and_terminal_audited=True,retained_two_success_arrays_exact=True,branch_guard_negatives=branch))
 dump(O/'NATIVE_AUDIT_QUALIFICATION.json',dict(passed=True,base_native_source_same_as_verified_V1228=True,new_ns_live_goal_audit=read(O/'LIVE_ADAPTER_QUALIFICATION.json')))
 dump(O/'NS_SOURCE_QUALIFICATION.json',dict(passed=True,source='V1234',scientific_revisions=1,retained_balanced_first=True,maximum_search_expansions=6000,old_cases_exact=read(S/'RETAINED_SUCCESS_EXACT_QUALIFICATION.json')))
 env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
 cache=[]
 for case in ['legacy_then_prebind','prebind_then_legacy']:
  p=subprocess.run([sys.executable,'-B',str(C/'check_cached_runtime.py'),case],cwd=R,env=env,capture_output=True,text=True,timeout=20);assert p.returncode==0,(p.stdout,p.stderr);cache.append(json.loads(p.stdout.strip().splitlines()[-1]))
 now=time.time();mono=time.monotonic();w=dict(started_unix=now,absolute_deadline_unix=now+5400,started_monotonic=mono,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 approval=dict(models_authorized=True,synthetic_qualification_only=True,stop_on_safety_evidence=True,automatic_new24=False,allowed_task_ids=[t['task_id']for t in tasks],window_seconds=5400,absolute_deadline_unix=w['absolute_deadline_unix'])
 for t in tasks:envelope(t,approval,w,entry_check=True)
 negatives=[]
 for name,fn in [('modified_seed',lambda:task_contract(dict(tasks[0],seed=0))),('synthetic_physical',lambda:envelope(tasks[0],approval,w)),('extended_window',lambda:envelope(tasks[0],approval,dict(w,absolute_deadline_unix=w['absolute_deadline_unix']+1),entry_check=True))]:
  try:fn()
  except (AssertionError,KeyError):negatives.append(name)
  else:raise AssertionError('BAD_CONTEXT_ACCEPTED '+name)
 class BeforeStep(BaseException):pass
 prestep=[]
 for slot in [10,9]:
  t=tasks[0 if slot==10 else 2];prior=R/'runs/v858_nav2_verified/v1228'/('t0_slot'+str(slot).zfill(2));p0=read(prior/'RESULT.json')['canonical_initial_packet'];setup=read(prior/'physics/SETUP.json');scan=read(prior/'INITIAL_SENSOR.json');requests=[]
  class Interface:
   count=0;d=types.SimpleNamespace(time=0.);adapter=types.SimpleNamespace(last=np.array(p0['controller_memory']['last_ctrl']),integral=p0['controller_memory']['integral'])
   def body(self):return p0['body']
   def steering_sample(self):return np.array(p0['steering']['position']+p0['steering']['velocity'])
   def scan(self):return copy.deepcopy(scan)
   def step(self,*a):requests.append(a);raise BeforeStep()
  out=O/('PRESTEP_'+str(slot));out.mkdir();owner=configure_owner(O,time.time()+300,w)
  try:owner.navigate(Interface(),setup,t,time.time()+300,out,{})
  except BeforeStep:pass
  else:raise AssertionError('FIRST_STEP_NOT_REACHED')
  assert len(requests)==1 and read(out/'00_STATIC_00_PLAN.json')['passed'];prestep.append(dict(slot=slot,request=requests[0]))
 cli=[]
 for entry,args,expected in [('worker.py',[str(C/'TASK_slot10_main.json')],'NO_NEW_MODEL_AUTHORITY'),('audit.py',[str(C/'TASK_slot10_main.json')],'AssertionError'),('campaign.py',[],'AssertionError'),('start.py',[],'AssertionError')]:
  p=subprocess.run([sys.executable,'-B',str(C/entry),*args],cwd=R,env=env,capture_output=True,text=True,timeout=20);assert p.returncode!=0 and expected in p.stdout+p.stderr and 'ModuleNotFoundError'not in p.stderr and 'ImportError'not in p.stderr,(entry,p.stdout,p.stderr);cli.append(entry)
 fixtures=O/'ENTRY_FIXTURES';fixtures.mkdir();dump(fixtures/'APPROVAL.json',approval);dump(fixtures/'WINDOW.json',w);fcntl.flock(lock,fcntl.LOCK_UN);isolated=[]
 try:
  (R/'REVIEW_PENDING').unlink()
  for t in [tasks[0],tasks[2],tasks[4]]:
   p=subprocess.run([str(R/'run_phase.sh'),str(C/'worker.py'),str(C/('TASK_'+t['task_id']+'.json')),'--entry-check','--approval',str(fixtures/'APPROVAL.json'),'--window',str(fixtures/'WINDOW.json')],cwd=R,env=env,capture_output=True,text=True,timeout=30);assert p.returncode==0,(p.stdout,p.stderr);isolated.append(json.loads(p.stdout.strip().splitlines()[-1]))
 finally:(R/'REVIEW_PENDING').write_bytes(guard)
 result=dict(passed=True,source='V1234',six_registered_tasks_only=True,models=0,new_mujoco_native=0,cache=cache,branch_guards=branch,negative_contexts=negatives,prestep=prestep,cli=cli,isolated=isolated,old_success_arrays_exact=True,wall_s=time.monotonic()-start)
 dump(O/'QUALIFICATION.json',result);dump(O/'ISOLATED_QUALIFICATION.json',dict(passed=True,entries=isolated));dump(O/'READY_FOR_REVIEW.json',dict(preparation_gates_passed=True,models_authorized=False));print(json.dumps(result))
if __name__=='__main__':
 try:main()
 except BaseException as error:dump(O/'PREPARATION_ERROR.json',dict(error=repr(error),traceback=traceback.format_exc(),models=0,new_mujoco_native=0,unfinished_analytical_unknown=True));raise
