"""Check frozen actual-input prefix and all allowed-variable bounds, zero dynamics."""
import sys,json
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1131_final_section_restore'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(C));from restore import Solver
import numpy as np

def main():
 t=json.loads((C/'TASK.json').read_text());x=json.loads((R/t['input']).read_text());x['safe_terminal_pose']=json.loads((R/t['terminal']).read_text())['selected_body_pose'];p=json.loads((R/t['path']).read_text());s=Solver(x,np.array(p['path']),p['gear']);z=s.seed();old=json.loads((R/'runs/v1130_timed_recording_continuation/OPTIMIZATION.json').read_text());assert s.reference_rows[:41]==[tuple(r)for r in old['rows'][:41]];assert len(s.free)==13 and len(s.fixed)==39;assert np.all(s.lower[s.fixed]==s.upper[s.fixed]);assert np.all(s.lower[s.free]<s.upper[s.free]);assert np.array_equal(z,np.array(old['selected_z']));tests=0
 for j in s.free:
  for val in [s.lower[j],s.upper[j]]:
   q=z.copy();q[j]=val;rows,events=s.schedule(q);assert rows[:41]==s.prefix_rows and events[2][2]==s.prefix_native;tests+=1
 assert all(s.reference_rows[i]==tuple(old['rows'][i])for i in range(41));answer={'passed':True,'same_saved_failed_source_seed':True,'fixed_variables':39,'free_variables':13,'fixed_prefix_native':s.prefix_native,'first41_schedule_rows_identical':True,'allowed_variable_bound_cases':tests,'physical_models':0,'physical_integrations':0,'analytical_dynamics_integrations':0,'solver_executed':False,'scope':'saved-state warm-start only; not generic policy qualification'};(O/'RESTORATION_ENTRY_QUALIFICATION.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer))
if __name__=='__main__':main()
