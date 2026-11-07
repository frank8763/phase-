"""Independent registration/provenance for the return-only appended finite library."""
import argparse,gzip,json,math
from pathlib import Path
import numpy as np
def target(steer,wheel):
 if abs(steer)<1e-9:return [0.,0.,wheel,wheel]
 radius=.6/math.tan(abs(steer));inner=math.atan2(.6,radius-.27);outer=math.atan2(.6,radius+.27)
 return [inner,outer,wheel,wheel]if steer>0 else[-outer,-inner,wheel,wheel]
def audit(pair):
 pair=Path(pair);cell=pair/'geometry_memory';lines=lambda p:[json.loads(s)for s in p.open()]if p.exists()else[];decisions=lines(cell/'control_decisions.jsonl');records=[];by_step={}
 steers=[-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]
 for d in decisions:
  if d['stage']!='BACKUP_APPEND':continue
  candidates=d['detail'].get('candidates',[]);new=[c for c in candidates if c['library']=='RETURN_FORWARD_ESCAPE']
  if not new:continue
  assert d['candidate_role']=='BACKUP_RETURN','NEW_ESCAPE_OUTSIDE_RETAINED_RETURN'
  old=[c for c in candidates if c['library']in ['ORIGINAL','FORWARD_EXTENSION']]
  assert len(old)==21 and all(c['reason']is not None for c in old),'OLD_PRIORITY_OR_GATE_CHANGED'
  assert len(new)==10 and len(candidates)==31
  for c,(steer,wheel)in zip(new,[(s,w)for s in steers for w in[8.,12.]]):
   assert c['kind']=='FORWARD_ESCAPE_BRAKE'and c['brake_after_native_ticks']==160 and np.max(abs(np.asarray(c['target_command'])-target(steer,wheel)))<=1e-12
   if c['reason']is None:assert c['minimum_clearance_m']>=.155 and c['self_domain_margin_m']>=.002 and c['terminal_speed_m_s']<=.025 and c['signed_displacement_m']>=.02 and not c['full_minimum_not_evaluated']
  by_step.setdefault(d['step'],[]).append(d)
  records.append(dict(step=d['step'],nominal_rank=d.get('return_nominal_rank'),old21_all_rejected=True,new10_registered=True,valid=sum(c['reason']is None for c in new)))
 accepted={}
 for file in(cell/'handover_certificates').glob('*.gz'):
  with gzip.open(file,'rt')as stream:c=json.load(stream)
  if c['recovery_kind']!='FORWARD_ESCAPE_BRAKE':continue
  assert c['brake_after_native_ticks']==160 and tuple(c['target'][2:])in[(8.,8.),(12.,12.)]
  match=[d for d in by_step.get(c['handover_step'],[])if d['return_nominal_rank']==c['metadata']['return_nominal_rank']]
  assert len(match)==1 and match[0]['detail']['status']=='APPENDABLE_BACKUP_FOUND'
  assert any(x['reason']is None and np.array_equal(x['target_command'],c['target'])for x in match[0]['detail']['candidates']if x['library']=='RETURN_FORWARD_ESCAPE')
  accepted[c['created_step']]=c['target']
 for file in(cell/'recovery_contracts').glob('*.gz'):
  with gzip.open(file,'rt')as stream:c=json.load(stream)
  if c['recovery_kind']=='FORWARD_ESCAPE_BRAKE':assert c['created_step']in accepted and c['target']==accepted[c['created_step']]
 result=dict(status='FORWARD_ESCAPE_PROVENANCE_PASS',checks=dict(return_only=True,old21_have_priority=True,registered10_brake160=True,all_original_full_gates=True,actual_escape_contracts_from_certified_handover=True),records=records,escape_handover_contracts=len(accepted),models=0,integrations=0)
 (pair/'FORWARD_ESCAPE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],attempts=len(records),accepted=len(accepted))))
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('pair');audit(p.parse_args().pair)
