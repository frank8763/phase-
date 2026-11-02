"""New bounded V697 development; old overnight records are read-only."""
import os,sys,time,signal,subprocess,json,hashlib,fcntl,traceback
from pathlib import Path
src=Path(__file__).resolve().parent;repo=src.parents[1];root=repo/'runs/v697_rpccr_dynamic_initialization';root.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n');tmp.replace(p)
freeze=read(src/'CANDIDATE_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items()),'PREREGISTERED_SOURCE_CHANGED'
assert read(repo/'DYNAMIC_OVERNIGHT_LEDGER_20261101.json')['status']=='CLOSED_PREFLIGHT_BLOCKED_NOT_CONFIRMED','OLD_WINDOW_NOT_CLOSED'
lock=(root/'window.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
phase_lock=(repo/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(phase_lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(phase_lock,fcntl.LOCK_UN)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
window=root/'development01';window.mkdir();started=time.time();deadline=started+3600
sources={p.name:sha(p)for p in src.glob('*.py')};documents={p.name:sha(p)for p in src.glob('*.md')};dump(window/'SOURCE_FREEZE.json',sources);dump(window/'DOCUMENT_FREEZE.json',documents)
external=repo/'experiments/v649_static_stability/audit_later_stop_certificate_geometry.py';external_sha=sha(external);dump(window/'EXTERNAL_AUDITOR_FREEZE.json',{'path':str(external.relative_to(repo)),'sha256':external_sha})
model=repo/'runs/v690_visible_eight_meter/training_8m/proposer.json';model_sha='fc9d3132c912033e2ec04cd8ae1ce236c818c484d5b96961c6f3dc1b0548b527';assert sha(model)==model_sha;dump(window/'MODEL_FREEZE.json',{'path':str(model.relative_to(repo)),'sha256':model_sha,'gradient_updates':0})
ledger={'started_unix':started,'absolute_deadline_unix':deadline,'limit_s':3600,'pid':os.getpid(),'round_closed':False,'navigation_attempts':0,'preflight_attempts':0,'supervised_gradient_updates':0,'sac_gradient_updates':0,'single_cpu_sequential':True,'moving_discovery_gate_passed':False,'stage_access':0,'real_robot':0,'algorithm_revisions':0,'role':'INITIALIZATION_REPAIR_DEVELOPMENT_NOT_FRESH_CONFIRMATION'};dump(root/'ROUND_WINDOW.json',ledger)
tasks=read(src/'ORIGINAL_V696_TASK_LIST.json');assert len(tasks)==24 and tasks[11]['seed']==97010012;dump(window/'LOCKED_PREFLIGHT_TASK_LIST.json',tasks)
results=[];status='RUNNING';preflight_records=[]
def execute(args,log,cap,envvars=None):
 assert time.time()+cap+3<deadline,'INSUFFICIENT_REMAINING_WINDOW'
 assert all(sha(src/n)==h for n,h in {**sources,**documents}.items())and sha(external)==external_sha and sha(model)==model_sha,'FROZEN_SOURCE_MODEL_CHANGED'
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
 ledger['preflight_attempts'if preflight else'navigation_attempts']+=1;assert ledger['preflight_attempts']<=24 and ledger['navigation_attempts']<=3;dump(root/'ROUND_WINDOW.json',ledger)
 env={'PHASE_COURSE_DISTANCE':'8','PHASE_COURSE_PHASE':str(phase),'PHASE_PROPOSAL_MODEL':str(model)}
 args=[str(src.relative_to(repo)/'run_static.py'),'--name',name,'--seed',str(seed),'--wall-seconds',str(45 if preflight else 900),'--max-steps','1200','--initial-observation-steps','0']
 if preflight:args+=['--feasibility-only']
 code=execute(args,window/(name+'.console'),50 if preflight else 905,env);pair=root/name/'paired'
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
 assert r['strict_safe_arrival'],'CLOSED_NON_ARRIVAL'
 assert chain==0,'DISCOVERY_CHAIN_FAILED'
 return pair
def repeat(base,pair):
 import numpy as np
 from contact_fingerprint import compare_contacts
 a=[json.loads(s)for s in(base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()];b=[json.loads(s)for s in(pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
 errors={k:float(np.max(abs(np.asarray([x[k]for x in a])-np.asarray([x[k]for x in b]))))if len(a)==len(b)else None for k in ['qpos_full','qvel_full','ctrl','mocap_pos']};contacts=compare_contacts(base,pair)
 checks={'same_model':sha(base/'scene_model.mjb')==sha(pair/'scene_model.mjb'),'same_initial':read(base/'geometry_memory/result.json')['normalized_initial_state_hash']==read(pair/'geometry_memory/result.json')['normalized_initial_state_hash'],'exact_full_state_ctrl':all(v is not None and v<=1e-8 for v in errors.values()),'contacts':contacts['passed'],'same_discovery_event':read(base/'geometry_memory/FIRST_DISCOVERY.json')==read(pair/'geometry_memory/FIRST_DISCOVERY.json')}
 dump(pair/'EXACT_REPEAT_AUDIT.json',{'checks':checks,'errors':errors,'contacts':contacts,'passed':all(checks.values())});assert all(checks.values()),'COMPLETE_REPEAT_FAILED'
try:
 for task in tasks:
  pair=run('t0_slot%02d'%task['slot'],True,task['phase'],task['seed']);preflight_records.append({'task':task,'run':str(pair.relative_to(repo))});dump(window/'PREFLIGHTS.json',preflight_records)
 assert execute([str(src.relative_to(repo)/'audit_initialization.py'),str(window)],window/'initialization_audit.console',30)==0,'INITIALIZATION_AUDIT_FAILED'
 baseline=run('anchor_phase0',phase=0.,seed=95000011)
 repeat(repo/'runs/v695_discovery_verified_fixture/phase0/paired',baseline)
 task=tasks[11];target=run('original_slot12',phase=task['phase'],seed=task['seed'])
 again=run('original_slot12_repeat',phase=task['phase'],seed=task['seed']);repeat(target,again)
 ledger['moving_discovery_gate_passed']=True;status='PROVISIONAL_INITIALIZATION_AND_ORIGINAL_SLOT12_DEVELOPMENT_PASS'
except BaseException as e:
 status='CLOSED_NON_ARRIVAL'if str(e)=='CLOSED_NON_ARRIVAL'else'STOPPED_EXCEPTION';dump(window/'ERROR.json',{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
finally:
 ledger.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump(root/'ROUND_WINDOW.json',ledger)
 dump(window/'COMPLETION.json',{'status':status,'results':results,'preflights':preflight_records,'round_closed':True,'elapsed_s':time.time()-started,'moving_discovery_gate_passed':ledger['moving_discovery_gate_passed'],'automatic_additional_simulation':False,'fresh_confirmation':False,'old_overnight_records_changed':False})
 dump(window/'ACTIVE.json',{'status':status,'completed':True});print(status,flush=True)
