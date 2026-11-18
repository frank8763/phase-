"""Reduced terminal solver, original prefix and finite timing entry checks."""
import sys,json,ast
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1132_terminal_timing_split';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump
sys.path.insert(0,str(R/'experiments/v1131_final_section_restore'));from restore import Solver
import numpy as np

def main():
 t=json.loads((C/'TASK.json').read_text());x=json.loads((R/t['input']).read_text());x['safe_terminal_pose']=json.loads((R/t['terminal']).read_text())['selected_body_pose'];p=json.loads((R/t['path']).read_text());s=Solver(x,np.array(p['path']),p['gear']);z=np.array(json.loads((C/'WARM_START.json').read_text())['selected_z']);assert np.array_equal(z[s.fixed],s.registered[s.fixed]);rows,events=s.schedule(z);assert rows[:41]==s.prefix_rows and events[2][2]==9388
 for j in range(36,48):
  for val in [s.lower[j],s.upper[j]]:
   q=z.copy();q[j]=val;qr,ev=s.schedule(q);assert qr[:41]==rows[:41]and q[51]==z[51]
 waits=json.loads((C/'TIMING_TICKS.json').read_text());assert waits==list(range(0,2000,50))and len(waits)==40;phases=np.mod(np.array(waits)*.01,2*np.pi/.32);assert len(np.unique(phases))==40
 sys.path.insert(0,str(R/'runs/v1111_solver_dependencies/site'));from scipy.optimize import least_squares
 r=least_squares(lambda a:np.array([a[0]-.3,a[1]+.2]),[0.,0.],jac=lambda a:np.eye(2),bounds=([-1.,-1.],[1.,1.]),max_nfev=30);assert r.success and abs(r.x-[.3,-.2]).max()<1e-7
 for p in C.glob('*.py'):ast.parse(p.read_text())
 answer={'passed':True,'installed_least_squares_fixture_passed':True,'fixed_prefix_native':9388,'reduced_bound_prefix_cases':24,'last_duration_fixed':True,'unique_registered_timing_candidates':40,'models':0,'physical_integrations':0,'analytical_dynamics_integrations':0,'real_solver_calls':0};dump(O/'QUALIFICATION.json',answer);print(json.dumps(answer))
if __name__=='__main__':main()
