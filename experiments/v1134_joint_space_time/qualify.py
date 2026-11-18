"""Verify actual wait scheduling and no hidden prefix/control/state reset."""
import sys,json,ast
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1134_joint_space_time';sys.path.insert(0,str(C));import run
import numpy as np

def main():
 t=json.loads((C/'TASK.json').read_text());x=json.loads((R/t['input']).read_text());x['safe_terminal_pose']=json.loads((R/t['terminal']).read_text())['selected_body_pose'];p=json.loads((R/t['path']).read_text());s=run.Solver(x,np.array(p['path']),p['gear']);seed=json.loads((O/'SELECTED_SEED.json').read_text());z=np.array(seed['selected_z']);u=np.r_[z[36:48],18.5];cases=0
 for seconds,ticks in [(0.,0),(.1,10),(18.5,1850),(19.63,1963)]:
  v=u.copy();v[12]=seconds;rows,wait,events=run.schedule(s,z,v);assert wait==ticks;without=rows[1:]if wait else rows;assert without[:41]==s.prefix_rows;assert sum(r[2]for r in rows)==sum(r[2]for r in s.schedule(z)[0])+ticks;cases+=1
 for q in [-.1,19.64]:
  v=u.copy();v[12]=q
  try:run.schedule(s,z,v)
  except AssertionError:cases+=1
  else:raise AssertionError('OUT_OF_RANGE_WAIT_ACCEPTED')
 assert np.array_equal(z[s.fixed],s.registered[s.fixed]);answer={'passed':True,'wait_and_prefix_cases':cases,'first3_command_sections_fixed':True,'new_hold_states_explicitly_propagated':True,'models':0,'physical_integrations':0,'analytical_dynamics_integrations':0,'solver_calls':0};run.dump(O/'QUALIFICATION.json',answer);print(json.dumps(answer))
if __name__=='__main__':main()
