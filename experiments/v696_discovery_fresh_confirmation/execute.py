"""One bounded first-discovery task and success-only complete repeat."""
import os,sys,time,signal,subprocess,json,hashlib,fcntl,traceback
from pathlib import Path
repo=Path(__file__).resolve().parents[2];src=repo/'experiments/v695_discovery_verified_fixture';confirmation_src=Path(__file__).resolve().parent;root=repo/'runs/v696_discovery_fresh_confirmation'
prereq=json.loads((repo/'runs/v695_discovery_verified_fixture/development03/COMPLETION.json').read_text());assert prereq['moving_discovery_gate_passed'] and prereq['status']=='DEVELOPMENT03_BOTH_PHASES_AND_REPEATS_PASS','DEVELOPMENT_NOT_PASSED'
authorization=json.loads((repo/'DYNAMIC_OVERNIGHT_AUTHORIZATION_20261101.json').read_text());assert time.time()+15000<authorization['hard_deadline_unix'],'INSUFFICIENT_CONFIRMATION_BUDGET'
root.mkdir(exist_ok=True)
lock=(root/'window.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
window=root/'confirmation01';window.mkdir();started=time.time();deadline=min(started+15000,authorization['hard_deadline_unix'])
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
sources={p.name:sha(p)for p in src.glob('*.py')};documents={p.name:sha(p)for p in src.glob('*.md')};dump(window/'SOURCE_FREEZE.json',sources);dump(window/'DOCUMENT_FREEZE.json',documents)
external=repo/'experiments/v649_static_stability/audit_later_stop_certificate_geometry.py';external_sha=sha(external);dump(window/'EXTERNAL_AUDITOR_FREEZE.json',{'path':str(external.relative_to(repo)),'sha256':external_sha})
model=repo/'runs/v690_visible_eight_meter/training_8m/proposer.json';model_sha='fc9d3132c912033e2ec04cd8ae1ce236c818c484d5b96961c6f3dc1b0548b527';dump(window/'MODEL_FREEZE.json',{'path':str(model.relative_to(repo)),'sha256':model_sha,'gradient_updates':0})
ledger={'started_unix':started,'absolute_deadline_unix':deadline,'limit_s':15000,'pid':os.getpid(),'round_closed':False,'navigation_attempts':0,'preflight_attempts':0,'supervised_gradient_updates':0,'sac_gradient_updates':0,'single_cpu_sequential':True,'moving_discovery_gate_passed':False,'stage_access':0,'real_robot':0};dump(root/'ROUND_WINDOW.json',ledger)
preregistered=read(confirmation_src/'CANDIDATE_FREEZE.json');assert all(sha(repo/n)==h for n,h in preregistered['files'].items()),'PREREGISTERED_CANDIDATE_CHANGED'
ownfiles=[*confirmation_src.glob('*.py'),*confirmation_src.glob('*.md'),confirmation_src/'TASK_LIST.json'];ownfreeze={str(p.relative_to(repo)):sha(p)for p in ownfiles};dump(window/'CONFIRMATION_SOURCE_FREEZE.json',ownfreeze)
tasks=read(confirmation_src/'TASK_LIST.json');assert len(tasks)==24 and len({t['seed']for t in tasks})==24
for task in tasks:
 assert not(repo/'runs/v695_discovery_verified_fixture'/('fresh01_slot%02d'%task['slot'])).exists(),'TASK_ALREADY_USED'
nightpath=repo/'DYNAMIC_OVERNIGHT_LEDGER_20261101.json';night=read(nightpath)
assert night['fresh_confirmations_started']==0 and night['development_revisions_started']==3
night['fresh_confirmations_started']+=1;night['status']='FRESH_CONFIRMATION01_RUNNING';night['attempts'].append({'kind':'FRESH_CONFIRMATION','confirmation':1,'root':str(root.relative_to(repo)),'started_unix':started,'deadline_unix':deadline,'pid':os.getpid(),'status':'RUNNING'});dump(nightpath,night)
dump(window/'LOCKED_TASK_LIST.json',tasks)
results=[];status='RUNNING'
def execute(args,log,cap,envvars=None):
 assert time.time()+cap+3<deadline,'INSUFFICIENT_REMAINING_WINDOW'
 assert all(sha(src/n)==h for n,h in {**sources,**documents}.items())and sha(external)==external_sha and sha(model)==model_sha and all(sha(repo/n)==h for n,h in ownfreeze.items()),'FROZEN_SOURCE_MODEL_CHANGED'
 dump(window/'ACTIVE.json',{'command':args,'started_unix':time.time(),'env':envvars});env=os.environ.copy();env.update(envvars or {})
 with log.open('w')as f:
  child=subprocess.Popen([str(repo/'run_phase.sh'),*args],cwd=repo,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:return child.wait(timeout=cap)
  except BaseException:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=2)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
   raise
def run(name,preflight=False,phase=0.,seed=95000011):
 ledger['preflight_attempts'if preflight else'navigation_attempts']+=1;assert ledger['preflight_attempts']<=24 and ledger['navigation_attempts']<=27;dump(root/'ROUND_WINDOW.json',ledger)
 env={'PHASE_COURSE_DISTANCE':'8','PHASE_COURSE_PHASE':str(phase),'PHASE_PROPOSAL_MODEL':str(model)}
 args=[str(src.relative_to(repo)/'run_static.py'),'--name',name,'--seed',str(seed),'--wall-seconds',str(45 if preflight else 900),'--max-steps','1200','--initial-observation-steps','0']
 if preflight:args+=['--feasibility-only']
 code=execute(args,window/(name+'.console'),50 if preflight else 905,env);pair=repo/'runs/v695_discovery_verified_fixture'/name/'paired'
 if preflight:
  assert code==0,'PREFLIGHT_RUNNER_FAILED'
  assert execute([str(src.relative_to(repo)/'audit_discovery.py'),str(pair),'--preflight'],pair/'initial_unseen_audit.console',30)==0,'PREFLIGHT_CAUSAL_AUDIT_FAILED'
  c=read(pair/'DYNAMIC_PROTOCOL.json');assert read(pair/'TASK_FEASIBILITY.json')['eligible']and c['swept_envelope_reference']['eligible']and c['swept_envelope_reference']['continuous_polygonal_pose_clearance_lower_bound_m']>=.15 and c['protected_junction_clearance_of_sweep_m']>=.05
  return pair
 completion=read(pair/'completion.json');r=read(pair/'geometry_memory/result.json')if(pair/'geometry_memory/result.json').exists()else None
 results.append({'name':name,'run':str(pair.relative_to(repo)),'runner_exit':code,'result':r,'completion_status':completion['status']});dump(window/'RESULTS.json',results)
 partial=read(pair/'geometry_memory/interrupted.json')if r is None and(pair/'geometry_memory/interrupted.json').exists()else None
 if r is not None or(partial and partial['public_steps']>0):
  assert execute([str(src.relative_to(repo)/'replay_native_audit.py'),str(pair)],pair/'replay.console',35)==0,'REPLAY_EXECUTION_FAILED'
  assert read(pair/'NATIVE_REPLAY_AUDIT.json')['status']=='MATCHED_RECORDED_PUBLIC_STATES','REPLAY_FAILED'
 assert code==0 and r is not None,'TASK_RUNNER_FAILED'
 for script,filename,cap in [('audit_run.py','physical_audit',55),('audit_route_commitment.py','route_audit',60),('audit_projection_learning.py','projection_learning',60)]:
  args=[str(src.relative_to(repo)/script),str(pair)]
  if script=='audit_run.py':args+=['--window',str(window)]
  if script=='audit_projection_learning.py':args+=['--model',str(model)]
  assert execute(args,pair/(filename+'.console'),cap)==0,script+'_FAILED'
 dump(pair/'TAIL_AUDITOR_SOURCE.json',{'path':str(external.relative_to(repo)),'sha256':external_sha})
 assert execute([str(external.relative_to(repo)),str(pair)],pair/'tail_audit.console',40)==0,'TAIL_AUDIT_FAILED'
 chain=execute([str(src.relative_to(repo)/'audit_discovery.py'),str(pair)],pair/'discovery_chain.console',60)
 results[-1]['physical_audits_passed']=True;results[-1]['discovery_chain_audit_passed']=chain==0;dump(window/'RESULTS.json',results)
 # Functional failures remain in the fixed24 denominator; physical audit failures already stop above.
 return pair
def repeat(base,pair):
 import numpy as np
 from contact_fingerprint import compare_contacts
 a=[json.loads(s)for s in(base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()];b=[json.loads(s)for s in(pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
 errors={k:float(np.max(abs(np.asarray([x[k]for x in a])-np.asarray([x[k]for x in b]))))if len(a)==len(b)else None for k in ['qpos_full','qvel_full','ctrl','mocap_pos']};contacts=compare_contacts(base,pair)
 checks={'same_model':sha(base/'scene_model.mjb')==sha(pair/'scene_model.mjb'),'same_initial':read(base/'geometry_memory/result.json')['normalized_initial_state_hash']==read(pair/'geometry_memory/result.json')['normalized_initial_state_hash'],'exact_full_state_ctrl':all(v is not None and v<=1e-8 for v in errors.values()),'contacts':contacts['passed'],'same_discovery_event':read(base/'geometry_memory/FIRST_DISCOVERY.json')==read(pair/'geometry_memory/FIRST_DISCOVERY.json')}
 dump(pair/'EXACT_REPEAT_AUDIT.json',{'checks':checks,'errors':errors,'contacts':contacts,'passed':all(checks.values())});assert all(checks.values()),'COMPLETE_REPEAT_FAILED'
try:
 for record in prereq['results']:
  pair=repo/record['run'];assert read(pair/'INDEPENDENT_CANONICAL_AUDIT.json')['status']=='ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS'
  assert read(pair/'DISCOVERY_CHAIN_AUDIT.json')['status']=='PASS'
 assert len(prereq['results'])==4
 for name in ['phase0_repeat','phasepi2_repeat']:
  assert read(repo/'runs/v695_discovery_verified_fixture'/name/'paired/EXACT_REPEAT_AUDIT.json')['passed']
 for task in tasks:run('fresh01_t0_slot%02d'%task['slot'],True,task['phase'],task['seed'])
 nonarrivals=0;baselines={}
 for task in tasks:
  pair=run('fresh01_slot%02d'%task['slot'],phase=task['phase'],seed=task['seed']);baselines[task['slot']]=pair
  results[-1].update(task=task,repeat=False);dump(window/'RESULTS.json',results)
  if not(results[-1]['result']['strict_safe_arrival']and results[-1]['discovery_chain_audit_passed']):nonarrivals+=1
  assert nonarrivals<2,'SECOND_FRESH_FUNCTIONAL_NON_SUCCESS'
 groups={name:sum(x['result']['strict_safe_arrival']and x['discovery_chain_audit_passed']for x in results if x['task']['initial_motion_direction']==name)for name in ['POSITIVE_Y','NEGATIVE_Y']}
 assert len(results)==24 and sum(groups.values())>=23 and min(groups.values())>=11,'FRESH24_FUNCTIONAL_GATE_FAILED'
 for slot in [1,8,20]:
  task=tasks[slot-1];assert results[slot-1]['result']['strict_safe_arrival']and results[slot-1]['discovery_chain_audit_passed'],'PRESELECTED_REPEAT_BASELINE_FAILED'
  again=run('fresh01_repeat_slot%02d'%slot,phase=task['phase'],seed=task['seed']);results[-1].update(task=task,repeat=True);dump(window/'RESULTS.json',results)
  assert results[-1]['result']['strict_safe_arrival']and results[-1]['discovery_chain_audit_passed'],'REPEAT_FUNCTIONAL_NON_SUCCESS'
  repeat(baselines[slot],again)
 ledger['moving_discovery_gate_passed']=True;status='PROVISIONAL_FRESH24_AND_THREE_REPEATS_PASS'
except BaseException as e:
 status='CLOSED_NON_ARRIVAL'if str(e)=='CLOSED_NON_ARRIVAL'else'STOPPED_EXCEPTION';dump(window/'ERROR.json',{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
finally:
 ledger.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump(root/'ROUND_WINDOW.json',ledger)
 dump(window/'COMPLETION.json',{'status':status,'results':results,'round_closed':True,'elapsed_s':time.time()-started,'moving_discovery_gate_passed':ledger['moving_discovery_gate_passed'],'automatic_additional_simulation':False,'no_original_complex_field_or_global_safety_claim':True})
 dump(window/'ACTIVE.json',{'status':status,'completed':True});print(status,flush=True)

 night=read(nightpath);night['attempts'][-1].update(status=status,completed_unix=time.time(),moving_discovery_gate_passed=ledger['moving_discovery_gate_passed']);night['status']='CONFIRMATION_PROVISIONAL_NEEDS_INDEPENDENT_FINAL_AUDIT'if ledger['moving_discovery_gate_passed']else'CONFIRMATION_FAILED_STOP_NO_FOURTH_DEVELOPMENT'
 night['navigation_tasks']+=ledger['navigation_attempts'];night['cumulative_native_navigation_steps']+=sum(x['result']['physics_steps']for x in results if x['result'])
 night['cumulative_private_integrations']+=sum(x['result']['prediction_steps']for x in results if x['result'])
 for name in ['fixed73/COMPLETION.json']:
  if(root/name).exists():
   fixed=read(root/name);night['cumulative_native_replay_steps']+=fixed['replay_native_steps'];night['cumulative_private_integrations']+=fixed['private_prediction_integrations']
 for x in results:
  f=repo/x['run']/'NATIVE_REPLAY_AUDIT.json'
  if f.exists():night['cumulative_native_replay_steps']+=read(f)['replay_integration_steps']
 dump(nightpath,night)
