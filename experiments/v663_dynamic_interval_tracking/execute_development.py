"""Frozen same-task observation ablation, charged to original V662 window."""
import os,signal,time,traceback
from pathlib import Path
from bounded_execution import Window,read,dump,digest
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
src=Path(__file__).resolve().parent;repo=src.parents[1]
origin=read(repo/'runs/v662_dynamic_sensor_diagnosis/diagnosis01/WINDOW.json')
window=Window(src,'v663_dynamic_interval_tracking','development01',3600,origin['absolute_deadline_unix'])
outcomes=[];repeat=[];status='INTERVAL_OBSERVATION_ABLATION_RUNNING';base=None
ledger_path=repo/'runs/v662_dynamic_sensor_diagnosis/ROUND_LEDGER.json'
ledger=read(ledger_path);ledger.update(status=status,development_revisions=1,active_window=str(window.path.relative_to(repo)));dump(ledger_path,ledger)
def stop(*_):raise RuntimeError('BOUNDARY_OR_USER_STOP')
signal.signal(signal.SIGTERM,stop)
try:
 validation=read(window.root/'OFFLINE_PACKET_VALIDATION.json')
 assert validation['status']=='PASS'and validation['tracker_sha256']==digest(src/'motion_tracker.py'),'OFFLINE_VALIDATION_OR_SOURCE_CHANGED'
 assert read(repo/'runs/v662_dynamic_sensor_diagnosis/diagnosis01/DIAGNOSTIC_AUDIT.json')['passed'],'DIAGNOSTIC_DEPENDENCY_FAILED'
 for name,observation in [('dev33_95000011_observe32',32),('dev33_95000011_observe0',0)]:
  row=window.run(name,95000011,'single_event',mode='predictive',observation_steps=observation)
  if row is None:status='NAVIGATION_BUDGET_INCOMPLETE';break
  result=window.result(row);safe=window.audit(row)
  pair=window.root/name/'paired';coverage=[]
  f=pair/'geometry_memory/forecast_coverage.jsonl'
  if f.exists():
   import json
   coverage=[json.loads(s)for s in f.read_text().splitlines()]
  coverage_pass=bool(result and coverage and all(x['passed']for x in coverage)and len(coverage)>=result['public_steps'])
  if base is None:base=pair
  pairing={'model':read(base/'STATIC_PROTOCOL.json')['full_model_sha256']==read(pair/'STATIC_PROTOCOL.json')['full_model_sha256'],
           'initial_state':bool(result and result['normalized_initial_state_hash']==read(base/'geometry_memory/result.json')['normalized_initial_state_hash'])}
  record={'name':name,'initial_observation_steps':observation,'result':result,'physical_audit_passed':safe,'coverage_passed':coverage_pass,'pairing':pairing}
  outcomes.append(record);dump(window.path/'RESULTS.json',outcomes)
  ledger.update(new_navigation_branches=len(outcomes));dump(ledger_path,ledger)
  if not safe or not coverage_pass or not all(pairing.values()):status='STOPPED_SAFETY_COVERAGE_OR_PAIRING';break
 else:
  status='OBSERVATION_ABLATION_COMPLETED'
  if outcomes[0]['result']['strict_safe_arrival']:
   row=window.run('dev33_95000011_observe32_repeat',95000011,'single_event',mode='predictive',observation_steps=32)
   if row is None:status='REPEAT_BUDGET_INCOMPLETE'
   else:
    record=window.repeat(row,base);repeat.append(record);dump(window.path/'REPEAT_AUDIT.json',repeat)
    status='MAIN_REPEAT_MATCHED'if record['matched']else'MAIN_REPEAT_FAILED'
except BaseException as error:
 status='STOPPED_EXCEPTION';dump(window.path/'ERROR.json',{'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
finally:
 final={'status':status,'elapsed_s':time.monotonic()-window.started,'original_deadline_unix':origin['absolute_deadline_unix'],'new_navigation_branches':len(outcomes),'conditional_repeat_attempted':bool(repeat),'distinct_development_tasks':1,'independent_confirmation_tasks':0,'dynamic_stability_acceptance_passed':False,'training_updates':0,'automatic_revision02_started':False}
 dump(window.path/'COMPLETION.json',final);dump(window.path/'ACTIVE.json',{'status':status,'completed':True})
 ledger.update(status=status,round_closed=True,charged_round_elapsed_s=time.time()-origin['started_unix'],conditional_repeat_attempted=bool(repeat));dump(ledger_path,ledger)
 print('DYNAMIC_INTERVAL_DEVELOPMENT_COMPLETE',status,flush=True)
