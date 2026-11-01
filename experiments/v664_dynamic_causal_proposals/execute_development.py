"""One registered causal-proposal candidate and success-dependent exact repeat."""
import os,signal,time,traceback,json
from pathlib import Path
from bounded_execution import Window,read,dump,digest
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
src=Path(__file__).resolve().parent;repo=src.parents[1]
deadline=1793502431.7726939
window=Window(src,'v664_dynamic_causal_proposals','development01',3600,deadline)
status='RUNNING';outcomes=[];repeats=[]
old=repo/'runs/v663_dynamic_interval_tracking/dev33_95000011_observe0/paired'
def stop(*_):raise RuntimeError('BOUNDARY_OR_USER_STOP')
signal.signal(signal.SIGTERM,stop)
def evaluate(row):
 result=window.result(row);safe=window.audit(row)
 pair=window.root/row['name']/'paired'
 coverage=[json.loads(s)for s in (pair/'geometry_memory/forecast_coverage.jsonl').read_text().splitlines()] if (pair/'geometry_memory/forecast_coverage.jsonl').exists() else []
 checks={'physical_audit':safe,'forecast_coverage':bool(result and coverage and len(coverage)>=result['public_steps'] and all(x['passed']for x in coverage)),
 'same_model':read(old/'STATIC_PROTOCOL.json')['full_model_sha256']==read(pair/'STATIC_PROTOCOL.json')['full_model_sha256'],
 'same_normalized_initial_state':bool(result and result['normalized_initial_state_hash']==read(old/'geometry_memory/result.json')['normalized_initial_state_hash'])}
 return {'name':row['name'],'result':result,'passed_evidence':all(checks.values()),'checks':checks}
try:
 assert read(repo/'runs/v663_dynamic_interval_tracking/INDEPENDENT_DYNAMIC_AUDIT.json')['status']=='EVIDENCE_AND_EXECUTED_NATIVE_CHECKS_PASS'
 diagnosis=read(repo/'runs/v663_dynamic_interval_tracking/OFFLINE_ROUTE_PROJECTION_DIAGNOSIS.json')
 assert diagnosis['results'][0]['path'] is None and diagnosis['results'][1]['stats']['status']=='GLOBAL_GOAL_PATH'
 assert digest(src/'motion_tracker.py')==digest(repo/'experiments/v663_dynamic_interval_tracking/motion_tracker.py')
 row=window.run('dev34_95000011_proposal',95000011,'single_event',mode='predictive',observation_steps=0)
 if row is None:status='BUDGET_NOT_STARTED'
 else:
  first=evaluate(row);outcomes.append(first);dump(window.path/'RESULTS.json',outcomes)
  if not first['passed_evidence']:status='STOPPED_EVIDENCE_ANOMALY'
  elif not first['result']['strict_safe_arrival']:status='CLOSED_NAVIGATION_NON_SUCCESS'
  else:
   row=window.run('dev34_95000011_proposal_repeat',95000011,'single_event',mode='predictive',observation_steps=0)
   if row is None:status='ARRIVED_REPEAT_NOT_EXECUTED_BUDGET'
   else:
    second=evaluate(row);outcomes.append(second);dump(window.path/'RESULTS.json',outcomes)
    repeat=window.repeat(row,window.root/'dev34_95000011_proposal/paired');repeats.append(repeat);dump(window.path/'REPEAT_AUDIT.json',repeats)
    status='DEVELOPMENT_ARRIVAL_AND_REPEAT_PASS'if second['passed_evidence'] and repeat['matched'] else 'STOPPED_REPEAT_OR_EVIDENCE_FAILURE'
except BaseException as error:
 status='STOPPED_EXCEPTION';dump(window.path/'ERROR.json',{'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
finally:
 final={'status':status,'elapsed_s':time.monotonic()-window.started,'absolute_deadline_unix':deadline,'new_navigation_branches':min(1,len(outcomes)),
 'executed_branches_including_repeat':len(outcomes),'strict_arrivals_including_repeats':sum(bool(x['result'] and x['result']['strict_safe_arrival'])for x in outcomes),
 'conditional_repeat_attempted':bool(repeats),'distinct_development_tasks':1 if outcomes else 0,'independent_confirmation_tasks':0,'dynamic_stability_acceptance_passed':False,'training_updates':0,'automatic_further_revision_started':False}
 dump(window.path/'COMPLETION.json',final);dump(window.path/'ACTIVE.json',{'status':status,'completed':True});dump(window.root/'FINAL_BUDGET_ACCOUNT.json',final)
 print('DYNAMIC_PROPOSAL_COMPLETE',status,flush=True)
