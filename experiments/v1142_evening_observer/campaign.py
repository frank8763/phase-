"""Gated offline physical observation pair and measurement-derived goal software."""
import sys,os,signal,subprocess,time,fcntl,traceback,shutil
from evening_tools import *

def compare_repeats(a,b):
 import numpy as np
 a=Path(a);b=Path(b);aa=np.load(a/'physics/NATIVE_TRACE.npz');bb=np.load(b/'physics/NATIVE_TRACE.npz');maximum=0.;shape=True
 for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
  shape&=aa[k].shape==bb[k].shape
  if shape and aa[k].size:maximum=max(maximum,float(abs(aa[k]-bb[k]).max()))
 import gzip
 ca=json.loads(gzip.open(a/'physics/CONTACTS.json.gz','rt').read());cb=json.loads(gzip.open(b/'physics/CONTACTS.json.gz','rt').read());sensor_a=json.loads(gzip.open(a/'physics/SENSORS.json.gz','rt').read());sensor_b=json.loads(gzip.open(b/'physics/SENSORS.json.gz','rt').read());ra=json.loads((a/'RESULT.json').read_text());rb=json.loads((b/'RESULT.json').read_text());model=sha(a/'physics/scene_model.mjb')==sha(b/'physics/scene_model.mjb');initial=sha(a/'physics/INITIAL_STATE.npz')==sha(b/'physics/INITIAL_STATE.npz');discovery=ra['physical']['first_actor_detection']==rb['physical']['first_actor_detection'];passed=shape and maximum<=1e-8 and ca==cb and sensor_a==sensor_b and model and initial and discovery
 return {'passed':bool(passed),'same_complete_length':shape,'maximum_qpos_qvel_ctrl_mocap_error':maximum,'model_same':model,'initial_same':initial,'contacts_same':ca==cb,'actual_sensor_packets_same':sensor_a==sensor_b,'actual_discovery_same':discovery}

