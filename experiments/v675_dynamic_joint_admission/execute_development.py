"""One-candidate authorized window, success-only exact repeat, no new scenes."""
import os,time,signal,json,traceback
from pathlib import Path
from bounded_execution import Window,read,dump,digest
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
src=Path(__file__).resolve().parent;repo=src.parents[1];root=repo/'runs/v675_dynamic_joint_admission'
roundpath=repo/'runs/v674_dynamic_renewable_backup/ROUND_WINDOW.json';ledger=read(roundpath)
assert not ledger['round_closed'] and ledger['navigation_attempts']==1 and ledger['candidates_started']==1,'ROUND_CLOSED_OR_DUPLICATE'
assert not (root/'development01').exists(),'NO_DUPLICATE'
assert read(repo/'runs/v671_dynamic_consistency_diagnosis/ROUND_WINDOW.json')['round_closed'],'OLDER_ROUND_ACTIVE'
oldroot=repo/'runs/v674_dynamic_renewable_backup'
validation=read(oldroot/'selection_probe/COMPLETION.json');assert validation['status']=='PASS' and validation['concrete_missed_appendable_commands']>=1
assert validation['replay_native_steps']==1808 and max(validation['maximum_qpos_qvel_mocap_errors'])<=1e-8
assert read(oldroot/'INDEPENDENT_DYNAMIC_AUDIT.json')['status']=='EVIDENCE_AND_EXECUTED_NATIVE_CHECKS_PASS'
assert read(oldroot/'development01/COMPLETION.json')['strict_arrivals_including_repeats']==0
for name in ['reserved_recovery.py','recovery_supervisor.py','motion_tracker.py','union_belief.py','motion_evaluator.py','geometry_predictor.py']:
 assert digest(src/name)==validation['source_sha256'][name],'UNCHANGED_ADMISSION_RULE_CHANGED'
window=Window(src,'v675_dynamic_joint_admission','development01',5400,ledger['absolute_deadline_unix'])
ledger['status']='NAVIGATING_CANDIDATE42';ledger['candidates_started']=2;dump(roundpath,ledger)
results=[];repeats=[];status='RUNNING'
def stop(*_):raise RuntimeError('BOUNDARY_OR_USER_STOP')
signal.signal(signal.SIGTERM,stop)
def run(name):
 assert ledger['navigation_attempts']<4,'ATTEMPT_CAP'
 if window.remaining()<1000:return None
 ledger['navigation_attempts']+=1;dump(roundpath,ledger)
 return window.run(name,95000011,'single_event',mode='predictive',observation_steps=0)
def evaluate(row,audit=True):
 result=window.result(row);safe=window.audit(row)if audit else window.physical[-1]['passed'];pair=root/row['name']/'paired'
 coveragefile=pair/'geometry_memory/forecast_coverage.jsonl';coverage=[json.loads(s)for s in coveragefile.read_text().splitlines()]if coveragefile.exists()else[]
 old=repo/'runs/v669_dynamic_reserved_recovery/dev37_95000011_reserve/paired'
 checks={'physical_audit':safe,'finite_forecast_coverage':bool(result and len(coverage)>=result['public_steps']and all(s['passed']and s['checked_future_samples']==329 for s in coverage)),
 'same_saved_model':read(pair/'STATIC_PROTOCOL.json',{}).get('full_model_sha256')==read(old/'STATIC_PROTOCOL.json')['full_model_sha256'],
 'same_initial_state':bool(result and result['normalized_initial_state_hash']==read(old/'geometry_memory/result.json')['normalized_initial_state_hash'])}
 out={'name':row['name'],'seed':95000011,'result':result,'checks':checks,'passed_evidence':all(checks.values())};results.append(out);dump(window.path/'RESULTS.json',results);return out
try:
 row=run('dev42_95000011_jointadmission')
 if row is None:status='INSUFFICIENT_BUDGET_NO_NAVIGATION'
 else:
  record=evaluate(row)
  if not record['passed_evidence']:status='STOPPED_EVIDENCE_ANOMALY'
  elif not record['result']['strict_safe_arrival']:status='CLOSED_MAIN_NON_SUCCESS'
  else:
   row=run('dev42_95000011_jointadmission_repeat')
   if row is None:status='ARRIVED_REPEAT_NOT_EXECUTED_BUDGET'
   else:
    repeat=window.repeat(row,root/'dev42_95000011_jointadmission/paired');repeats.append(repeat);dump(window.path/'REPEAT_AUDIT.json',repeats);record=evaluate(row,False)
    status='SAME_DEVELOPMENT_ARRIVAL_AND_REPEAT_PASS'if repeat['matched']and record['passed_evidence']else'STOPPED_REPEAT_OR_EVIDENCE_ANOMALY'
except BaseException as e:
 status='STOPPED_EXCEPTION';dump(window.path/'ERROR.json',{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
finally:
 final={'status':status,'elapsed_s':time.monotonic()-window.started,'round_elapsed_s':time.time()-ledger['started_unix'],'absolute_deadline_unix':ledger['absolute_deadline_unix'],'executed_branches':len(results),'strict_arrivals_including_repeats':sum(bool(x['result']and x['result']['strict_safe_arrival'])for x in results),'distinct_executed_development_tasks':int(bool(results)),'conditional_repeat_attempted':bool(repeats),'independent_confirmation_tasks':0,'dynamic_stability_acceptance_passed':False,'training_updates':0,'automatic_next_revision_started':False}
 dump(window.path/'COMPLETION.json',final);dump(window.path/'ACTIVE.json',{'status':status,'completed':True});ledger.update(status='CANDIDATE42_'+status,last_completion=final,round_closed=True);dump(roundpath,ledger);print('V675_COMPLETE',status,flush=True)
