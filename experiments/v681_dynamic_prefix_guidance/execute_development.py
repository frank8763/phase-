"""One-candidate authorized window, success-only exact repeat, no new scenes."""
import os,time,signal,json,traceback
from pathlib import Path
from bounded_execution import Window,read,dump,digest
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
src=Path(__file__).resolve().parent;repo=src.parents[1];root=repo/'runs/v681_dynamic_prefix_guidance'
roundpath=repo/'runs/v679_dynamic_forward_reserve/ROUND_WINDOW.json';ledger=read(roundpath)
assert not ledger['round_closed'] and ledger['navigation_attempts']==1 and ledger['algorithm_candidates_started']==1,'ROUND_CLOSED_OR_DUPLICATE'
assert not (root/'development02').exists(),'NO_DUPLICATE'
assert read(repo/'runs/v671_dynamic_consistency_diagnosis/ROUND_WINDOW.json')['round_closed'],'OLDER_ROUND_ACTIVE'
validation=read(root/'PRE_NAV_VALIDATION.json');assert validation['status']=='PASS' and validation['packets']==804
assert validation['simulation_integrations']==0 and validation['maximum_joint_cell_outside_projection_m']<=1e-8
for name in ['reserved_recovery.py','actuator_commands.py','serial_predictor.py','geometry_predictor.py','run_static.py','future_guide.py','planner.py','motion_tracker.py']:
 assert digest(src/name)==validation['source_sha256'][name],'VALIDATED_SOURCE_CHANGED'
assert read(repo/'runs/v680_dynamic_later_stop_reserve/development01/COMPLETION.json')['status']=='CLOSED_MAIN_NON_SUCCESS'
assert read(repo/'runs/v676_dynamic_canonical_commands/ROUND_WINDOW.json')['round_closed'],'PREVIOUS_ROUND_ACTIVE'
window=Window(src,'v681_dynamic_prefix_guidance','development02',7200,ledger['absolute_deadline_unix'])
ledger['status']='NAVIGATING_CANDIDATE48';ledger['algorithm_candidates_started']=2;dump(roundpath,ledger)
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
 auxiliary=repo/'experiments/v649_static_stability/audit_dynamic_later_stop_run.py'
 assert digest(auxiliary)==read(root/'AUDITOR_FREEZE.json')['sha256'],'INDEPENDENT_AUDITOR_CHANGED'
 independent_code=window.execute([str(repo/'run_phase.sh'),str(auxiliary.relative_to(repo)),str(pair),'--window',str(window.path)],pair/'independent_canonical.console',45)
 checks['independent_raw_state_command_audit']=independent_code==0 and read(pair/'INDEPENDENT_CANONICAL_AUDIT.json',{}).get('status')=='ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS'
 for helper,filename,wanted in [('audit_later_stop_certificate_geometry.py','SAVED_TAIL_GEOMETRY_AUDIT.json','ALL_SAVED_TAIL_GEOMETRY_DIRECTION_SCHEDULE_PASS'),('audit_prefix_route_geometry.py','PREFIX_ROUTE_AUDIT.json','ALL_CAUSAL_PREFIX_ROUTE_PROJECTIONS_PASS')]:
  auxiliary=repo/'experiments/v649_static_stability'/helper
  assert digest(auxiliary)==read(root/'ADDITIONAL_AUDITORS_FREEZE.json')[helper],'ADDITIONAL_AUDITOR_CHANGED'
  code=window.execute([str(repo/'run_phase.sh'),str(auxiliary.relative_to(repo)),str(pair)],pair/(helper+'.console'),45)
  checks[filename]=code==0 and read(pair/filename,{}).get('status')==wanted
 out={'name':row['name'],'seed':95000011,'result':result,'checks':checks,'passed_evidence':all(checks.values())};results.append(out);dump(window.path/'RESULTS.json',results);return out
try:
 row=run('dev48_95000011_prefix')
 if row is None:status='INSUFFICIENT_BUDGET_NO_NAVIGATION'
 else:
  record=evaluate(row)
  if not record['passed_evidence']:status='STOPPED_EVIDENCE_ANOMALY'
  elif not record['result']['strict_safe_arrival']:status='CLOSED_MAIN_NON_SUCCESS'
  else:
   ledger['conditional_repeat_attempts']+=1;dump(roundpath,ledger)
   row=run('dev48_95000011_prefix_repeat')
   if row is None:status='ARRIVED_REPEAT_NOT_EXECUTED_BUDGET'
   else:
    repeat=window.repeat(row,root/'dev48_95000011_prefix/paired');repeats.append(repeat);dump(window.path/'REPEAT_AUDIT.json',repeats);record=evaluate(row,False)
    status='SAME_DEVELOPMENT_ARRIVAL_AND_REPEAT_PASS'if repeat['matched']and record['passed_evidence']else'STOPPED_REPEAT_OR_EVIDENCE_ANOMALY'
except BaseException as e:
 status='STOPPED_EXCEPTION';dump(window.path/'ERROR.json',{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
finally:
 final={'status':status,'elapsed_s':time.monotonic()-window.started,'round_elapsed_s':time.time()-ledger['started_unix'],'absolute_deadline_unix':ledger['absolute_deadline_unix'],'executed_branches':len(results),'strict_arrivals_including_repeats':sum(bool(x['result']and x['result']['strict_safe_arrival'])for x in results),'distinct_executed_development_tasks':int(bool(results)),'conditional_repeat_attempted':bool(repeats),'independent_confirmation_tasks':0,'dynamic_stability_acceptance_passed':False,'training_updates':0,'automatic_next_revision_started':False}
 dump(window.path/'COMPLETION.json',final);dump(window.path/'ACTIVE.json',{'status':status,'completed':True});ledger.update(status='CANDIDATE48_'+status,last_completion=final,round_closed=True);dump(roundpath,ledger);print('V681_COMPLETE',status,flush=True)
