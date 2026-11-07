"""Saved audit adapters only; synthetic views are explicitly NOT new trials."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import MethodType
import numpy as np

repo=Path(__file__).resolve().parents[2];own=repo/'experiments/v812_soft_global_reference'
root=repo/'runs/v812_interface_checks';root.mkdir(exist_ok=False)
sys.path.insert(0,str(own))
from current_guide import attach
from independent_soft_reference import field
from exact_footprint import pose_values
from route_commitment import route_check
read=lambda p:json.loads(p.read_text())
dump=lambda p,v:p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
for p in own.glob('*.py'):ast.parse(p.read_text())
pair=repo/'runs/v809_time_reference_global/main_slot01/paired';cell=pair/'geometry_memory'
protocol=read(pair/'STATIC_PROTOCOL.json')
qual=read(repo/'runs/v812_soft_global_reference/pre_navigation/RESULTS.json')
proposal=root/'qualification_packet_view';proposal.mkdir();(proposal/'geometry_memory').mkdir()
dump(proposal/'AUDIT_VIEW_ONLY.json',dict(not_navigation=True,integrations=0,source='V812 saved pure qualification outputs'))
dump(proposal/'STATIC_PROTOCOL.json',protocol)
(proposal/'geometry_memory/motion_estimate.jsonl').write_text(''.join(json.dumps(x['causal_state'])+'\n'for x in qual))
for x in qual:
    dump(proposal/f'geometry_memory/planning_{x["step"]:04d}.json',dict(step=x['step'],path=x['path'],stats=x['stats'],causal_route_input=x['causal_world'],route_projection_metadata=x['metadata']))
def audit(name,args,log):
    cp=subprocess.run([sys.executable,'-B',str(own/name),*map(str,args)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=90)
    (root/log).write_text(cp.stdout);assert cp.returncode==0,cp.stdout[-1500:]
audit('audit_proposal_separation.py',[proposal],'proposal_adapter.console')
# Independently exercise ten real saved pose/path combinations under the new
# current-geometry reference semantics; no old trajectory is relabelled PASS.
oldrows=[json.loads(s)for s in(cell/'route_revalidation.jsonl').open()]
chosen=[oldrows[i]for i in np.linspace(0,len(oldrows)-1,10).astype(int)]
needed={x['step']for x in chosen};states={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').open())if x['step']in needed}
trace=read(cell/'trace.json');view=root/'ten_revalidation_views';view.mkdir();(view/'geometry_memory').mkdir()
dump(view/'AUDIT_VIEW_ONLY.json',dict(not_navigation=True,integrations=0,source='V809 real poses and paths, V812 independently recomputed route predicate'))
dump(view/'STATIC_PROTOCOL.json',protocol);dump(view/'geometry_memory/trace.json',trace)
newrows=[]
for r in chosen:
    step=r['step'];f=field(protocol,states[step]);f.pose_values=MethodType(pose_values,f);attach(f,states[step])
    new=route_check(f,np.asarray(r['reference_path']),r['index'],np.asarray(trace[step-1]['pose']),trace[:step],step,r['last_plan'])
    base={k:r[k]for k in ['step','index','last_plan','reference_path']};newrows.append(dict(**base,**new))
(view/'geometry_memory/route_revalidation.jsonl').write_text(''.join(json.dumps(x)+'\n'for x in newrows))
(view/'geometry_memory/motion_estimate.jsonl').write_text(''.join(json.dumps(states[s])+'\n'for s in sorted(states)))
for p in cell.glob('planning_*.json'):shutil.copy2(p,view/'geometry_memory'/p.name)
audit('audit_route_commitment.py',[view],'route_adapter.console')
# The original three immutable t0 packet sets exercise exact count/noise schema.
pre=read(repo/'runs/v809_time_reference_global/development01/PREFLIGHTS.json');dump(root/'PREFLIGHTS.json',pre)
audit('audit_field_preflight.py',[root],'preflight_adapter.console')
out=dict(status='V812_ZERO_MODEL_AUDIT_INTERFACES_PASS',proposal_view='SPATIAL_PROPOSAL_SEPARATION_AUDIT_PASS',
    saved_revalidations=10,revalidation_audit=read(view/'ROUTE_COMMITMENT_AUDIT.json')['status'],
    maximum_reconstruction_error=read(view/'ROUTE_COMMITMENT_AUDIT.json')['maximum_geometry_reconstruction_error'],
    original_three_t0_noise_schema=read(root/'PREFLIGHT_INDEPENDENT_AUDIT.json')['status'],
    models=0,integrations=0,views_are_not_new_navigation_or_old_result_reclassification=True)
dump(root/'RESULT.json',out);print(json.dumps(out))
