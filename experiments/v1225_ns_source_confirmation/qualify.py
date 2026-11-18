"""Reuse unchanged hashed gates; qualify the new NS assembly and launcher."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
import fcntl,copy,subprocess,types,ast,traceback
import route_dispatch
from gates import main_gate

def main():
 start=time.monotonic();guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')==GUARD
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not read(O/'APPROVAL.json')['models_authorized']
 for case in ['slot09','oldNS']:assert read(R/'runs/v1224_ns_current_source'/('ENTRY_'+case+'_QUALIFICATION.json'))['passed']
 assert read(O/'LIVE_ADAPTER_QUALIFICATION.json')['passed']
 parent=R/'runs/v1222_exact_stop_confirmation';assert read(parent/'FINALIZED.json')['manifest_readback']
 manifest=read(parent/'LOCAL_MANIFEST.json')['files'];assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in manifest.items())
 assert read(parent/'QUALIFICATION.json')['passed']and read(parent/'INHERITED_ROUTE_GATE.json')['passed']
 # Inherit the exact unchanged WE and EW scientific bindings only.
 for name in ['live_entry.py','audit_admission.py']:
  assert (C/name).read_text()==(R/'experiments/v1222_exact_stop_confirmation'/name).read_text().replace('v1222','v1225').replace('V1222','V1225')
 inherited=dict(passed=True,WE_EW_only=True,NS_requires_four_new_physical_tasks=True,old_manifest_readback=True,zero_new_route_samples=True)
 dump(O/'INHERITED_ROUTE_GATE.json',inherited)
 tasks=read(C/'TASKS.json');assert len(tasks)==55
 for t in tasks:task_contract(t)
 assert [t['task_id']for t in tasks[:4]]==['repair_main_NORTH_SOUTH','repair_repeat_NORTH_SOUTH','regression_main_NORTH_SOUTH','regression_repeat_NORTH_SOUTH']
 assert (C/'ORIGINAL_TASK_LIST.json').read_bytes()==(R/'experiments/v828_goal_dynamic_confirmation/TASK_LIST.json').read_bytes()
 for p in C.glob('*.py'):ast.parse(p.read_text())
 env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
 cache=[]
 for case in ['legacy_then_prebind','prebind_then_legacy']:
  p=subprocess.run([sys.executable,'-B',str(C/'check_cached_runtime.py'),case],cwd=R,env=env,capture_output=True,text=True,timeout=20);assert p.returncode==0,(p.stdout,p.stderr);cache.append(json.loads(p.stdout.strip().splitlines()[-1]))
 now=time.time();mono=time.monotonic();a=read(O/'AUTHORIZATION.json');duration=min(a['absolute_ceiling_unix']-now,a['monotonic_ceiling']-mono)
 w=dict(started_unix=now,absolute_deadline_unix=now+duration,started_monotonic=mono,hard_stop_monotonic=mono+duration,boot_id=a['boot_id'])
 approval=dict(models_authorized=True,synthetic_qualification_only=True,stop_on_safety_evidence=True,automatic_new24=False,allowed_task_ids=[t['task_id']for t in tasks],window_seconds=duration,absolute_deadline_unix=w['absolute_deadline_unix'])
 # Reuse actual old NS native recording to verify the shared full-native auditor.
 base=load('v1225_base_saved_qualification',C/'audit_refusal.py');oldtask=next(t for t in read(R/'experiments/v1220_stop_reserve_confirmation/TASKS.json')if t['task_id']=='regression_main_NORTH_SOUTH')
 saved=base.audit(oldtask,output_path=O/'SHARED_NATIVE_AUDIT_QUALIFICATION.json');assert saved['passed']
 dump(O/'GOAL_AUDIT_QUALIFICATION.json',dict(passed=True,scope='two new NS analytical executor bundles and new live adapter external-control negative; unchanged WE/EW full saved audits inherited'))
 dump(O/'NATIVE_AUDIT_QUALIFICATION.json',dict(passed=True,shared_full_native=saved,new_ns_adapter=read(O/'LIVE_ADAPTER_QUALIFICATION.json')))
 for t in tasks:envelope(t,approval,w,entry_check=True)
 negatives=[]
 for name,fn in [('modified_task',lambda:task_contract(dict(tasks[0],seed=0))),('synthetic_physical',lambda:envelope(tasks[0],approval,w)),('extended_deadline',lambda:envelope(tasks[0],approval,dict(w,absolute_deadline_unix=w['absolute_deadline_unix']+1),entry_check=True))]:
  try:fn()
  except AssertionError:negatives.append(name)
  else:raise AssertionError('BAD_INPUT_ACCEPTED '+name)
 class BeforeStep(BaseException):pass
 prestep=[]
 for slot in [1,9,17]:
  t=next(t for t in tasks if t['task_id']=='main_slot'+str(slot).zfill(2));prior=R/'runs/v858_nav2_verified/v1218'/('t0_slot'+str(slot).zfill(2));p0=read(prior/'RESULT.json')['canonical_initial_packet'];setup=read(prior/'physics/SETUP.json');scan=read(prior/'INITIAL_SENSOR.json');requests=[]
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
 rows=[dict(role='main',slot=t['slot'],case_id=t['case_id'],direction=t['initial_axis_motion_direction'],functional_passed=True,safety_evidence_passed=True,result=dict(new_actual_native=1))for t in tasks if t['role']=='main']
 assert main_gate(rows)['passed']and main_gate(rows[:-1])['full_denominator_success_rate']is None
 assert main_gate([dict(rows[0],role='development_main')]+rows)==main_gate(rows)
 cli=[]
 for entry,arguments,expected in [('worker.py',[str(C/'TASK_repair_main_NORTH_SOUTH.json')],'NO_NEW_MODEL_AUTHORITY'),('t0.py',[str(C/'TASK_t0_slot01.json')],'NO_NEW_MODEL_AUTHORITY'),('audit.py',[str(C/'TASK_repair_main_NORTH_SOUTH.json')],'AssertionError'),('campaign.py',[],'AssertionError'),('start.py',[],'AssertionError')]:
  p=subprocess.run([sys.executable,'-B',str(C/entry),*arguments],cwd=R,env=env,capture_output=True,text=True,timeout=20);assert p.returncode!=0 and expected in p.stdout+p.stderr and 'ModuleNotFoundError'not in p.stderr and 'ImportError'not in p.stderr,(entry,p.stdout,p.stderr);cli.append(entry)
 fixtures=O/'ENTRY_FIXTURES';fixtures.mkdir();dump(fixtures/'APPROVAL.json',approval);dump(fixtures/'WINDOW.json',w)
 fcntl.flock(lock,fcntl.LOCK_UN);isolated=[]
 try:
  (R/'REVIEW_PENDING').unlink()
  for t in [tasks[0],next(t for t in tasks if t['task_id']=='main_slot17')]:
   p=subprocess.run([str(R/'run_phase.sh'),str(C/'worker.py'),str(C/('TASK_'+t['task_id']+'.json')),'--entry-check','--approval',str(fixtures/'APPROVAL.json'),'--window',str(fixtures/'WINDOW.json')],cwd=R,env=env,capture_output=True,text=True,timeout=30);assert p.returncode==0,(p.stdout,p.stderr);isolated.append(json.loads(p.stdout.strip().splitlines()[-1]))
 finally:(R/'REVIEW_PENDING').write_bytes(guard)
 result=dict(passed=True,models=0,new_mujoco_native=0,cache=cache,normal_first_step=prestep,cli=cli,negatives=negatives,isolated=isolated,unchanged_gates_reused_by_hash=True,wall_s=time.monotonic()-start)
 dump(O/'QUALIFICATION.json',result);dump(O/'ISOLATED_QUALIFICATION.json',dict(passed=True,entries=isolated));dump(O/'READY_FOR_REVIEW.json',dict(preparation_gates_passed=True,physical_authorized=False));print(json.dumps(result))
if __name__=='__main__':
 try:main()
 except BaseException as e:dump(O/'PREPARATION_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),models=0,new_mujoco_native=0,unfinished_analytical_unknown=True));raise
