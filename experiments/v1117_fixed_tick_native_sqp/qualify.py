"""One exact-native arithmetic and fixed-timing derivative check, no physics."""
import sys,json,hashlib,ast
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1117_fixed_tick_native_sqp';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(C));import run as driver;import numpy as np
from solver import Solver

def main():
 assert not(O/'ENTRY_QUALIFICATION.json').exists()
 old=R/'runs/v1116_native_path_constraints';x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());pg=json.loads((R/'runs/v1107_reference_frame_alignment/PATH_GEARS.json').read_text());seed=json.loads((old/'OPTIMIZATION.json').read_text())['z'];engine=Solver(x,np.array(pg['path']),pg['gear'],initial_guess=seed);events=json.loads((old/'CONTROL_SCHEDULE.json').read_text())['sections']
 with np.load(old/'CONTROLLER_SOURCE.npz')as z:ss=z['states'].copy()
 g,terms=engine.constraint_terms(ss,events);before=json.loads((old/'COMPLETION.json').read_text());assert len(g)==2055 and not terms['restoration_targets_met'];assert abs(terms['minimum_certified_raw_lower_m']-before['complete_review']['minimum_full_cycle_raw_m'])<=1e-12
 assert abs(terms['maximum_certified_cross_upper_m']-before['complete_review']['maximum_predicted_cross_track_m'])<=1e-12
 z=engine.seed();engine.lower[-engine.n:]=z[-engine.n:];engine.upper[-engine.n:]=z[-engine.n:];baseline=engine.schedule(z)[1];j=int(np.argmin(abs(z[:48])));left=z.copy();right=z.copy();left[j]-=.0001;right[j]+=.0001
 assert engine.schedule(left)[1]==engine.schedule(right)[1]==baseline
 fl,gl,_=engine.evaluate(left);fr,gr,_=engine.evaluate(right);dg=(gr-gl)/.0002;assert np.isfinite(dg).all() and abs(dg).max()>1e-6
 changed=ss.copy();changed[500,:2]+=[.1,.1];_,bad=engine.constraint_terms(changed,events);assert bad['maximum_certified_cross_upper_m']>terms['maximum_certified_cross_upper_m']+.02
 for p in C.glob('*.py'):ast.parse(p.read_text())
 q=json.loads((old/'ENTRY_QUALIFICATION.json').read_text());q.update(arithmetic_qualification={'passed':True,'exact_native_raw_m':terms['minimum_certified_raw_lower_m'],'exact_native_cross_m':terms['maximum_certified_cross_upper_m'],'fixed_tick_derivative_shape':list(dg.shape),'fixed_tick_events_identical':True,'all_failed_final_gates_preserved':True,'perturbed_native_rejected':True},registered_saved_development_seed='V1116 selected single fixed EW z; timings frozen',analytical_work={'cpp_native':engine.native,'python_native':0})
 (O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(q,indent=2)+'\n');files=json.loads((old/'SOURCE_FREEZE.json').read_text())
 for n,h in files.items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
 for p in C.iterdir():
  if p.is_file():files[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 for p in [O/'profile.so',O/'ENTRY_QUALIFICATION.json',old/'OPTIMIZATION.json',old/'CONTROL_SCHEDULE.json',old/'COMPLETION.json',old/'CONTROLLER_SOURCE.npz']:
  files[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 (O/'SOURCE_FREEZE.json').write_text(json.dumps(files,indent=2)+'\n');print(json.dumps({'qualification':q['arithmetic_qualification'],'new_work':q['analytical_work']}))
if __name__=='__main__':main()
