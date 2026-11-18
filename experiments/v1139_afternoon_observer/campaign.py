"""Finite gated offline campaign, single immutable 2026-11-14 14:30 deadline."""
import sys,os,signal,subprocess,time,fcntl,traceback
from afternoon_tools import *

def main():
 assert not(O/'DRIVER_STARTED.json').exists();lock=(O/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard=(O/'GUARD.bin').read_bytes();assert sha(R/'REVIEW_PENDING')==GUARD_SHA and source_ok();w=json.loads((O/'ROUND_WINDOW.json').read_text());dump(O/'DRIVER_STARTED.json',{'pid':os.getpid(),'proc_start':Path('/proc/self/stat').read_text().split()[21]});child=None;results=[];attempts=[];error=None;reason='FINITE_QUEUE_COMPLETE';passed=False
 def stop():
  nonlocal child
  if child and child.poll()is None:
   try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=5)
   except BaseException:
    try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
    except ProcessLookupError:pass
  child=None
 def halt(*_):raise TimeoutError('ABSOLUTE_1430_STOP')
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,remaining(w)))
 def job(name,script,args,limit,physical=False):
  nonlocal child
  assert source_ok(),'FROZEN_SOURCE_CHANGED';assert used()+128*1024**2<2*1024**3,'TEMPORARY_STORAGE_RESERVE';assert remaining()>limit+30,'INSUFFICIENT_ABSOLUTE_REMAINDER';assert (R/'REVIEW_PENDING').read_bytes()==guard
  command=[str(R/'run_phase.sh'),str((C/script).relative_to(R)),*map(str,args)]if physical else[sys.executable,'-B',str(C/script),*map(str,args)]
  if physical:(R/'REVIEW_PENDING').unlink()
  try:
   with(O/(name+'.console')).open('x')as log:
    child=subprocess.Popen(command,cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'ACTIVE.json',{'stage':name,'pid':child.pid,'proc_start':Path('/proc',str(child.pid),'stat').read_text().split()[21],'physical':physical});code=child.wait(timeout=min(limit,remaining()-15))
  finally:stop();(R/'REVIEW_PENDING').write_bytes(guard)
  return code
 try:
  assert all(json.loads((O/f).read_text())['passed']for f in ['ENTRY_QUALIFICATION.json','PREPARATION.json','HISTORY_CONTROLLER_QUALIFICATION.json']);code=job('software','software_worker.py',[],650);soft=json.loads((O/'software/RESULT.json').read_text());results.append({'stage':'software','returncode':code,'result':soft});dump(O/'RESULTS.json',results)
  if code!=0 or soft.get('error'):raise AssertionError('SOFTWARE_OPERATION_OR_EVIDENCE_ERROR')
  if not soft['passed']:reason='SOFTWARE_COMPONENT_NOT_PASSED';return
  tasks=json.loads((C/'TASKS.json').read_text());tasks.append(json.loads((C/'OBSERVER_TASK.json').read_text()))
  for task in tasks:
   observe=task['task_id']=='observation_refuge';limit=1000 if observe else 800;attempts.append(task);dump(O/'ATTEMPTS.json',attempts);code=job(task['task_id'],'observer_worker.py'if observe else'static_worker.py',[C/('OBSERVER_TASK.json'if observe else'TASK_'+task['task_id']+'.json')],limit,True);file=Path(task['output'])/'RESULT.json';r=json.loads(file.read_text())if file.exists()else{'passed':False,'missing_result':True};row={'stage':task['task_id'],'returncode':code,'result':r};results.append(row);dump(O/'RESULTS.json',results)
   if r.get('evidence_saved')and r.get('new_actual_native',0):
    audit_script='observer_audit.py'if observe else'static_audit.py';acode=job(task['task_id']+'_audit',audit_script,[C/('OBSERVER_TASK.json'if observe else'TASK_'+task['task_id']+'.json')],180);af=Path(task['output'])/'FINAL_INDEPENDENT_AUDIT.json';row['audit']=json.loads(af.read_text())if af.exists()else{'passed':False,'missing_audit':True};row['audit_returncode']=acode;dump(O/'RESULTS.json',results)
   if code!=0 or not r['passed']or not row.get('audit',{}).get('passed'):reason='FIRST_PHYSICAL_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE';return
  code=job('actual_observation_refit','post_observation.py',[],650);post=json.loads((O/'post_observation/RESULT.json').read_text())if(O/'post_observation/RESULT.json').exists()else{'passed':False,'missing_result':True};results.append({'stage':'actual_observation_refit','returncode':code,'result':post});dump(O/'RESULTS.json',results);assert code==0 and post['passed'],'ACTUAL_OBSERVATION_OR_SOURCE_ERROR';passed=True
 except BaseException as e:error={'error':repr(e),'traceback':traceback.format_exc()};reason='EXCEPTION_OR_DEADLINE';dump(O/'ERROR.json',error)
 finally:
  stop();(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',{'models_authorized':False,'closed':True});dump(O/'ACTIVE.json',{'closed':True});signal.setitimer(signal.ITIMER_REAL,0)
  physical=[r for r in results if r['stage']in ['negative_to_positive','positive_to_negative','observation_refuge']];keys=['vehicle_initializations','new_actual_native','own_replay_native','replay_state_initializations','private_mujoco_native','training_updates','analytical_prediction_native'];counts={k:sum(r['result'][k]for r in physical)if len(physical)==len(attempts)and all(r['result'].get(k)is not None for r in physical)else None for k in keys};counts['historical_reconstruction_native']=sum(r['result'].get('historical_reconstruction_native',0)for r in physical)if len(physical)==len(attempts)else None;obs=[r['result']for r in physical if r['stage']=='observation_refuge'];counts['new_observer_component_native']=obs[0].get('new_observer_component_native')if obs else 0
  result={'closed':True,'passed_afternoon_components':passed,'stop_reason':reason,'error':error,'attempted':[t['task_id']for t in attempts],'unexecuted':[t['task_id']for t in [*json.loads((C/'TASKS.json').read_text()),json.loads((C/'OBSERVER_TASK.json').read_text())]if t not in attempts],'counts':counts,'stage_results':results,'source_unchanged':source_ok(),'guard_original':sha(R/'REVIEW_PENDING')==GUARD_SHA,'absolute_deadline_unix':w['absolute_deadline_unix'],'closed_unix':time.time(),'whole_original_goal_passed':False,'same_version_three_routes_passed':False,'new24_executed':False,'new24_denominator':None,'old_failures_and_windows_preserved':True,'network_delivery_pending':True};dump(O/'COMPLETION.json',result);report=R/'docs/RPCCR_AFTERNOON_OBSERVER_V1139_REPORT.md';report.write_text('# V1139 afternoon observer components\n\n```json\n'+encode(result)+'```\n\nNormal brake uses original finite2200/fullgeometry/terminal.025/heading.1 contract; parked steering keeps separate.02/.1 envelope. V1138 stays failed. Static speed response is a finite component; observation source is reconstructed from real past controls plus a new stopped prefix. No component/reconstruction is counted as original-goal arrival, three-route or24 acceptance. Fixed deadline14:30 never extended.\n');cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,active_zero_model_diagnostic=None,next_physical_authorized=False,latest_completed=result,latest_report=str(report.relative_to(R)));dump(R/'CURRENT_EXPERIMENT.json',cur)
  with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V1139下午14:30硬截止轮闭：components='+str(passed)+', reason='+reason+', counts='+encode(counts).strip()+'；原goal/同版本三路线/24未完成，报告docs/RPCCR_AFTERNOON_OBSERVER_V1139_REPORT.md。\n')
  files=[]
  for root in [C,O,R/'runs/v858_nav2_verified/v1139']:
   if root.exists():
    for p in root.rglob('*'):
     if p.is_file()and p.name not in ['campaign.console','watchdog.console','LOCAL_MANIFEST.json']and not p.is_symlink():files.append({'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p)})
  files.append({'path':str(report.relative_to(R)),'bytes':report.stat().st_size,'sha256':sha(report)});dump(O/'LOCAL_MANIFEST.json',{'files':files,'readback_verified':all(sha(R/f['path'])==f['sha256']for f in files),'network_delivery_pending':True,'raw_retained':True});print(encode(result),flush=True)
if __name__=='__main__':main()
