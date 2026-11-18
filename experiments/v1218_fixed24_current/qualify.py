"""Actual fixed-pool entry tests with all vehicle/model imports forbidden."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODEL_QUALIFICATION '+name)
sys.meta_path.insert(0,NoModels())
from worker_context import *
import ast,copy,subprocess,fcntl,types,traceback
import route_dispatch
from gates import main_gate,final_gate

def main():
 assert not read(O/'APPROVAL.json')['models_authorized'] and not(O/'QUALIFICATION.json').exists()
 start=time.monotonic();guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 parent=R/'runs/v1217_private_three_route';assert read(parent/'FINALIZED.json')['same_version_three_routes_passed']
 manifest=read(parent/'LOCAL_MANIFEST.json')['files'];assert all(sha(R/n)==v['sha256'] and (R/n).stat().st_size==v['bytes'] for n,v in manifest.items())
 for p in (C/'goal_package').glob('*.py'):assert p.read_bytes()==(R/'experiments/v1217_private_three_route/goal_package'/p.name).read_bytes()
 for name in ['live_entry.py','native_audit.py','audit_admission.py','route_dispatch.py']:
  old=(R/'experiments/v1217_private_three_route'/name).read_text().replace('v1217','v1218').replace('V1217','V1218')
  assert old==(C/name).read_text(),name
 assert read(O/'CACHED_RUNTIME_QUALIFICATION.json')['passed']
 auth=read(O/'AUTHORIZATION.json');assert sha(C/'ORIGINAL_TASK_LIST.json')==sha(R/'experiments/v828_goal_dynamic_confirmation/TASK_LIST.json')==auth['original_pool_sha256']
 pool=read(C/'ORIGINAL_TASK_LIST.json');tasks=read(C/'TASKS.json');assert len(tasks)==51 and [t['role']for t in tasks]==['t0']*24+['main']*24+['repeat']*3
 assert [t['seed']for t in pool]==list(range(10060001,10060025))and[t['slot']for t in pool]==list(range(1,25))
 assert all(sum(t['case_id']==c for t in pool)==8 for c in ['WEST_EAST','NORTH_SOUTH','EAST_WEST'])and all(sum(t['initial_axis_motion_direction']==d for t in pool)==12 for d in ['POSITIVE_AXIS','NEGATIVE_AXIS'])
 for t in tasks:task_contract(t)
 negatives=[]
 def reject(label,fn):
  try:fn()
  except AssertionError:negatives.append(label)
  else:raise AssertionError('NEGATIVE_ACCEPTED '+label)
 for k,v in [('seed',10010001),('phase',0.),('scope','new_pool'),('historical_prefix_native',1),('native_limit',85000),('output',str(RAW/'wrong'))]:reject(k,lambda k=k,v=v:task_contract(dict(tasks[0],**{k:v})))
 starter=load('v1218_start_qualification',C/'start.py');assert starter.validate_authorization(auth)==10800
 for k,v in [('authorized',False),('window_seconds',10800.),('window_seconds',43200),('temporary_bytes',8*1024**3),('repeat_slots',[2,9,17]),('scientific_revisions',1)]:reject('auth_'+k,lambda k=k,v=v:starter.validate_authorization(dict(auth,**{k:v})))
 rows=[dict(role='main',slot=t['slot'],case_id=t['case_id'],direction=t['initial_axis_motion_direction'],functional_passed=True,safety_evidence_passed=True,result=dict(new_actual_native=1))for t in pool]
 assert main_gate(rows)['passed']
 for index in range(24):
  one=copy.deepcopy(rows);one[index]['functional_passed']=False;assert main_gate(one)['passed']
  one[(index+1)%24]['functional_passed']=False;assert not main_gate(one)['passed']
 assert main_gate(rows[:-1])['full_denominator_success_rate']is None
 zero=copy.deepcopy(rows);zero[-1]['result']['new_actual_native']=0;assert not main_gate(zero)['full24_executed']
 bad=copy.deepcopy(rows);bad[0]['safety_evidence_passed']=False;assert not main_gate(bad)['passed']
 repeats=[dict(rows[s-1],role='repeat')for s in [1,9,17]];pairs={str(s):dict(passed=True)for s in [1,9,17]};assert final_gate(rows+repeats,pairs)
 for slot in pairs:
  bad=copy.deepcopy(pairs);bad[slot]['passed']=False;assert not final_gate(rows+repeats,bad)
 assert not final_gate(rows,pairs)
 now=time.time();mono=time.monotonic();window=dict(started_unix=now,absolute_deadline_unix=now+10800,started_monotonic=mono,hard_stop_monotonic=mono+10800,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 assert remaining(window)>10700 and remaining(dict(window,absolute_deadline_unix=now-1,started_unix=now-10801))<0 and remaining(dict(window,hard_stop_monotonic=mono-1,started_monotonic=mono-10801))<0
 approval=dict(models_authorized=True,synthetic_qualification_only=True,stop_on_safety_evidence=True,automatic_new24=False,allowed_task_ids=[t['task_id']for t in tasks],window_seconds=10800,absolute_deadline_unix=window['absolute_deadline_unix'])
 for t in tasks[24:]:assert envelope(t,approval,window,entry_check=True)
 reject('synthetic_cannot_run_physics',lambda:envelope(tasks[24],approval,window))
 reject('wrong_deadline',lambda:envelope(tasks[24],dict(approval,absolute_deadline_unix=now+10801),window,entry_check=True))
 old=science();np=old.np
 # Every original phase/seed uses its real saved t0 sensor packet from V1185.
 # These are saved-state software views, never claimed new actual MJB checks.
 t0audit=load('v1218_t0_saved_audit',C/'t0_audit.py');checks=[];cpp=py=0
 class BeforeStep(BaseException):pass
 for t in tasks[:24]:
  prior=R/'runs/v858_nav2_verified/v1185'/t['task_id'];p0=read(prior/'RESULT.json')['canonical_initial_packet'];setup=read(prior/'physics/SETUP.json');scan=read(prior/'INITIAL_SENSOR.json')
  assert setup['seed']==t['seed'] and setup['actor']['phase_rad']==t['phase'] and p0['sim_time']==0. and scan['time']==0.
  target=O/('T0_SAVED_'+str(t['slot']).zfill(2));target.mkdir()
  proof=t0audit.audit(dict(t,output=str(prior)),output_path=target/'AUDIT.json');assert proof['passed']
  worker=configure_owner(O,time.time()+300,window);requests=[]
  class Interface:
   count=0;d=types.SimpleNamespace(time=0.)
   adapter=types.SimpleNamespace(last=np.asarray(p0['controller_memory']['last_ctrl']),integral=p0['controller_memory']['integral'])
   def body(self):return p0['body']
   def steering_sample(self):return np.asarray(p0['steering']['position']+p0['steering']['velocity'])
   def scan(self):return copy.deepcopy(scan)
   def step(self,*row):requests.append(row);raise BeforeStep()
  main_task=next(x for x in tasks if x['role']=='main' and x['slot']==t['slot'])
  try:worker.navigate(Interface(),setup,main_task,time.time()+300,target,{})
  except BeforeStep:pass
  else:raise AssertionError('NORMAL_FIRST_STEP_NOT_REACHED '+t['task_id'])
  plan=read(target/'00_STATIC_00_PLAN.json');assert len(requests)==1 and plan['passed'] and all(plan['checks'].values())
  cpp+=4405;py+=len(plan['planned_body_requests']);checks.append(dict(slot=t['slot'],seed=t['seed'],phase=t['phase'],first_request=requests[0],saved_actual_t0_audited=True,new_actual_model=False))
 # Full refusal safety auditor on a preserved successful trace, then ctrl tamper rejection.
 safety=load('v1218_saved_refusal_safety',C/'audit_refusal.py');fixture=read(R/'experiments/v1217_private_three_route/TASK_main_NORTH_SOUTH.json');r=read(Path(fixture['output'])/'RESULT.json')
 view=dict(r,passed=False,functional_failure=dict(reason='SYNTHETIC_ONLY'))
 proof=safety.audit(fixture,result_override=view,output_path=O/'REFUSAL_SAFETY_QUALIFICATION.json');assert proof['passed']and not proof['functional_passed']
 saved=safety.read
 def tamper(p):
  d=saved(p)
  if Path(p).name=='BODY_COMMANDS.json':d=copy.deepcopy(d);d[0][1]+=.01
  return d
 safety.read=tamper
 try:reject('control_tamper',lambda:safety.audit(fixture,result_override=view,output_path=O/'FORBIDDEN_TAMPER.json'))
 finally:safety.read=saved
 for p in C.rglob('*.py'):ast.parse(p.read_text())
 # Exact launch environment; denied actual CLI paths must stop before any model.
 env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),PYOPENGL_PLATFORM='osmesa',MUJOCO_GL='osmesa',CUDA_VISIBLE_DEVICES='')
 cli=[]
 for name,args,expect in [('worker.py',[str(C/'TASK_main_slot01.json')],'NO_NEW_MODEL_AUTHORITY'),('t0.py',[str(C/'TASK_t0_slot01.json')],'NO_NEW_MODEL_AUTHORITY'),('audit.py',[str(C/'TASK_main_slot01.json')],'AssertionError')]:
  p=subprocess.run([sys.executable,'-B',str(C/name),*args],cwd=R,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
  assert p.returncode!=0 and expect in p.stdout+p.stderr and 'ModuleNotFoundError'not in p.stderr and 'ImportError'not in p.stderr,(name,p.stdout,p.stderr)
  cli.append(dict(entry=name,expected_refusal=expect,returncode=p.returncode))
 fixture=O/'ENTRY_FIXTURES';fixture.mkdir();dump(fixture/'APPROVAL.json',approval);dump(fixture/'WINDOW.json',window)
 isolated=[]
 fcntl.flock(lock,fcntl.LOCK_UN)
 try:
  (R/'REVIEW_PENDING').unlink()
  for slot in [1,9,17]:
   p=subprocess.run([str(R/'run_phase.sh'),str(C/'worker.py'),str(C/('TASK_main_slot'+str(slot).zfill(2)+'.json')),'--entry-check','--approval',str(fixture/'APPROVAL.json'),'--window',str(fixture/'WINDOW.json')],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30)
   # Parent lock released only for the subprocess entry check below.
   assert p.returncode==0,(slot,p.stdout,p.stderr)
   isolated.append(json.loads(p.stdout.strip().splitlines()[-1]))
 finally:(R/'REVIEW_PENDING').write_bytes(guard)
 result=dict(passed=True,parent_six_audits_and_manifest_verified=True,scientific_package_byte_identical=True,original_pool_sha_unchanged=True,registered_jobs=51,all24_saved_initial_phase_interfaces=checks,negatives=negatives,full_cli=cli,isolated_entries=isolated,models=0,new_mujoco_native=0,analytical_cpp_native=cpp,analytical_python_native=py,saved_safety_native_reviewed=proof['native_reviewed'],wall_s=time.monotonic()-start)
 dump(O/'QUALIFICATION.json',result);dump(O/'ISOLATED_QUALIFICATION.json',dict(passed=True,entries=isolated,models=0,new_mujoco_native=0));dump(O/'READY_FOR_REVIEW.json',dict(preparation_gates_passed=True,physical_authorized=False));print(json.dumps(result))
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  p=O/'PREPARATION_ERRORS.json';a=read(p)if p.exists()else[];a.append(dict(error=repr(exc),traceback=traceback.format_exc(),models=0,new_mujoco_native=0,unfinished_analytical_count_unknown=True));dump(p,a);raise
