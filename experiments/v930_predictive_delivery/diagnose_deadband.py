"""Saved production command seam counterexample, no model initialization."""
import importlib.util,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];P=R/'runs/v858_nav2_verified/v929/static_main_we';O=R/'runs/v930_predictive_delivery';O.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('actual_twist_contract',R/'experiments/v929_executable_mppi/twist_contract.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
x=json.loads((P/'MPPI_DIAGNOSTICS.json').read_text());cmd=json.loads((P/'COMMANDS.json').read_text());violations=[]
for i,row in enumerate(x):
 try:m.require_representable(row['v'],row['w'])
 except ValueError as e:violations.append(dict(index=i,row=row,error=repr(e)))
assert len(violations)==1 and violations[0]['index']==len(x)-1
last=x[-1];assert last['gear']==-1 and last['v']<0 and abs(last['v'])<.005 and abs(last['w'])<=abs(last['v'])/1.32+1e-6
# No online repair. This pure-data proposal illustrates a deadband projection;
# physical closure, full rollout/output handling and acceptance are not qualified.
def proposal(v,w):return (0.,0.)if abs(v)<.005 else(v,max(-abs(v)/1.32,min(abs(v)/1.32,w)))
new=proposal(last['v'],last['w']);m.require_representable(*new)
assert new==(0.,0.)
trace=np.load(P/'physics/NATIVE_TRACE.npz');xy=trace['qpos'][:,:2];travel=float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum())
result=dict(models=0,integrations=0,all_diagnostics=len(x),all_curvature_checks_pass=True,actuator_deadband_violations=violations,valid_saved_final_commands=len(cmd['cmd_vel']),saved_controller_commands=len(cmd['cmd_vel_nav']),rejected_final_twist_not_logged_exactly=True,last_raw_controller_command_reproduces_same_rejection=True,actual_total_travel_m=travel,compute_p50_s=float(np.quantile([r['compute_s']for r in x],.5)),compute_p99_s=float(np.quantile([r['compute_s']for r in x],.99)),prototype_deadband_counterexample_output=new,prototype_is_deployed=False,qualification_scope='One saved failure reproduced against actual production contract. Not a repaired navigation qualification or unique cause of all historical failures.')
(O/'DEADBAND_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
