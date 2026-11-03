"""Recompute all saved progress-band and visibility choices; no integration."""
import argparse,gzip,json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from observation_selection import choose_backup
p=argparse.ArgumentParser();p.add_argument('paired');args=p.parse_args();pair=Path(args.paired);cell=pair/'geometry_memory'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]if p.exists()else[]
protocol=read(pair/'STATIC_PROTOCOL.json');states={x['step']:x for x in lines(cell/'motion_estimate.jsonl')};execution=lines(cell/'v648_execution.jsonl');events=lines(cell/'control_decisions.jsonl');field=SimpleNamespace(rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']));details=[];sources={}
for event in events:
 if event['stage']!='BACKUP_APPEND':continue
 meta=event.get('detail',{}).get('recovery_selection_metadata')
 if meta is None:continue
 step=event['step'];current=protocol['start_qpos'][:2]if step==0 else execution[step-1]['qpos_full'][:2];candidates=[]
 for row in meta['candidates']:
  candidates.append(dict(target=np.asarray(row['target']),recovery_kind=row['kind'],poses=np.asarray([row['terminal_pose']]),minimum_causal_predicted_clearance_m=row['minimum_causal_clearance_m']))
 admitted=[x for x in event['detail']['candidates'] if x['reason']is None]
 work=event['detail']['recovery_selection_work']
 chosen,recomputed=choose_backup(candidates,current,np.asarray(protocol['goal_xy']),field,states[step]);local=dict(full_metadata_recomputed=meta==recomputed,public_current_state=meta['public_current_xy']==current,public_goal=meta['public_goal_xy']==protocol['goal_xy'],registered_undetected=states[step]['center']is None and 'free_space_renewal'in states[step],all_candidates_original_floor=all(x['minimum_causal_clearance_m']>=.155 for x in meta['candidates']),no_future_observation_for_safety=meta['safety_uses_future_measurement']is False,all_logged_safe_candidates_present=len(admitted)==len(meta['candidates']) and all(a['target_command']==b['target'] and a['minimum_clearance_m']==b['minimum_causal_clearance_m'] for a,b in zip(admitted,meta['candidates'])),extra_visibility_work_recorded=work['wall_seconds']>=0 and work['visibility_evaluations']==sum(x['within_best_progress_band']for x in meta['candidates']))
 details.append(dict(step=step,passed=all(local.values()),checks=local,selected_target=chosen['target'].tolist(),selected_goal_progress_m=meta['selected_goal_progress_m'],potential_visible_cells=meta['selected_potential_visible_cells']));sources.setdefault(step,[]).append(meta)
certificates=[]
for folder in['recovery_contracts','handover_certificates','shadow_handover_certificates']:
 for path in sorted((cell/folder).glob('*.gz')):
  with gzip.open(path,'rt')as stream:c=json.load(stream)
  if c['recovery_kind']=='BRAKE_ONLY'or'free_space_renewal'not in c['forecast_state']:continue
  meta=c.get('recovery_selection_metadata');checks=dict(selection_saved=meta is not None)
  if meta:
   selected=meta['candidates'][meta['selected_safe_index']]
   checks.update(selected_command=c['target']==selected['target'],selected_terminal_pose=np.max(abs(np.asarray(c['poses'])[-1]-selected['terminal_pose']))<=1e-12,same_full_input_metadata=any(x==meta for x in sources.get(c['created_step'],[])),all_original_gates=c['minimum_causal_predicted_clearance_m']>=.155 and c['minimum_predicted_self_domain_margin_m']>=.002 and c['terminal_speed_m_s']<=.025)
  certificates.append(dict(file=str(path),passed=all(checks.values()),checks=checks))
all_checks=dict(all_actual_choices_recomputed=all(x['passed']for x in details),all_saved_nonbrake_recovery_choices=all(x['passed']for x in certificates),same_event_count=len(details)==sum(e['stage']=='BACKUP_APPEND'and e.get('detail',{}).get('recovery_selection_metadata')is not None for e in events))
work=[e['detail']['recovery_selection_work']for e in events if e['stage']=='BACKUP_APPEND'and e.get('detail',{}).get('recovery_selection_metadata')is not None]
out=dict(status='ALL_RECOVERY_SELECTIONS_RECOMPUTED'if all(all_checks.values())else'FAIL',checks=all_checks,choices=details,certificates=certificates,choice_count=len(details),extra_visibility_evaluations=sum(x['visibility_evaluations']for x in work),extra_selection_wall_seconds=sum(x['wall_seconds']for x in work),new_integrations=0,scope='Recomputes only geometric potential used to rank already-certified tails; not a future free-space certificate or recursive viability guarantee.')
(pair/'RECOVERY_SELECTION_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in['choices','certificates']}));assert out['status']!='FAIL'
