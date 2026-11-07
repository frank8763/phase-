"""Independent saved nominal ordering/progress/dedup/command proof; zero dynamics."""
import argparse,gzip,json
from pathlib import Path
import numpy as np
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(s)for s in p.read_text().splitlines()]if p.exists()else[]
def audit(pair):
 pair=Path(pair);cell=pair/'geometry_memory';goal=np.asarray(read(pair/'STATIC_PROTOCOL.json')['goal_xy'])
 decisions=lines(cell/'control_decisions.jsonl');ad={x['step']:x for x in lines(cell/'model_admission.jsonl')};records=[]
 nominal=[x for x in decisions if x.get('candidate_role')=='BACKUP_RETURN'and x['stage']=='NOMINAL']
 selected_steps=set()
 for n in nominal:
  step=n['step'];ranked=sorted([c for c in n['candidates']if c['reason']is None],key=lambda c:c['score'],reverse=True)
  selected=[x for x in decisions if x.get('candidate_role')=='BACKUP_RETURN'and x['step']==step and x['stage']=='RETURN_SELECTION']
  attempts=[x for x in decisions if x.get('candidate_role')=='BACKUP_RETURN'and x['step']==step and x['stage']=='BACKUP_APPEND']
  seen=set();attempt_index=0;accepted=False;checks=[]
  if not ranked:
   assert not selected and not attempts
  else:
   assert 0<len(selected)<=len(ranked)<=25,'RETURN_SEARCH_MISSING'
   for rank,x in enumerate(selected):
    c=ranked[rank];z=np.load(cell/'nominal_forecasts'/c['nominal_saved_forecast']);trajectory=z['poses']
    progress=float(np.linalg.norm(z['initial_pose'][:2]-goal)-np.linalg.norm(trajectory[-1,:2]-goal));command=np.asarray(c['first_command']);key=tuple(command)
    assert x['nominal_rank']==rank and x['nominal_candidates_total']==len(ranked)and abs(x['ordinary_score']-c['score'])<=1e-12
    assert np.array_equal(x['first_command'],command)and np.array_equal(x['predicted_end_pose'],trajectory[-1])and abs(x['predicted_goal_progress_m']-progress)<=1e-12
    assert x['hidden_world_geometry_used']is False
    if not read(pair/'geometry_memory/result.json')['source_revision'].startswith('V853')and progress<.02:assert x['status']=='SKIPPED_ORIGINAL_PROGRESS_GATE'
    elif key in seen:assert x['status']=='SKIPPED_DUPLICATE_ELIGIBLE_COMMAND'
    else:
     seen.add(key);a=attempts[attempt_index];attempt_index+=1
     assert a['return_nominal_rank']==rank and np.array_equal(a['first_command'],command)
     success=a['detail']['status']=='APPENDABLE_BACKUP_FOUND'
     if not success:
      assert a['detail']['status']in ['NO_APPENDABLE_BACKUP','PREFIX_SELF_DOMAIN_REJECTED']
      assert x['status']=='COMPLETE_ADMISSION_REJECTED'and x['old_contract_retained']is True
     else:
      assert x['status']=='COMPLETE_ADMISSION_ACCEPTED'and rank==selected[-1]['nominal_rank']
      actual=ad[step];assert actual['certified_backup_handover']and actual['return_nominal_rank']==rank and actual['return_original_candidates']==len(ranked)
      assert abs(actual['score']-c['score'])<=1e-12 and np.array_equal(actual['predicted_end_pose'],trajectory[-1])
      with gzip.open(cell/'handover_certificates'/actual['recovery_reserve']['handover_certificate'],'rt')as stream:cert=json.load(stream)
      meta=cert['metadata'];assert meta['return_nominal_rank']==rank and abs(meta['predicted_goal_progress_m']-progress)<=1e-12 and np.array_equal(cert['first_command'],command)
      assert cert['minimum_causal_predicted_clearance_m']>=.155 and cert['minimum_predicted_self_domain_margin_m']>=.002 and cert['terminal_speed_m_s']<=.025
      assert len(cert['qpos'])==len(cert['qvel'])==len(cert['controls'])==320 and len(cert['prefix_poses'])==8
      accepted=True;selected_steps.add(step)
    checks.append(dict(rank=rank,progress_m=progress,status=x['status']))
   assert attempt_index==len(attempts)and(accepted or len(selected)==len(ranked)),'RETURN_SEARCH_TRUNCATED'
  records.append(dict(step=step,ranked_candidates=len(ranked),distinct_complete_attempts=len(attempts),accepted=accepted,details=checks))
 assert selected_steps=={s for s,x in ad.items()if x.get('certified_backup_handover')},'MISSING_ACCEPTED_RETURN_PROVENANCE'
 result=dict(status='RANKED_RETURN_INDEPENDENT_PASS',checks=dict(all_saved_returns_reconstructed=True,all_existing_candidates_examined_until_first_certificate=True,common_complete_maneuver_gate_separately_audited=True,complete328_admission_required=True,selected_commands_provenance=True),records=records,new_integrations=0,scope='Search completeness only; original physical/replay/full-tail audits separately mandatory')
 (pair/'RANKED_RETURN_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],return_searches=len(records),certified_returns=len(selected_steps))))
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('pair');audit(p.parse_args().pair)
