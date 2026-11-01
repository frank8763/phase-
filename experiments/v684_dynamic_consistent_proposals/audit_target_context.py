"""Zero-integration check: corrected targets correspond to the original recorded steering/wheel library."""
import os,json,hashlib
from pathlib import Path
import numpy as np
from consistent_targets import target_from_geometry
repo=Path(os.environ['PHASE_REPO']);root=repo/'runs/v684_dynamic_consistent_proposals';validation=json.loads((root/'pre_navigation_retry02/COMPLETION.json').read_text());base=repo/'runs/v680_dynamic_later_stop_reserve/dev47_95000011_laterstop/paired/geometry_memory';decisions=[json.loads(s)for s in(base/'control_decisions.jsonl').read_text().splitlines()];records=[]
for row in validation['records']:
 k=row['checkpoint'];old=next(d['candidates']for d in decisions if d['step']==k and d['stage']=='NOMINAL'and d['candidate_role']=='ORDINARY');straight=[c['target_command'][2]for c in old if max(abs(x)for x in c['target_command'][:2])<1e-9];assert len(straight)==3;expected=[];angles=[]
 for i in range(0,len(old),3):
  lf,rf=old[i]['target_command'][:2]
  if max(abs(lf),abs(rf))<1e-9:angle=0.
  else:
   radius=.6/np.tan(rf)-.27 if rf>0 else .6/np.tan(lf)+.27;angle=float(np.arctan(.6/radius))
  angles.append(angle)
  for wheel in straight:expected.append(target_from_geometry(.6,.54,.42722137342572125,angle,wheel))
 actual=np.asarray([c['target_command']for c in row['new_candidate_diagnostics']]);expected=np.asarray(expected);error=float(np.max(np.min(np.max(abs(expected[:,None,:]-actual[None,:,:]),axis=2),axis=1)));reverse=float(np.max(np.min(np.max(abs(expected[:,None,:]-actual[None,:,:]),axis=2),axis=0)));records.append({'step':k,'original_virtual_steering_targets':angles,'original_straight_wheel_targets':straight,'maximum_target_library_difference':max(error,reverse),'passed':max(error,reverse)<=1e-9})
result={'status':'ALL_FIXED_TARGET_CONTEXTS_MATCH'if all(r['passed']for r in records)else'FIXED_CONTEXT_MISMATCH','records':records,'robot_integrations':0,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'compares target sets despite time-varying inherited steer limit; no additional rollout or changed result'};(root/'TARGET_CONTEXT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
