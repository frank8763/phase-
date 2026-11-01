"""Bounded new dynamic round, frozen candidate, conditional development expansion."""
import os,signal,time,traceback,json
from pathlib import Path
from bounded_execution import Window,read,dump,digest
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
src=Path(__file__).resolve().parent;repo=src.parents[1]
root=repo/'runs/v669_dynamic_reserved_recovery';root.mkdir(exist_ok=True)
round_path=repo/'runs/v666_dynamic_dense_navigation/ROUND_WINDOW.json'
round_ledger=read(round_path)
assert round_ledger['development_candidates']==2 and round_ledger['navigation_attempts']==2 and not round_ledger['round_closed'],'ROUND_DEPENDENCY_OR_DUPLICATE'
assert read(repo/'runs/v667_dynamic_first_hit/INDEPENDENT_DYNAMIC_AUDIT.json')['status']=='EVIDENCE_AND_EXECUTED_NATIVE_CHECKS_PASS'
assert not (root/'development03').exists(),'NO_DUPLICATE_CANDIDATE'
deadline=round_ledger['absolute_deadline_unix'];assert deadline-time.time()>1000
validation=read(root/'pre_nav_retry02/PRE_NAV_DIAGNOSTIC.json')
assert validation['status']=='COMPLETE_FIXED_GRID' and validation['error'] is None
assert validation['private_contract_replay_checks'] and all(x['all_public_full_states_match']for x in validation['private_contract_replay_checks'])
freeze=read(root/'pre_nav_retry02/SOURCE_FREEZE.json')
for name in ['reserved_recovery.py','geometry_predictor.py','motion_tracker.py']:
 assert digest(src/name)==freeze[str((src/name).relative_to(repo))],'VALIDATED_CONTROL_COMPONENT_CHANGED'
round_ledger.update(status='RUNNING_CANDIDATE37',development_candidates=3)
dump(round_path,round_ledger)
window=Window(src,'v669_dynamic_reserved_recovery','development03',7200,deadline)
status='RUNNING';outcomes=[];repeats=[]
old=repo/'runs/v664_dynamic_causal_proposals/dev34_95000011_proposal/paired'
def stop(*_):raise RuntimeError('BOUNDARY_OR_USER_STOP')
signal.signal(signal.SIGTERM,stop)
def run(name,seed,feasibility=False):
 key='preflight_attempts'if feasibility else'navigation_attempts';cap=2 if feasibility else 6
 if round_ledger[key]>=cap:return None
 round_ledger[key]+=1;round_ledger['attempts'].append({'name':name,'seed':seed,'feasibility_only':feasibility,'started_unix':time.time()});dump(round_path,round_ledger)
 return window.run(name,seed,'single_event',mode='predictive',observation_steps=0,feasibility=feasibility)
def evaluate(row,run_audit=True):
 result=window.result(row);safe=window.audit(row)if run_audit else next((r['passed']for r in reversed(window.physical)if r['name']==row['name']),False)
 pair=window.root/row['name']/'paired';f=pair/'geometry_memory/forecast_coverage.jsonl'
 coverage=[json.loads(s)for s in f.read_text().splitlines()]if f.exists()else[]
 checks={'physical_audit':safe,'forecast_coverage':bool(result and coverage and len(coverage)>=result['public_steps']and all(x['passed']for x in coverage))}
 if row['seed']==95000011:
  checks.update(same_model=read(old/'STATIC_PROTOCOL.json')['full_model_sha256']==read(pair/'STATIC_PROTOCOL.json')['full_model_sha256'],same_normalized_initial_state=bool(result and result['normalized_initial_state_hash']==read(old/'geometry_memory/result.json')['normalized_initial_state_hash']))
 return {'name':row['name'],'seed':row['seed'],'result':result,'passed_evidence':all(checks.values()),'checks':checks}
def append(record):
 outcomes.append(record);dump(window.path/'RESULTS.json',outcomes)
try:
 assert read(repo/'runs/v665_dynamic_dense_edges/INDEPENDENT_OFFLINE_CHECK.json')['status']=='ZERO_INTEGRATION_SAVED_INPUT_CHECKS_PASS'
 assert digest(src/'planner.py')==digest(repo/'experiments/v665_dynamic_dense_edges/planner.py')
 assert digest(src/'task_planner.py')==digest(repo/'experiments/v664_dynamic_causal_proposals/planner.py')
 row=run('dev37_95000011_reserve',95000011)
 if row is None:status='BUDGET_NOT_STARTED'
 else:
  first=evaluate(row);append(first)
  if not first['passed_evidence']:status='STOPPED_EVIDENCE_ANOMALY'
  elif not first['result']['strict_safe_arrival']:status='CLOSED_MAIN_NON_SUCCESS'
  else:
   row=run('dev37_95000011_reserve_repeat',95000011)
   if row is None:status='ARRIVED_REPEAT_NOT_EXECUTED_BUDGET'
   else:
    repeat=window.repeat(row,window.root/'dev37_95000011_reserve/paired');repeats.append(repeat);dump(window.path/'REPEAT_AUDIT.json',repeats)
    second=evaluate(row,False);append(second)
    if not second['passed_evidence']or not repeat['matched']:status='STOPPED_REPEAT_OR_EVIDENCE_FAILURE'
    else:
     status='ARRIVAL_REPEAT_PASS_EXPANSION'
     for seed in [95000039,95000053]:
      pre=run(f'dev37_preflight_{seed}',seed,True)
      if pre is None:status='EXPANSION_BUDGET_INCOMPLETE';break
      if pre['returncode']!=0 or not(pre.get('feasibility')or{}).get('eligible'):
       dump(window.path/f'UNEXECUTED_{seed}.json',{'status':'PREREGISTERED_SCENE_NOT_CERTIFIED_NO_REPLACEMENT','seed':seed,'preflight':pre});continue
      row=run(f'dev37_{seed}_reserve',seed)
      if row is None:status='EXPANSION_BUDGET_INCOMPLETE';break
      record=evaluate(row);append(record)
      if not record['passed_evidence']:status='STOPPED_EXPANSION_EVIDENCE_ANOMALY';break
     else:status='CONDITIONAL_DEVELOPMENT_EXPANSION_COMPLETED'
except BaseException as error:
 status='STOPPED_EXCEPTION';dump(window.path/'ERROR.json',{'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
finally:
 final={'status':status,'elapsed_s':time.monotonic()-window.started,'absolute_deadline_unix':deadline,'executed_branches':len(outcomes),'strict_arrivals_including_repeats':sum(bool(x['result']and x['result']['strict_safe_arrival'])for x in outcomes),'distinct_executed_development_tasks':len(set(x['seed']for x in outcomes)),'conditional_repeat_attempted':bool(repeats),'independent_confirmation_tasks':0,'dynamic_stability_acceptance_passed':False,'training_updates':0,'automatic_next_revision_started':False}
 dump(window.path/'COMPLETION.json',final);dump(window.path/'ACTIVE.json',{'status':status,'completed':True})
 round_ledger.update(status=status,last_completion=final,round_closed=True);dump(round_path,round_ledger)
 print('DYNAMIC_RESERVED_RECOVERY_COMPLETE',status,flush=True)
