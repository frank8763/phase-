"""Saved-state arithmetic qualification; zero new dynamics or physical models."""
import sys,json,hashlib,ast,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1116_native_path_constraints';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(C));import run as d;import numpy as np
from solver import Solver
def main():
 assert not(O/'ENTRY_QUALIFICATION.json').exists()
 old=R/'runs/v1115_coupled_complete_source';q=json.loads((old/'ENTRY_QUALIFICATION.json').read_text());x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());pg=json.loads((R/'runs/v1107_reference_frame_alignment/PATH_GEARS.json').read_text());engine=Solver(x,np.array(pg['path']),pg['gear']);events=json.loads((old/'CONTROL_SCHEDULE.json').read_text())['sections']
 with np.load(old/'CONTROLLER_SOURCE.npz')as z:ss=z['states'].copy()
 g,terms=engine.constraint_terms(ss,events);maximum=0.
 for i,((path,arc,gear),(begin,moving,end))in enumerate(zip(engine.sections,events)):maximum=max(maximum,float(d.distances(ss[begin-600 if i else begin:end+1],path).max()))
 a=json.loads((old/'COMPLETION.json').read_text());before=a['optimizer_constraint_review'];assert abs(terms['maximum_certified_cross_upper_m']-maximum)<1e-12;assert maximum<=.04 and before['maximum_certified_cross_upper_m']>.04
 error=0.
 for key in ['minimum_certified_raw_lower_m','endpoint_errors_m','coupled_mode_envelope_lower_m']:
  difference=float(np.max(abs(np.asarray(terms[key])-np.asarray(before[key]))));error=max(error,difference);assert difference<=1e-12,key
 assert len(g)==2055 and not terms['restoration_targets_met'];changed=ss.copy();changed[500,:2]+=[.1,.1];_,bad=engine.constraint_terms(changed,events);assert bad['maximum_certified_cross_upper_m']>maximum+.02
 for p in C.glob('*.py'):ast.parse(p.read_text())
 assert hashlib.sha256((O/'profile.so').read_bytes()).digest()==hashlib.sha256((old/'profile.so').read_bytes()).digest()
 q.update(arithmetic_qualification={'passed':True,'old_conservative_cross_upper_m':before['maximum_certified_cross_upper_m'],'new_exact_cross_max_m':maximum,'other_constraint_maximum_error':error,'native_perturbation_rejected':True,'count':2055,'new_analytical_dynamics':0,'invalid_source_still_rejected':True},registered_saved_development_seed='V1115 selected z for this same fixed EW software continuation',entry_dynamics_qualification_reused_by_sha=True)
 q['reused_analytical_work']=q.pop('analytical_work');q['analytical_work']={'cpp_native':0,'python_native':0}
 (O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(q,indent=2)+'\n')
 files=json.loads((old/'SOURCE_FREEZE.json').read_text())
 for n,h in files.items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
 for p in C.iterdir():
  if p.is_file():files[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 for p in [O/'profile.so',O/'ENTRY_QUALIFICATION.json',old/'OPTIMIZATION.json',old/'CONTROL_SCHEDULE.json',old/'COMPLETION.json',old/'CONTROLLER_SOURCE.npz']:
  files[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 (O/'SOURCE_FREEZE.json').write_text(json.dumps(files,indent=2)+'\n');print(json.dumps(q['arithmetic_qualification']))
if __name__=='__main__':main()
