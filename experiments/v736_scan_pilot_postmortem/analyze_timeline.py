"""Reproduce the closed pilot's interface timeline using saved JSON only."""
import json,gzip
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];cell=repo/'runs/v735_scan_differential_navigation/main01/paired/geometry_memory';read=lambda p:json.loads(p.read_text());lines=lambda n:[json.loads(s)for s in(cell/n).read_text().splitlines()]if(cell/n).exists()else[]
assert (repo/'REVIEW_PENDING').exists()and read(repo/'runs/v735_scan_differential_navigation/ROUND_WINDOW.json')['round_closed']
execution=lines('v648_execution.jsonl');decisions=lines('control_decisions.jsonl');admissions=lines('model_admission.jsonl');samples=lines('proposal_learning_samples.jsonl');events=lines('handover_attempts.jsonl');xy=np.asarray([x['qpos_full'][:2]for x in execution]);r=read(cell/'result.json');detail=[]
for event in events:
 step=event['step'];nom=[x for x in decisions if x['step']==step and x['stage']=='NOMINAL'and x['candidate_role']=='BACKUP_RETURN'];append=[x for x in decisions if x['step']==step and x['stage']=='BACKUP_APPEND'and x['candidate_role']=='BACKUP_RETURN'];candidates=nom[0]['candidates']if nom else[]
 detail.append(dict(step=step,status=event['status'],nominal_candidate_count=len(candidates),ordinary_safe_count=sum(x['reason']is None for x in candidates),append_inputs_tested=len(append),goal_progress_m=event.get('predicted_goal_progress_m'),all_existing_backup_tails_rejected=bool(append)and all(all(c['reason']is not None for c in d['detail'].get('candidates',[]))for d in append)))
backups=[]
for p in sorted((cell/'recovery_contracts').glob('*.gz')):
 with gzip.open(p,'rt')as stream:c=json.load(stream)
 used=[x for x in admissions if x.get('retained_from_step')==c['created_step']];backups.append(dict(created_step=c['created_step'],activation_step=c['activation_step'],kind=c['recovery_kind'],used_public_steps=len(used),forecast_minimum_m=c['minimum_causal_predicted_clearance_m'],signed_longitudinal_displacement_m=c['signed_longitudinal_displacement_m']))
roles={k:sum(x['selected_role']==k for x in samples)for k in sorted({x['selected_role']for x in samples})};old=repo/'runs/v721_recursive_unseen_navigation/main01/paired/geometry_memory';oldexe=[json.loads(s)for s in(old/'v648_execution.jsonl').read_text().splitlines()];oldxy=np.asarray([x['qpos_full'][:2]for x in oldexe]);first=next((i for i,(a,b)in enumerate(zip(execution,oldexe))if max(np.max(abs(np.asarray(a[k])-b[k]))for k in ['qpos_full','qvel_full','ctrl','mocap_pos'])>1e-8),None)
out=dict(status='FAILED_PILOT_INTERFACE_TIMELINE_RECONSTRUCTED',outcome=r['outcome'],strict_arrival=False,first_discovery=None,public_steps=len(execution),maximum_displacement_m=float(np.linalg.norm(xy-[-4,-2],axis=1).max()),closest_goal_distance_m=float(np.linalg.norm(xy-[4,-2],axis=1).min()),final_goal_distance_m=r['goal_distance_m'],old_v721_maximum_displacement_m=float(np.linalg.norm(oldxy-[-4,-2],axis=1).max()),old_v721_closest_goal_distance_m=float(np.linalg.norm(oldxy-[4,-2],axis=1).min()),first_changed_execution_zero_based_step=first,selected_ordinary_roles=roles,recovery_contracts=backups,return_attempts=detail,new_initializations=0,new_integrations=0,scope='Missing alternative appended backups are untested, not assumed feasible; no additional private prediction performed.')
target=repo/'runs/v736_scan_pilot_postmortem/INTERFACE_TIMELINE.json'
if target.exists():assert read(target)==out,'EXISTING_TIMELINE_DIFFERS'
else:target.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(status='SAVED_INTERFACE_TIMELINE_EXACTLY_REPRODUCED',states=out['public_steps'],return_attempts=len(detail),new_integrations=0)))
