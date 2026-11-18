"""Offline sequential frozen-candidate campaign, one immutable09:00 cutoff."""
import sys,os,json,time,signal,subprocess,hashlib,fcntl,traceback,math
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1121_coupled_route_night'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));from fresh_campaign import same_complete
sys.path.insert(0,str(C));from policy import classify

def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def used():
 seen=set();total=0
 for base,dirs,names in os.walk(R/'runs',followlinks=False):
  dirs[:]=[d for d in dirs if not Path(base,d).is_symlink()]
  for name in names:
   p=Path(base,name)
   if p.is_symlink():continue
   st=p.stat();key=st.st_dev,st.st_ino
   if key not in seen:seen.add(key);total+=st.st_size
 return total
class HardStop(Exception):pass

def main():
 w=json.loads((O/'ROUND_WINDOW.json').read_text());guard=(O/'GUARD.bin').read_bytes();assert sha(R/'REVIEW_PENDING')==hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';own=(O/'driver.lock').open('a+');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
 q=json.loads((O/'FINAL_ENTRY_QUALIFICATION.json').read_text());assert q['passed'];freeze=json.loads((C/'SOURCE_FREEZE.json').read_text())['files'];tasks=json.loads((C/'TASKS.json').read_text());candidates=json.loads((C/'CANDIDATES.json').read_text());cfg=json.loads((O/'CONFIG.json').read_text());assert not(O/'DRIVER_STARTED.json').exists();dump(O/'DRIVER_STARTED.json',{'pid':os.getpid(),'proc_start':Path('/proc/self/stat').read_text().split()[21],'started_unix':time.time(),'deadline_unix':w['absolute_deadline_unix'],'boot_id':w['boot_id']});rows=[];gates=[];offline=[];child=None;hard_error=None;selected=None;confirmation=None;task_by_id={t['task_id']:t for t in tasks};attempted=[];repeat_rows=[]
 def remaining():
  assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'CROSS_BOOT_STOP'
  return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
 def frozen():return all(sha(R/p)==h for p,h in freeze.items())
 def halt(*_):raise HardStop('ABSOLUTE09_DEADLINE_OR_TERMINATION')
 def stop_child():
  nonlocal child
  if child is not None and child.poll()is None:
   try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=3)
   except BaseException:
    try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
    except ProcessLookupError:pass
  child=None
 def job(args,console,limit,stage,task_id=None):
  nonlocal child
  assert remaining()>limit+15,'INSUFFICIENT_BOUNDED_JOB_RESERVE';assert used()+256*1024**2<=cfg['temporary_limit_bytes'],'TEMPORARY_STORAGE_RESERVE';assert frozen(),'FROZEN_SOURCE_CHANGED'
  with Path(console).open('x')as log:
   child=subprocess.Popen(args,cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'ACTIVE.json',{'pid':child.pid,'proc_start':Path('/proc',str(child.pid),'stat').read_text().split()[21],'stage':stage,'task_id':task_id,'started_unix':time.time()})
   try:return child.wait(timeout=min(limit,remaining()-5))
   finally:stop_child()
 def activate(candidate,preflight):
  cfg['active_candidate']=candidate;cfg['preflight_output']=str(preflight);dump(O/'CONFIG.json',cfg)
 def physical(task,candidate,preflight=None):
  nonlocal rows
  assert remaining()>(145 if task['kind']=='t0'else 1230),'TASK_AUDIT_ROOT_RESERVE';assert(R/'REVIEW_PENDING').read_bytes()==guard;activate(candidate,preflight or task['output']);attempted.append(task['task_id']);dump(O/'ATTEMPTS.json',attempted)
  approval={'models_authorized':True,'absolute_deadline_unix':w['absolute_deadline_unix'],'allowed_task_ids':[task['task_id']],'task_id':task['task_id'],'candidate_id':candidate['id']};dump(O/'APPROVAL.json',approval);(R/'REVIEW_PENDING').unlink()
  try:code=job([str(R/'run_phase.sh'),str((C/('t0.py'if task['kind']=='t0'else'worker.py')).relative_to(R)),str(O/(task['task_id']+'.json'))],O/(task['task_id']+'.console'),100 if task['kind']=='t0'else 905,'preflight'if task['kind']=='t0'else'navigation',task['task_id'])
  finally:(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',{'models_authorized':False,'between_jobs':True})
  out=Path(task['output']);p=out/'RESULT.json';p=p if p.exists()else out/'physics/paired/ENTRY_FAILURE_RESULT.json';result=json.loads(p.read_text())if p.exists()else {'passed':False,'missing_result':True};row={'task':task,'returncode':code,'result':result,'candidate':candidate['id']};rows.append(row);dump(O/'RESULTS.json',rows)
  if task['kind']=='t0':
   if code!=0 or not result.get('passed'):raise HardStop('CANONICAL_PREFLIGHT_FAILURE')
   return row
  if code!=0 and not result.get('functional_refusal_safely_stopped'):raise HardStop('SAFETY_SOURCE_MODEL_STATE_CONTROL_OR_EVIDENCE_ANOMALY')
  code=job([sys.executable,'-B',str(C/'audit.py'),str(O/(task['task_id']+'.json'))],O/(task['task_id']+'.audit.console'),300,'independent_zero_model_audit',task['task_id']);a=out/'FINAL_INDEPENDENT_AUDIT.json'
  if code!=0 or not a.exists():raise HardStop('INDEPENDENT_EVIDENCE_ANOMALY')
  row['audit']=json.loads(a.read_text());dump(O/'RESULTS.json',rows)
  row['classification']=classify(row['returncode'],result,row['audit']);dump(O/'RESULTS.json',rows)
  if row['classification']=='HARD':raise HardStop('INDEPENDENT_EVIDENCE_OR_UNVERIFIED_STOP_ANOMALY')
  return row
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,remaining()))
 try:
  assert frozen();preflights={}
  for case in ['EAST_WEST','WEST_EAST','NORTH_SOUTH']:
   t=task_by_id['t0_'+case];physical(t,candidates[0]);preflights[case]=Path(t['output'])
  for candidate in candidates:
   if remaining()<1250:break
   gate={'candidate':candidate['id'],'passed':False,'route_results':[],'closed':False};gates.append(gate);dump(O/'CANDIDATE_GATES.json',gates)
   for case in ['EAST_WEST','WEST_EAST','NORTH_SOUTH']:
    if remaining()<2500:gate['reason']='NO_MAIN_AND_REPEAT_RESERVE';break
    main=task_by_id[candidate['id']+'_main_'+case];row=physical(main,candidate,preflights[case]);route={'case':case,'main':main['task_id'],'main_passed':row['result'].get('passed')and row['audit'].get('passed')};gate['route_results'].append(route)
    if not route['main_passed']:gate['reason']='FUNCTIONAL_REFUSAL_WITH_FULL_VERIFIED_STOP';break
    repeat=task_by_id[candidate['id']+'_repeat_'+case];rep=physical(repeat,candidate,preflights[case]);route['repeat']=repeat['task_id'];route['repeat_passed']=rep['result'].get('passed')and rep['audit'].get('passed')
    if not route['repeat_passed']:gate['reason']='REPEAT_FUNCTIONAL_FAILURE_WITH_VERIFIED_STOP';break
    try:exact=same_complete(main,repeat)
    except BaseException as e:raise HardStop('COMPLETE_REPEAT_STATE_CONTACT_DISCOVERY_MISMATCH '+repr(e))
    route['complete_repeat']=exact;repeat_rows.append(exact);dump(O/'CANDIDATE_GATES.json',gates)
   gate['passed']=bool(len(gate['route_results'])==3 and all(r.get('main_passed')and r.get('repeat_passed')and r.get('complete_repeat',{}).get('passed')for r in gate['route_results']));gate['closed']=True;dump(O/'CANDIDATE_GATES.json',gates)
   if gate['passed']:
    assert frozen();selected=candidate;dump(O/'DEVELOPMENT_GATE.json',dict(passed=True,candidate=candidate,gate=gate,source_unchanged=True,closed=True));break
  if selected and remaining()>=36000:
   confirmation={'started':True,'candidate':selected,'mains':[],'repeats':[],'passed':False,'pool_sha256':sha(C/'CONFIRMATION_POOL.json')};dump(O/'CONFIRMATION.json',confirmation);confpre={}
   for i in range(1,25):
    t=task_by_id['night_t0_confirm_%02d'%i];physical(t,selected);confpre[i]=Path(t['output'])
   failures=0
   for i in range(1,25):
    t=task_by_id['night_confirm_main_%02d'%i];row=physical(t,selected,confpre[i]);passed=bool(row['result'].get('passed')and row['audit'].get('passed'));confirmation['mains'].append({'slot':i,'case':t['case_id'],'passed':passed,'task_id':t['task_id']});failures+=not passed;dump(O/'CONFIRMATION.json',confirmation)
    if failures>=2:confirmation['reason']='SECOND_FUNCTIONAL_FAILURE';break
   if len(confirmation['mains'])==24:
    pool=json.loads((C/'CONFIRMATION_POOL.json').read_text());ok=[r for r in confirmation['mains']if r['passed']];directions={p['slot']:p['initial_axis_motion_direction']for p in pool};main_gate=len(ok)>=23 and all(sum(r['case']==case for r in ok)>=7 for case in ['WEST_EAST','NORTH_SOUTH','EAST_WEST'])and all(sum(directions[r['slot']]==d for r in ok)>=11 for d in ['POSITIVE_AXIS','NEGATIVE_AXIS']);confirmation['main_gate_passed']=main_gate
    if main_gate and all(confirmation['mains'][i-1]['passed']for i in [1,9,17]):
     for i in [1,9,17]:
      t=task_by_id['night_confirm_repeat_%02d'%i];row=physical(t,selected,confpre[i]);success=bool(row['result'].get('passed')and row['audit'].get('passed'))
      if not success:confirmation['reason']='FIXED_REPEAT_FUNCTIONAL_FAILURE';break
      try:exact=same_complete(task_by_id['night_confirm_main_%02d'%i],t)
      except BaseException as e:raise HardStop('CONFIRMATION_REPEAT_EVIDENCE_MISMATCH '+repr(e))
      confirmation['repeats'].append({'slot':i,'passed':exact['passed'],'exact':exact});dump(O/'CONFIRMATION.json',confirmation)
     confirmation['passed']=len(confirmation['repeats'])==3 and all(r['passed']for r in confirmation['repeats'])
    else:confirmation['reason']='LOCKED_MAIN_OR_FIXED_BASELINE_GATE_FAILED'
   confirmation['closed']=True;dump(O/'CONFIRMATION.json',confirmation)
  elif selected:confirmation={'started':False,'reason':'INSUFFICIENT_FULL_CONFIRMATION_RESERVE','required_s':36000,'remaining_s':remaining(),'denominator':None};dump(O/'CONFIRMATION.json',confirmation)
  # Continue useful preregistered DEVELOPMENT analysis after functional queue
  # exhaustion, completion or no full-confirmation reserve. No confirm data.
  inputs=[str(R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json'),str(R/'runs/v1092_stopped_replan/FAILED_ACTUAL_INPUT.json')]
  for row in rows:
   p=Path(row['task']['output'])/'COUPLED_ENTRY.json'
   if row['task'].get('stage')!='confirmation'and p.exists()and str(p)not in inputs:inputs.append(str(p))
  dump(O/'OFFLINE_INPUTS.json',inputs);number=0
  for offset_index in range(72):
   if remaining()<310:break
   heading=0. if offset_index==0 else ((offset_index+1)//2)*(math.pi/36)*(1 if offset_index%2 else-1)
   for radius_index in range(12):
    if remaining()<310:break
    for inp in inputs:
     if remaining()<310:break
     number+=1;item={'number':number,'input':inp,'goal_heading_offset':heading,'radius_extra':radius_index*.05,'output':str(O/'offline'/('%05d'%number))};file=O/('offline_job_%05d.json'%number);dump(file,item);code=job([sys.executable,'-B',str(C/'offline.py'),str(file)],O/('offline_%05d.console'%number),290,'offline_development_feasibility',str(number));p=Path(item['output'])/'RESULT.json'
     if code!=0 or not p.exists():raise HardStop('OFFLINE_OPERATION_OR_ACCOUNTING_ANOMALY')
     data=json.loads(p.read_text());offline.append({'job':item,'passed':data.get('passed'),'counts':data.get('counts'),'wall_s':data.get('wall_s')});dump(O/'OFFLINE_RESULTS.json',offline)
     if data.get('hard_anomaly'):raise HardStop('OFFLINE_SOURCE_MODEL_OR_EVIDENCE_ANOMALY')
 except BaseException as e:hard_error={'error':repr(e),'traceback':traceback.format_exc()};dump(O/'ERROR.json',hard_error)
 finally:
  stop_child();(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',{'models_authorized':False,'closed':True});dump(O/'ACTIVE.json',{'closed':True});signal.setitimer(signal.ITIMER_REAL,0)
 keys=['vehicle_initializations','new_actual_native','own_replay_native','replay_state_initializations','historical_replay_native','private_mujoco_native','training_updates'];counts={k:sum(r['result'][k]for r in rows)if rows and all(isinstance(r['result'].get(k),(int,float))for r in rows)else None if rows else 0 for k in keys};completed={'closed':True,'hard_deadline_unix':w['absolute_deadline_unix'],'started_unix':w['started_unix'],'closed_unix':time.time(),'candidate_gates':gates,'confirmation':confirmation,'attempted':attempted,'unexecuted':[t['task_id']for t in tasks if t['task_id']not in attempted],'counts':counts,'offline_jobs':len(offline),'hard_error':hard_error,'guard_original':(R/'REVIEW_PENDING').read_bytes()==guard,'source_unchanged':frozen(),'three_route_passed':selected is not None,'fixed24_passed':bool(confirmation and confirmation.get('passed')),'all24_executed':bool(confirmation and len(confirmation.get('mains',[]))==24),'new24_denominator':24 if confirmation and len(confirmation.get('mains',[]))==24 else None,'stop_reason':'HARD_ANOMALY_OR_DEADLINE'if hard_error else'FINITE_QUEUE_OR_FINALIZATION_RESERVE','no_Stage_access':True};dump(O/'COMPLETION.json',completed);dump(O/'LEDGER.json',completed)
 report=R/cfg['report'];report.write_text('# V1121 coupled complete-source overnight\n\n```json\n'+json.dumps(completed,ensure_ascii=False,indent=2)+'\n```\n\nThe geometric guide contract changed explicitly; physical safety and actual source tracking gates remain. Development/repeats/offline predictions are not independent confirmation samples. Fixed24 only after a single same-version full three-route gate. No realtime, arbitrary obstruction/multiple actor/map/RAS superiority claim.\n')
 current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_overnight=completed,latest_report=cfg['report']);dump(R/'CURRENT_EXPERIMENT.json',current)
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V1121通宵闭批：three_route='+str(completed['three_route_passed'])+', fixed24='+str(completed['fixed24_passed'])+', counts='+json.dumps(counts)+', offline_jobs='+str(len(offline))+', hard_error='+str(hard_error is not None)+'；新几何引导合同/原物理门保持，09:00不延期，见'+cfg['report']+'。\n')
 try:
  with(O/'finalize.console').open('x')as log:subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=300)
 except BaseException as e:dump(O/'FINALIZE_ERROR.json',{'error':repr(e),'models':0,'physical_integrations':0,'raw_retained':True})
 print(json.dumps(completed,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
