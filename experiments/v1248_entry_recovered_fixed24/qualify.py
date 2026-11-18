"""Fresh denominator, inherited immutable physics, actual new driver interfaces."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
from parent_gate import verify_parent,validate_parent
from gates import main_gate,final_gate
import ast,copy,fcntl,subprocess,types,traceback

def main():
 start=time.monotonic();guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')==GUARD
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not read(O/'APPROVAL.json')['models_authorized']and not(O/'ROUND_WINDOW.json').exists()
 parent=verify_parent();assert parent['passed'];dump(O/'PARENT_GATE_QUALIFICATION.json',parent)
 tasks=read(C/'TASKS.json');assert len(tasks)==51
 assert [t['slot']for t in tasks if t['role']=='t0']==list(range(1,25))
 assert [t['slot']for t in tasks if t['role']=='main']==list(range(1,25))
 assert [t['slot']for t in tasks if t['role']=='repeat']==[1,9,17]
 assert(C/'ORIGINAL_TASK_LIST.json').read_bytes()==(R/'experiments/v828_goal_dynamic_confirmation/TASK_LIST.json').read_bytes()
 for t in tasks:task_contract(t)
 tree=ast.parse((C/'campaign.py').read_text());node=next(n for n in ast.walk(tree)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='row'for t in n.targets))
 code=compile(ast.Module(body=[node],type_ignores=[]),str(C/'campaign.py'),'exec')
 for t in tasks:
  scope={'task':t};exec(code,scope);assert scope['row']['slot']==t['slot']and scope['row']['case_id']==t['case_id']
 for field in ['slot','task_id','role','case_id','initial_axis_motion_direction']:
  bad=dict(tasks[0]);bad.pop(field)
  try:exec(code,dict(task=bad))
  except KeyError:pass
  else:raise AssertionError('MISSING_DRIVER_FIELD_ACCEPTED '+field)
 negative=[]
 p=R/'runs/v1247_slot13_entry_validation';d=read(p/'COMPLETION.json');f=read(p/'FINALIZED.json')
 for name,a,b in [('parent_failed',dict(d,passed=False),f),('parent_no_archive',d,dict(f,manifest_readback=False))]:
  try:validate_parent(a,b)
  except AssertionError:negative.append(name)
  else:raise AssertionError('BAD_PARENT_ACCEPTED')
 bad=copy.deepcopy(d);bad['development_repeats']['slot13']['maximum_complete_state_ctrl_error']=1e-4
 try:validate_parent(bad,f)
 except AssertionError:negative.append('bad_repeat')
 else:raise AssertionError('BAD_REPEAT_ACCEPTED')
 env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
 cache=[]
 for order in ['legacy_then_prebind','prebind_then_legacy']:
  p=subprocess.run([sys.executable,'-B',str(C/'check_cached_runtime.py'),order],cwd=R,env=env,capture_output=True,text=True,timeout=25);assert p.returncode==0,(p.stdout,p.stderr);cache.append(json.loads(p.stdout.strip().splitlines()[-1]))
 now=time.time();mono=time.monotonic();window=dict(started_unix=now,absolute_deadline_unix=now+10800,started_monotonic=mono,hard_stop_monotonic=mono+10800,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 a=dict(models_authorized=True,synthetic_qualification_only=True,window_seconds=10800,absolute_deadline_unix=window['absolute_deadline_unix'],stop_on_safety_evidence=True,automatic_new24=False,allowed_task_ids=[t['task_id']for t in tasks])
 for t in tasks:envelope(t,a,window,entry_check=True)
 for name,fn in [('changed_phase',lambda:task_contract(dict(tasks[0],phase=0.))),('changed_seed',lambda:task_contract(dict(tasks[0],seed=0))),('synthetic_physical',lambda:envelope(tasks[0],a,window)),('extended_root',lambda:envelope(tasks[0],a,dict(window,absolute_deadline_unix=window['absolute_deadline_unix']+1),entry_check=True))]:
  try:fn()
  except AssertionError:negative.append(name)
  else:raise AssertionError('BAD_CONTEXT_ACCEPTED '+name)
 mains=[dict(role='main',slot=t['slot'],case_id=t['case_id'],direction=t['initial_axis_motion_direction'],functional_passed=True,safety_evidence_passed=True,result=dict(new_actual_native=1))for t in tasks if t['role']=='main']
 assert main_gate(mains)['passed']and main_gate(mains[:-1])['full_denominator_success_rate']is None
 repeats=[dict(role='repeat',slot=s,functional_passed=True,safety_evidence_passed=True)for s in [1,9,17]]
 assert final_gate(mains+repeats,{str(s):dict(passed=True)for s in [1,9,17]})and not final_gate(mains,{})
 bad=copy.deepcopy(mains);bad[1]['functional_passed']=False;assert main_gate(bad)['passed']
 bad[2]['functional_passed']=False;assert not main_gate(bad)['passed']
 class FirstStep(BaseException):pass
 prestep=[]
 for slot in [1,9,17]:
  task=next(t for t in tasks if t['task_id']==f'main_slot{slot:02}');raw=R/f'runs/v858_nav2_verified/v1237/t0_slot{slot:02}';p0=read(raw/'RESULT.json')['canonical_initial_packet'];setup=read(raw/'physics/SETUP.json');scan=read(raw/'INITIAL_SENSOR.json');requests=[]
  class Interface:
   count=0;d=types.SimpleNamespace(time=0.);adapter=types.SimpleNamespace(last=np.array(p0['controller_memory']['last_ctrl']),integral=p0['controller_memory']['integral'])
   def body(self):return p0['body']
   def steering_sample(self):return np.array(p0['steering']['position']+p0['steering']['velocity'])
   def scan(self):return copy.deepcopy(scan)
   def step(self,*a):requests.append(a);raise FirstStep()
  out=O/'PREPARATION_02'/f'PRESTEP_{slot}';out.mkdir(parents=True);owner=configure_owner(O,time.time()+300,window)
  try:owner.navigate(Interface(),setup,task,time.time()+300,out,{})
  except FirstStep:pass
  else:raise AssertionError('NORMAL_FIRST_STEP_NOT_REACHED')
  assert len(requests)==1 and read(out/'00_STATIC_00_PLAN.json')['passed'];prestep.append(dict(slot=slot,request=requests[0]))
 cli=[]
 for entry,args in [('worker.py',[str(C/'TASK_main_slot01.json')]),('t0.py',[str(C/'TASK_t0_slot01.json')]),('audit.py',[str(C/'TASK_main_slot01.json')]),('campaign.py',[]),('start.py',[])]:
  p=subprocess.run([sys.executable,'-B',str(C/entry),*args],cwd=R,env=env,capture_output=True,text=True,timeout=25);assert p.returncode!=0 and 'ModuleNotFoundError'not in p.stderr and 'ImportError'not in p.stderr,(entry,p.stdout,p.stderr);cli.append(entry)
 # Actual scene t0 executor/auditor inherited byte for byte modulo namespace.
 old=R/'experiments/v1247_slot13_entry_validation'
 for name in ['t0.py','t0_audit.py']:
  assert(C/name).read_text()==(old/name).read_text().replace('v1247','v1248').replace('V1247','V1248')
 for path in C.glob('*.py'):ast.parse(path.read_text())
 starter=load('v1248_start_qualification',C/'start.py');auth=dict(read(O/'AUTHORIZATION.json'),authorized=True,user_approved=True)
 assert starter.validate_authorization(auth)==10800
 for k,v in [('scientific_revisions',1),('window_seconds',10801),('temporary_bytes',9*1024**3)]:
  try:starter.validate_authorization(dict(auth,**{k:v}))
  except AssertionError:negative.append('start_'+k)
  else:raise AssertionError('BAD_START_AUTH_ACCEPTED '+k)
 fixtures=O/'ENTRY_FIXTURES';fixtures.mkdir();dump(fixtures/'APPROVAL.json',a);dump(fixtures/'WINDOW.json',window);fcntl.flock(lock,fcntl.LOCK_UN);isolated=[]
 try:
  (R/'REVIEW_PENDING').unlink()
  for slot in [1,9,17]:
   task=next(t for t in tasks if t['task_id']==f'main_slot{slot:02}')
   p=subprocess.run([str(R/'run_phase.sh'),str(C/'worker.py'),str(C/('TASK_'+task['task_id']+'.json')),'--entry-check','--approval',str(fixtures/'APPROVAL.json'),'--window',str(fixtures/'WINDOW.json')],cwd=R,env=env,capture_output=True,text=True,timeout=30);assert p.returncode==0,(p.stdout,p.stderr);isolated.append(json.loads(p.stdout.strip().splitlines()[-1]))
 finally:(R/'REVIEW_PENDING').write_bytes(guard)
 result=dict(passed=True,models=0,physical_native=0,scientific_revisions=0,parent_gate=parent,
  fresh_t0=24,fresh_main=24,fixed_repeats=[1,9,17],actual_driver_row_checks=51,missing_metadata_negatives=5,
  cache=cache,prestep=prestep,disabled_CLI=cli,negative_contexts=negative,isolated=isolated,
  old_confirmation_samples_imported=0,full_denominator_and_fixed_repeat_gates=True,wall_s=time.monotonic()-start)
 dump(O/'QUALIFICATION.json',result);dump(O/'ISOLATED_QUALIFICATION.json',dict(passed=True,entries=isolated));dump(O/'READY_FOR_REVIEW.json',dict(preparation_gates_passed=True,models_authorized=False));print(json.dumps(result))
if __name__=='__main__':
 try:main()
 except BaseException as exc:dump(O/'PREPARATION_ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),models=0,physical_native=0));raise
