"""Zero-model full runtime and independent saved-proof qualification."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from worker_context import *
import copy,subprocess,fcntl,types,ast,traceback
import route_dispatch
from gates import main_gate,final_gate

def main():
 assert read(R/'runs/v1221_exact_stop_pruning/CACHE_COMPLETE_QUALIFICATION.json')['passed']and read(R/'runs/v1221_exact_stop_pruning/CACHE_DOMAIN_QUALIFICATION.json')['passed']
 assert not(O/'QUALIFICATION.json').exists() and not read(O/'APPROVAL.json')['models_authorized']
 start=time.monotonic();guard=(R/'REVIEW_PENDING').read_bytes();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 for n in ['QUALIFIED_slot02/RESULT.json','QUALIFIED_slot01/RESULT.json','QUALIFIED_slot03/RESULT.json']:assert read(R/'runs/v1221_exact_stop_pruning'/n)['passed']
 tasks=read(C/'TASKS.json');assert len(tasks)==53 and [t['role']for t in tasks[:2]]==['development_main','development_repeat']
 for t in tasks:task_contract(t)
 assert [t['slot']for t in tasks if t['role']=='main']==list(range(1,25)) and [t['slot']for t in tasks if t['role']=='repeat']==[1,9,17]
 assert (C/'ORIGINAL_TASK_LIST.json').read_bytes()==(R/'experiments/v828_goal_dynamic_confirmation/TASK_LIST.json').read_bytes()
 for p in C.glob('*.py'):ast.parse(p.read_text())
 env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),PYOPENGL_PLATFORM='osmesa',MUJOCO_GL='osmesa',CUDA_VISIBLE_DEVICES='')
 cache=[]
 for case in ['legacy_then_prebind','prebind_then_legacy']:
  p=subprocess.run([sys.executable,'-B',str(C/'check_cached_runtime.py'),case],cwd=R,env=env,capture_output=True,text=True,timeout=20);assert p.returncode==0,(p.stdout,p.stderr);cache.append(json.loads(p.stdout.strip().splitlines()[-1]))
 dump(O/'CACHED_RUNTIME_QUALIFICATION.json',dict(passed=True,checks=cache))
 # Independent reconstruction of finite choices and each bound, then every
 # full chosen stop. These fixtures contain no new or fabricated sensor data.
 auditor=load('v1222_full_selected_stop_audit',R/'experiments/v1219_stop_preserving_observer/audit_observer.py')
 selection_audit=load('v1222_independent_selection',R/'experiments/v1221_exact_stop_pruning/audit_selection.py')
 proofs=[]
 for case in ['slot02','slot01','slot03']:
  saved=R/'runs/v1221_exact_stop_pruning'/('QUALIFIED_'+case);chosen=read(saved/'RESULT.json')
  raw=R/'runs/v858_nav2_verified'/('v1220/main_slot02'if case=='slot02'else 'v1218/main_'+case)
  fixture=O/('SELECTOR_FIXTURE_'+case);fixture.mkdir()
  import shutil
  for target,source in [('LIVE_OBSERVER_INPUT.json',raw/'LIVE_OBSERVER_INPUT.json'),('LIVE_OBSERVER_TABLE.npz',raw/'LIVE_OBSERVER_TABLE.npz'),('LIVE_OBSERVER_REFERENCE.npz',saved/'REFERENCE.npz'),('LIVE_OBSERVER_SELECTION.json',saved/'RESULT.json')]:shutil.copyfile(source,fixture/target)
  x=read(fixture/'LIVE_OBSERVER_INPUT.json')
  with auditor.np.load(fixture/'LIVE_OBSERVER_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
  choice=selection_audit.verify(x,table,chosen,time.monotonic()+120);full=auditor.verify_selected(fixture,time.monotonic()+120)
  proofs.append(dict(case=case,selection=choice,complete_stop=full));dump(O/('SELECTOR_AUDIT_'+case+'.json'),proofs[-1])
 original_read=auditor.read
 def badread(p):
  d=original_read(p)
  if Path(p).name=='LIVE_OBSERVER_SELECTION.json':d=copy.deepcopy(d);d['complete_stop_qualification']['records'][0]['offset']+=1
  return d
 auditor.read=badread
 try:
  try:auditor.verify_selected(fixture,time.monotonic()+20)
  except AssertionError:pass
  else:raise AssertionError('BAD_STOP_RECORD_ACCEPTED')
 finally:auditor.read=original_read
 # A fabricated early elimination must not pass independent reconstruction.
 original_choice=read(O/'SELECTOR_FIXTURE_slot02/LIVE_OBSERVER_SELECTION.json');bad=copy.deepcopy(original_choice)
 index=next(i for i,t in enumerate(bad['trials'])if t.get('state_bound_witness')or t.get('pruning_witness')or t.get('endpoint_bound_witness')or t.get('common_origin_bound_m')is not None)
 if bad['trials'][index].get('common_origin_bound_m')is not None:bad['trials'][index]['common_origin_bound_m']-=.1
 elif bad['trials'][index].get('state_bound_witness'):bad['trials'][index]['state_bound_witness']['raw_m']-=.1
 elif bad['trials'][index].get('endpoint_bound_witness'):bad['trials'][index]['endpoint_bound_witness']['raw_m']-=.1
 else:bad['trials'][index]['pruning_witness']['current_raw']-=.1
 fx=O/'SELECTOR_FIXTURE_slot02';xx=read(fx/'LIVE_OBSERVER_INPUT.json')
 with auditor.np.load(fx/'LIVE_OBSERVER_TABLE.npz')as z:tt={k:z[k].copy()for k in z.files}
 try:selection_audit.verify(xx,tt,bad,time.monotonic()+120)
 except AssertionError:pass
 else:raise AssertionError('FABRICATED_PRUNING_WITNESS_ACCEPTED')
 # Preserve the independently audited same-science route gate; old raw proofs
 # and complete paired comparisons are verified rather than rerun as new data.
 oldrows=read(R/'runs/v1220_stop_reserve_confirmation/RESULTS.json');dev=[r for r in oldrows if r['role'].startswith('development_')];assert len(dev)==8 and all(r['functional_passed']and r['safety_evidence_passed']for r in dev)
 pairs=read(R/'runs/v1220_stop_reserve_confirmation/COMPLETION.json')['development_repeats'];assert len(pairs)==4 and all(p['passed']and p['maximum_complete_state_ctrl_error']<=1e-8 for p in pairs.values())
 manifest=read(R/'runs/v1220_stop_reserve_confirmation/LOCAL_MANIFEST.json')['files'];assert all(sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes']for n,v in manifest.items())
 # The complete live execution source differs only in explicit selector binding
 # and private module names. No physical command, goal or stop-policy edit.
 oldlive=(R/'experiments/v1219_stop_preserving_observer/live_entry.py').read_text().replace("_here/'candidate_observer.py'","R/'experiments/v1221_exact_stop_pruning/candidate_observer.py'").replace("_here/'stop_policy.py'","R/'experiments/v1219_stop_preserving_observer/stop_policy.py'").replace('phase_v1219','phase_v1222').replace('min(300.,end-time.time()-240)','min(600.,end-time.time()-240)')
 assert oldlive==(C/'live_entry.py').read_text()
 dump(O/'INHERITED_ROUTE_GATE.json',dict(passed=True,eight_old_development_tasks_audited=True,four_complete_pairs_exact=True,manifest_readback=True,zero_new_route_samples=True,exact_scientific_selection_certified=True))
 now=time.time();mono=time.monotonic();duration=min(read(O/'AUTHORIZATION.json')['absolute_ceiling_unix']-now,read(O/'AUTHORIZATION.json')['monotonic_ceiling']-mono);w=dict(started_unix=now,absolute_deadline_unix=now+duration,started_monotonic=mono,hard_stop_monotonic=mono+duration,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 approval=dict(models_authorized=True,synthetic_qualification_only=True,stop_on_safety_evidence=True,automatic_new24=False,allowed_task_ids=[t['task_id']for t in tasks],window_seconds=duration,absolute_deadline_unix=w['absolute_deadline_unix'])
 for t in tasks:assert envelope(t,approval,w,entry_check=True)
 negatives=[]
 for name,fn in [('modified_task',lambda:task_contract(dict(tasks[0],seed=0))),('synthetic_physics',lambda:envelope(tasks[0],approval,w)),('changed_ceiling',lambda:envelope(tasks[0],approval,dict(w,absolute_deadline_unix=w['absolute_deadline_unix']+1),entry_check=True))]:
  try:fn()
  except AssertionError:negatives.append(name)
  else:raise AssertionError('NEGATIVE_ACCEPTED '+name)
 old=science();np=old.np;checks=[];cpp=py=0
 class BeforeStep(BaseException):pass
 for slot in [1,9,17]:
  t=next(t for t in tasks if t['role']=='main' and t['slot']==slot);prior=R/'runs/v858_nav2_verified/v1218'/('t0_slot'+str(slot).zfill(2));p0=read(prior/'RESULT.json')['canonical_initial_packet'];setup=read(prior/'physics/SETUP.json');scan=read(prior/'INITIAL_SENSOR.json')
  owner=configure_owner(O,time.time()+300,w);requests=[]
  class Interface:
   count=0;d=types.SimpleNamespace(time=0.);adapter=types.SimpleNamespace(last=np.asarray(p0['controller_memory']['last_ctrl']),integral=p0['controller_memory']['integral'])
   def body(self):return p0['body']
   def steering_sample(self):return np.asarray(p0['steering']['position']+p0['steering']['velocity'])
   def scan(self):return copy.deepcopy(scan)
   def step(self,*row):requests.append(row);raise BeforeStep()
  out=O/('PRESTEP_COMPLETE_'+str(slot));out.mkdir()
  try:owner.navigate(Interface(),setup,t,time.time()+300,out,{})
  except BeforeStep:pass
  else:raise AssertionError('FIRST_STEP_NOT_REACHED')
  plan=read(out/'00_STATIC_00_PLAN.json');assert len(requests)==1 and plan['passed'] and all(plan['checks'].values());cpp+=4405;py+=len(plan['planned_body_requests']);checks.append(dict(slot=slot,request=requests[0]))
 # Parent fixed24 pure denominator code is byte identical; test development isolation.
 assert (C/'gates.py').read_bytes()==(R/'experiments/v1218_fixed24_current/gates.py').read_bytes()
 rows=[dict(role='main',slot=t['slot'],case_id=t['case_id'],direction=t['initial_axis_motion_direction'],functional_passed=True,safety_evidence_passed=True,result=dict(new_actual_native=1))for t in tasks if t['role']=='main']
 assert main_gate(rows)['passed'] and main_gate(rows[:-1])['full_denominator_success_rate']is None
 assert main_gate([dict(rows[0],role='development_main')]+rows)==main_gate(rows)
 cli=[]
 for entry,args,expect in [('worker.py',[str(C/'TASK_repair_main_slot02.json')],'NO_NEW_MODEL_AUTHORITY'),('t0.py',[str(C/'TASK_t0_slot01.json')],'NO_NEW_MODEL_AUTHORITY'),('audit.py',[str(C/'TASK_repair_main_slot02.json')],'AssertionError'),('campaign.py',[],'AssertionError'),('start.py',[],'AssertionError')]:
  p=subprocess.run([sys.executable,'-B',str(C/entry),*args],cwd=R,env=env,capture_output=True,text=True,timeout=20);assert p.returncode!=0 and expect in p.stdout+p.stderr and 'ModuleNotFoundError'not in p.stderr and 'ImportError'not in p.stderr,(entry,p.stdout,p.stderr);cli.append(dict(entry=entry,returncode=p.returncode))
 ff=O/'ENTRY_FIXTURES';ff.mkdir();dump(ff/'APPROVAL.json',approval);dump(ff/'WINDOW.json',w);isolated=[];fcntl.flock(lock,fcntl.LOCK_UN)
 try:
  (R/'REVIEW_PENDING').unlink()
  for t in [tasks[0],next(t for t in tasks if t['task_id']=='main_slot09'),next(t for t in tasks if t['task_id']=='main_slot17')]:
   p=subprocess.run([str(R/'run_phase.sh'),str(C/'worker.py'),str(C/('TASK_'+t['task_id']+'.json')),'--entry-check','--approval',str(ff/'APPROVAL.json'),'--window',str(ff/'WINDOW.json')],cwd=R,env=env,capture_output=True,text=True,timeout=30);assert p.returncode==0,(p.stdout,p.stderr);isolated.append(json.loads(p.stdout.strip().splitlines()[-1]))
 finally:(R/'REVIEW_PENDING').write_bytes(guard)
 result=dict(passed=True,selected_stop_audits=proofs,normal_first_step_checks=checks,negatives=negatives,cli=cli,cache=cache,isolated=isolated,analytical_cpp_native=cpp+sum(p['selection']['analytical_cpp_native']+p['complete_stop']['analytical_cpp_native']for p in proofs),analytical_python_native=py,models=0,new_mujoco_native=0,wall_s=time.monotonic()-start)
 dump(O/'QUALIFICATION.json',result);dump(O/'ISOLATED_QUALIFICATION.json',dict(passed=True,entries=isolated));dump(O/'READY_FOR_REVIEW.json',dict(preparation_gates_passed=True,physical_authorized=False));print(json.dumps(result))
if __name__=='__main__':
 try:main()
 except BaseException as e:dump(O/'PREPARATION_02_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),models=0,new_mujoco_native=0,unfinished_analytical_unknown=True));raise
