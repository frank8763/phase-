import json,hashlib,math,signal,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
f=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in f.items());assert(repo/'REVIEW_PENDING').exists()
assert read(repo/'runs/v765_observation_progress_cycle_audit/RESULT.json')['status']=='OBSERVATION_PROGRESS_CYCLE_SAVED_EVIDENCE_VERIFIED'
start=time.time();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V766_600S_STOP')));signal.alarm(600)
b=read(repo/'runs/v764_observation_progress_cycle/FEEDBACK_MAIN_SUMMARY.json');rows=[]
for d in b['decisions']:
 sweep=d['selection_evidence'].get('actual_scan_range_rad',0.);valid=[c for c in d['candidates']if c['admissible']and c['goal_progress_m']>=.05 and sum(c['target'][2:])>=2.];best=sorted(valid,key=lambda c:(-c['goal_progress_m'],-c['minimum_causal_clearance_m'],c['action_index']))
 rows.append(dict(local_public=d['local_public'],mode=d['selection_evidence']['mode'],actual_sweep_deg=sweep*180/math.pi,original_unknown_hold_m=d['unknown_hold_m'],original_release_event='ACTUAL_SWEEP_AND_INFORMATION_RENEWED'in d['selection_evidence']['events'],certified_progress_actions=len(valid),counterfactual_release_eligible=d['selection_evidence']['mode']=='OBSERVE'and sweep>=math.pi/16 and bool(valid),best_certified_progress=None if not best else best[0],new_actual=False))
windows=[x['local_public']for x in rows if x['counterfactual_release_eligible']];root=repo/'runs/v766_commitment_release_diagnosis';root.mkdir(exist_ok=False)
result=dict(status='SAVED_OBSERVATION_RELEASE_PREDICATE_DIAGNOSED',rows=rows,existing_certified_progress_release_windows=windows,first_window=None if not windows else windows[0],original_release_events=sum(x['original_release_event']for x in rows),original_first_no_candidate=112,new_initializations=0,new_integrations=0,new_predictions=0,new_navigation=0,elapsed_s=time.time()-start)
assert all(sha(repo/n)==h for n,h in f.items());(root/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');signal.alarm(0);print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