def main():
 assert not(O/'DRIVER_STARTED.json').exists();lock=(O/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard=(O/'GUARD.bin').read_bytes();assert sha(R/'REVIEW_PENDING')==GUARD_SHA and source_ok();w=json.loads((O/'ROUND_WINDOW.json').read_text());dump(O/'DRIVER_STARTED.json',{'pid':os.getpid(),'proc_start':Path('/proc/self/stat').read_text().split()[21]});child=None;rows=[];attempts=[];error=None;reason='FINITE_GATED_QUEUE_COMPLETE';winner=None;repeat=None;physical_pass=False
 def stop():
  nonlocal child
  if child and child.poll()is None:
   try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=5)
   except BaseException:
    try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
    except ProcessLookupError:pass
  child=None
 def halt(*_):raise TimeoutError('ABSOLUTE_2100_STOP')
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,remaining()))
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
  assert json.loads((O/'ENTRY_QUALIFICATION.json').read_text())['passed'];assert json.loads((O/'OBSERVER_AUDIT_QUALIFICATION.json').read_text())['passed'];reuse=json.loads((O/'REUSED_GATES.json').read_text());assert reuse['passed'];dump(O/'RESULTS.json',rows)
  tasks=json.loads((C/'TASKS.json').read_text())
  for task in tasks:
   attempts.append(task);dump(O/'ATTEMPTS.json',attempts);code=job(task['task_id'],'observer_worker.py',[C/('TASK_'+task['task_id']+'.json')],1000,True);f=Path(task['output'])/'RESULT.json';r=json.loads(f.read_text())if f.exists()else{'passed':False,'missing_result':True};row={'stage':task['task_id'],'returncode':code,'result':r};rows.append(row);dump(O/'RESULTS.json',rows)
   if r.get('evidence_saved')and r.get('new_actual_native',0):
    acode=job(task['task_id']+'_audit','observer_audit.py',[C/('TASK_'+task['task_id']+'.json')],300);f=Path(task['output'])/'FINAL_INDEPENDENT_AUDIT.json';row['audit']=json.loads(f.read_text())if f.exists()else{'passed':False,'missing_audit':True};row['audit_returncode']=acode;dump(O/'RESULTS.json',rows)
   if code!=0 or not r['passed']or not row.get('audit',{}).get('passed'):reason='FIRST_PHYSICAL_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE';return
  repeat=compare_repeats(tasks[0]['output'],tasks[1]['output']);dump(O/'COMPLETE_REPEAT.json',repeat);assert repeat['passed'],'FULL_OBSERVER_REPEAT_MISMATCH';physical_pass=True
  code=job('actual_measurement_source','post_observation.py',[],650);f=O/'post_observation/RESULT.json';post=json.loads(f.read_text())if f.exists()else{'passed':False,'missing_result':True};rows.append({'stage':'actual_measurement_source','returncode':code,'result':post});dump(O/'RESULTS.json',rows);assert code==0 and post['passed'],'ACTUAL_MEASUREMENT_OR_SOURCE_EVIDENCE_ERROR'
  for name,speed in [('goal_v80',.08),('goal_v120',.12)]:
   if remaining()<1900:reason='ROOT_TIME_RESERVE';break
   out=O/name;file=O/(name+'.json');dump(file,{'output':str(out),'speed':speed});code=job(name,'goal_source.py',[file],1850);f=out/'RESULT.json';r=json.loads(f.read_text())if f.exists()else{'passed':False,'missing_result':True};rows.append({'stage':name,'returncode':code,'result':r});dump(O/'RESULTS.json',rows);assert code==0 and r.get('error')is None,'GOAL_SOURCE_OPERATION_OR_EVIDENCE_ERROR'
   if r['passed']:
    winner={'profile':name,'speed':speed,'source':str(out),'result':r};selected=O/'selected_goal';selected.mkdir()
    for n in ['SOURCE.npz','SOURCE_PROOF.json','ROWS.json','ALL8_BACKUPS.json','RESULT.json']:os.link(out/n,selected/n)
    break
 except BaseException as e:error={'error':repr(e),'traceback':traceback.format_exc()};reason='EXCEPTION_OR_DEADLINE';dump(O/'ERROR.json',error)
 finally:
  stop();(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',{'models_authorized':False,'closed':True});dump(O/'ACTIVE.json',{'closed':True});signal.setitimer(signal.ITIMER_REAL,0)
  physical=[r for r in rows if r['stage']in ['observation_main','observation_repeat']];keys=['vehicle_initializations','new_actual_native','own_replay_native','replay_state_initializations','private_mujoco_native','training_updates','analytical_prediction_native','historical_reconstruction_native','new_observer_component_native'];counts={k:sum(r['result'][k]for r in physical)if len(physical)==len(attempts)and all(r['result'].get(k)is not None for r in physical)else None for k in keys};result={'closed':True,'physical_observer_main_and_repeat_passed':physical_pass,'goal_software_source_and_all8_passed':winner is not None,'winner':winner,'stop_reason':reason,'error':error,'attempted':[t['task_id']for t in attempts],'unexecuted':[t['task_id']for t in json.loads((C/'TASKS.json').read_text())if t not in attempts],'physical_counts':counts,'results':rows,'complete_repeat':repeat,'source_unchanged':source_ok(),'guard_original':sha(R/'REVIEW_PENDING')==GUARD_SHA,'absolute_deadline_unix':w['absolute_deadline_unix'],'closed_unix':time.time(),'original_goal_physical_arrival_passed':False,'same_version_three_route_passed':False,'new24_executed':False,'new24_denominator':None,'reused_previous_speed_and_software_gates_counted_separately':True,'network_delivery_pending':True};dump(O/'COMPLETION.json',result);report=R/'docs/RPCCR_EVENING_OBSERVER_V1142_REPORT.md';report.write_text('# V1142 evening observation and goal-source relay\n\n```json\n'+encode(result)+'```\n\nNew absolute deadline2026-11-14 21:00+0800. Old failures/windows unchanged. Historical reconstructions are counted actual integrations, not independent route samples. An observation/refuge component or software goal source is not original-goal physical arrival/three-route/fixed24 acceptance. Source construction uses actual corrupted range packets only; no trueactor position/axis/phase/evaluator attribution. Two static speed response gates and1564 software backups are reused with SHA evidence, never counted as new trials.\n');cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,active_zero_model_diagnostic=None,next_physical_authorized=False,latest_completed=result,latest_report=str(report.relative_to(R)));dump(R/'CURRENT_EXPERIMENT.json',cur)
  with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V1142晚21:00轮闭：observer_main_repeat='+str(physical_pass)+', goal_software='+str(winner is not None)+', reason='+reason+', counts='+encode(counts).strip()+'；原goal物理/同版本三路线/24未完成；docs/RPCCR_EVENING_OBSERVER_V1142_REPORT.md。\n')
  files=[]
  for root in [C,O,R/'runs/v858_nav2_verified/v1142']:
   if root.exists():
    for p in root.rglob('*'):
     if p.is_file()and p.name not in ['campaign.console','watchdog.console','LOCAL_MANIFEST.json']and not p.is_symlink():files.append({'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p)})
  files.append({'path':str(report.relative_to(R)),'bytes':report.stat().st_size,'sha256':sha(report)});dump(O/'LOCAL_MANIFEST.json',{'files':files,'readback_verified':all(sha(R/f['path'])==f['sha256']for f in files),'network_delivery_pending':True,'raw_retained':True});print(encode(result),flush=True)
if __name__=='__main__':main()
