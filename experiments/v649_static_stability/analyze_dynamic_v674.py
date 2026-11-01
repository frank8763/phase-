"""Persisted decision rejection breakdown and same-state prefix; no integrations."""
from pathlib import Path
from collections import Counter
import json,numpy as np
repo=Path(__file__).resolve().parents[2];out=repo/'runs/v674_dynamic_renewable_backup';root=out/'dev41_95000011_renewable/paired';cell=root/'geometry_memory'
read=lambda p:json.loads(p.read_text())
lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]if p.exists()else[]
assert(root/'completion.json').exists(),'DO_NOT_ANALYZE_UNFINISHED_NAVIGATION'
decisions=lines(cell/'control_decisions.jsonl');nominal={x['step']:x for x in decisions if x['stage']=='NOMINAL'and x['candidate_role']=='ORDINARY'}
append=[x for x in decisions if x['stage']=='BACKUP_APPEND'and x['candidate_role']=='ORDINARY'];misses=[]
for x in append:
 d=x['detail'];n=nominal[x['step']];safe=[a for a in n['candidates']if a['reason']is None]
 if d['status']=='NO_APPENDABLE_BACKUP':
  misses.append({'step':x['step'],'ordinary_safe_candidates':len(safe),'distinct_safe_first_commands':len({tuple(a['first_command'])for a in safe}),'highest_safe_score':max((a.get('score',-1e9)for a in safe),default=None),'recovery_rejection_reasons':dict(Counter(a['reason']for a in d['candidates'])),'best_backup_clearance_m':max((a['minimum_clearance_m']for a in d['candidates']),default=None),'nominal_safe_scores':sorted([a['score']for a in safe],reverse=True)})
attempts=lines(cell/'handover_attempts.jsonl');matches=lines(cell/'reserved_state_matches.jsonl');rows=lines(cell/'v648_execution.jsonl');old=lines(repo/'runs/v673_dynamic_joint_forecast/dev40_95000011_joint/paired/geometry_memory/v648_execution.jsonl')
first=None;maxprefix=0.
for a,b in zip(old,rows):
 error=max(float(np.max(abs(np.asarray(a[k])-b[k])))for k in ['qpos_full','qvel_full','ctrl','mocap_pos'])
 if error>1e-8:first=a['step'];break
 maxprefix=max(maxprefix,error)
result={'status':'COMPLETE_ZERO_INTEGRATION_ANALYSIS','result':read(cell/'result.json')if(cell/'result.json').exists()else None,'ordinary_nominal_statuses':dict(Counter(x['summary']['status']for x in nominal.values())),'ordinary_backup_statuses':dict(Counter(x['detail']['status']for x in append)),'safe_nominal_but_no_backup_records':misses,'handover_statuses':dict(Counter(x['status']for x in attempts)),'handover_attempts':attempts,'first_full_state_control_difference_from_v673':first,'maximum_pre_difference_full_error':maxprefix,'all_executed_certificate_matches':bool(matches)and all(max(x['maximum_qpos_error'],x['maximum_qvel_error'])<=1e-8 for x in matches),'new_navigation_tasks':0,'simulation_integrations':0,'scope':'candidate library rejection only, not global control infeasibility; alternative appendability untested'}
(out/'DECISION_ANALYSIS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k not in ['result','handover_attempts','safe_nominal_but_no_backup_records']},indent=2));print('safe_nominal_no_backup',len(misses),'with_alternatives',sum(x['distinct_safe_first_commands']>1 for x in misses))
