"""Bounded current-information diagnostic and success-only full repeat."""
import os,time,signal,json,traceback
from pathlib import Path
from bounded_execution import Window,read,dump,digest
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});src=Path(__file__).resolve().parent;repo=src.parents[1];root=repo/'runs/v683_dynamic_current_state_diagnosis';roundpath=root/'ROUND_WINDOW.json';ledger=read(roundpath)
assert not ledger['round_closed']and ledger['privileged_navigation_branches']==0 and not(root/'diagnosis01').exists(),'CLOSED_OR_DUPLICATE'
assert read(repo/'runs/v679_dynamic_forward_reserve/ROUND_WINDOW.json')['round_closed'],'OLDER_ROUND_ACTIVE'
validation=read(root/'PRE_NAV_VALIDATION.json');assert validation['status']=='PASS'and validation['checked_instants']==804 and validation['robot_integrations']==0
for name in ['run_static.py','current_state_oracle.py','planner.py','serial_predictor.py','motion_tracker.py','reserved_recovery.py','recovery_supervisor.py','bounded_execution.py','motion_evaluator.py']:
 assert digest(src/name)==validation['source_sha256'][name],'VALIDATED_SOURCE_CHANGED'
window=Window(src,'v683_dynamic_current_state_diagnosis','diagnosis01',7200,ledger['absolute_deadline_unix']);ledger['status']='NAVIGATING_ORACLE_CURRENT_STATE_ONLY';dump(roundpath,ledger);results=[];repeats=[];status='RUNNING'
def stop(*_):raise RuntimeError('BOUNDARY_OR_USER_STOP')
signal.signal(signal.SIGTERM,stop)
def run(name):
 assert ledger['privileged_navigation_branches']<2
 if window.remaining()<1100:return None
 ledger['privileged_navigation_branches']+=1;dump(roundpath,ledger);return window.run(name,95000011,'single_event',mode='predictive',observation_steps=0)
def evaluate(row,audit=True):
 result=window.result(row);safe=window.audit(row)if audit else window.physical[-1]['passed'];pair=root/row['name']/'paired';old=repo/'runs/v680_dynamic_later_stop_reserve/dev47_95000011_laterstop/paired';checks={'physical_audit':safe,'same_saved_model':read(pair/'STATIC_PROTOCOL.json',{}).get('full_model_sha256')==read(old/'STATIC_PROTOCOL.json')['full_model_sha256'],'same_initial_state':bool(result and result['normalized_initial_state_hash']==read(old/'geometry_memory/result.json')['normalized_initial_state_hash'])}
 for helper,filename,wanted in [('audit_dynamic_current_state_run.py','INDEPENDENT_CANONICAL_AUDIT.json','ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS'),('audit_current_state_tail_geometry.py','SAVED_TAIL_GEOMETRY_AUDIT.json','ALL_SAVED_TAIL_GEOMETRY_DIRECTION_SCHEDULE_PASS'),('audit_current_state_information.py','CURRENT_STATE_INFORMATION_AUDIT.json','ALL_CURRENT_STATE_INFORMATION_CHECKS_PASS')]:
  auxiliary=repo/'experiments/v649_static_stability'/helper;assert digest(auxiliary)==read(root/'AUDITORS_FREEZE.json')[helper],'AUDITOR_CHANGED';args=[str(repo/'run_phase.sh'),str(auxiliary.relative_to(repo)),str(pair)]
  if helper=='audit_dynamic_current_state_run.py':args+=['--window',str(window.path)]
  code=window.execute(args,pair/(helper+'.console'),60);checks[filename]=code==0 and read(pair/filename,{}).get('status')==wanted
 out={'name':row['name'],'result':result,'checks':checks,'passed_evidence':all(checks.values()),'information_role':'ORACLE_CURRENT_STATE_ONLY','counts_as_unknown_dynamic_success':False};results.append(out);dump(window.path/'RESULTS.json',results);return out
try:
 row=run('diagnosis49_95000011_currentstate')
 if row is None:status='INSUFFICIENT_BUDGET_NO_NAVIGATION'
 else:
  record=evaluate(row)
  if not record['passed_evidence']:status='STOPPED_EVIDENCE_ANOMALY'
  elif not record['result']['strict_safe_arrival']:status='ORACLE_CURRENT_STATE_NON_ARRIVAL'
  else:
   row=run('diagnosis49_95000011_currentstate_repeat')
   if row is None:status='ORACLE_ARRIVAL_REPEAT_NOT_EXECUTED_BUDGET'
   else:
    repeat=window.repeat(row,root/'diagnosis49_95000011_currentstate/paired');repeats.append(repeat);dump(window.path/'REPEAT_AUDIT.json',repeats);record=evaluate(row,False);status='ORACLE_CURRENT_STATE_ARRIVAL_AND_REPEAT_PASS'if repeat['matched']and record['passed_evidence']else'STOPPED_REPEAT_OR_EVIDENCE_ANOMALY'
except BaseException as e:status='STOPPED_EXCEPTION';dump(window.path/'ERROR.json',{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
finally:
 final={'status':status,'elapsed_s':time.monotonic()-window.started,'original_round_deadline_unix':ledger['absolute_deadline_unix'],'executed_branches':len(results),'privileged_strict_arrivals_including_repeat':sum(bool(x['result']and x['result']['strict_safe_arrival'])for x in results),'information_role':'ORACLE_CURRENT_STATE_ONLY','counts_as_unknown_dynamic_success':False,'dynamic_acceptance_passed':False,'training_updates':0,'automatic_next_revision_started':False};dump(window.path/'COMPLETION.json',final);dump(window.path/'ACTIVE.json',{'completed':True,'status':status});ledger.update(status='DIAGNOSIS_'+status,last_completion=final,round_closed=status.startswith('STOPPED_'));dump(roundpath,ledger);print('V683_DIAGNOSIS_COMPLETE',status,flush=True)
