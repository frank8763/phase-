"""Only changed source/entry checks; inherit unchanged verified physics gates."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('QUALIFICATION_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
import ast,copy,types,subprocess,fcntl,traceback

def main():
 start=time.monotonic();guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')==GUARD
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not read(O/'APPROVAL.json')['models_authorized']and not(O/'ROUND_WINDOW.json').exists()
 source=R/'runs/v1241_fine_route_reconnection'
 saved={case:read(source/('QUALIFICATION_'+case+'.json'))for case in ['slot12','slot10','slot09','oldNS']}
 assert all(d['passed']for d in saved.values())and all(saved[c]['old_success_arrays_exact']for c in ['slot10','slot09','oldNS'])
 assert read(source/'BOUNDARY_QUALIFICATION.json')['passed']and read(source/'PROPOSAL_INDEPENDENT_AUDIT.json')['passed']
 live=read(O/'LIVE_ADAPTER_QUALIFICATION.json');assert live['passed']and live['negative_external_ctrl_rejected']
 tasks=read(C/'TASKS.json');assert len(tasks)==2 and [t['task_id']for t in tasks]==['slot12_main','slot12_repeat']
 for task in tasks:task_contract(task)
 for p in C.glob('*.py'):ast.parse(p.read_text())
 # Exercise exactly the real driver's metadata construction for both tasks.
 tree=ast.parse((C/'campaign.py').read_text());node=next(n for n in ast.walk(tree)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='row'for t in n.targets))
 code=compile(ast.Module(body=[node],type_ignores=[]),str(C/'campaign.py'),'exec')
 for task in tasks:
  scope={'task':task};exec(code,scope);assert scope['row']['slot']==12
 env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
 cached=[]
 for order in ['legacy_then_prebind','prebind_then_legacy']:
  p=subprocess.run([sys.executable,'-B',str(C/'check_cached_runtime.py'),order],cwd=R,env=env,capture_output=True,text=True,timeout=25);assert p.returncode==0,(p.stdout,p.stderr);cached.append(json.loads(p.stdout.strip().splitlines()[-1]))
 now=time.time();mono=time.monotonic();w=dict(started_unix=now,absolute_deadline_unix=now+5400,started_monotonic=mono,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 a=dict(models_authorized=True,synthetic_qualification_only=True,window_seconds=5400,absolute_deadline_unix=w['absolute_deadline_unix'],stop_on_safety_evidence=True,automatic_new24=False,allowed_task_ids=[t['task_id']for t in tasks])
 for t in tasks:envelope(t,a,w,entry_check=True)
 negative=[]
 for label,fn in [('wrong_seed',lambda:task_contract(dict(tasks[0],seed=0))),('wrong_phase',lambda:task_contract(dict(tasks[0],phase=0.))),('synthetic_physical',lambda:envelope(tasks[0],a,w)),('extended_root',lambda:envelope(tasks[0],a,dict(w,absolute_deadline_unix=w['absolute_deadline_unix']+1),entry_check=True))]:
  try:fn()
  except AssertionError:negative.append(label)
  else:raise AssertionError('BAD_ENTRY_ACCEPTED '+label)
 class FirstStep(BaseException):pass
 prior=R/'runs/v858_nav2_verified/v1237/t0_slot12';p0=read(prior/'RESULT.json')['canonical_initial_packet'];setup=read(prior/'physics/SETUP.json');scan=read(prior/'INITIAL_SENSOR.json');requests=[]
 class Interface:
  count=0;d=types.SimpleNamespace(time=0.);adapter=types.SimpleNamespace(last=np.array(p0['controller_memory']['last_ctrl']),integral=p0['controller_memory']['integral'])
  def body(self):return p0['body']
  def steering_sample(self):return np.array(p0['steering']['position']+p0['steering']['velocity'])
  def scan(self):return copy.deepcopy(scan)
  def step(self,*a):requests.append(a);raise FirstStep()
 out=O/'PRESTEP';out.mkdir();owner=configure_owner(O,time.time()+300,w)
 try:owner.navigate(Interface(),setup,tasks[0],time.time()+300,out,{})
 except FirstStep:pass
 else:raise AssertionError('NORMAL_FIRST_STEP_NOT_REACHED')
 assert len(requests)==1 and read(out/'00_STATIC_00_PLAN.json')['passed']
 cli=[]
 for entry,args in [('worker.py',[str(C/'TASK_slot12_main.json')]),('audit.py',[str(C/'TASK_slot12_main.json')]),('campaign.py',[]),('start.py',[])]:
  p=subprocess.run([sys.executable,'-B',str(C/entry),*args],cwd=R,env=env,capture_output=True,text=True,timeout=25);assert p.returncode!=0 and 'ModuleNotFoundError'not in p.stderr and 'ImportError'not in p.stderr,(entry,p.stdout,p.stderr);cli.append(entry)
 fixtures=O/'ENTRY_FIXTURES';fixtures.mkdir();dump(fixtures/'APPROVAL.json',a);dump(fixtures/'WINDOW.json',w);fcntl.flock(lock,fcntl.LOCK_UN);isolated=[]
 try:
  (R/'REVIEW_PENDING').unlink()
  for task in tasks:
   p=subprocess.run([str(R/'run_phase.sh'),str(C/'worker.py'),str(C/('TASK_'+task['task_id']+'.json')),'--entry-check','--approval',str(fixtures/'APPROVAL.json'),'--window',str(fixtures/'WINDOW.json')],cwd=R,env=env,capture_output=True,text=True,timeout=30);assert p.returncode==0,(p.stdout,p.stderr);isolated.append(json.loads(p.stdout.strip().splitlines()[-1]))
 finally:(R/'REVIEW_PENDING').write_bytes(guard)
 result=dict(passed=True,models=0,physical_native=0,full_live_adapter_passed=True,saved_case_qualifications=list(saved),old_three_success_arrays_exact=True,real_driver_rows=2,negative_contexts=negative,cache=cached,normal_first_step=requests[0],CLI_disabled=cli,isolated_worker_entry_checks=isolated,wall_s=time.monotonic()-start)
 dump(O/'QUALIFICATION.json',result);dump(O/'ISOLATED_QUALIFICATION.json',dict(passed=True,entries=isolated));dump(O/'READY_FOR_REVIEW.json',dict(preparation_gates_passed=True,models_authorized=False));print(json.dumps(result))
if __name__=='__main__':
 try:main()
 except BaseException as exc:dump(O/'PREPARATION_ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),models=0,physical_native=0));raise
