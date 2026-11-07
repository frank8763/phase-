"""Replay actual527 supervisor selection seam; no dynamics/safety certificate mocked as passing."""
import argparse,importlib.util,json,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser();ap.add_argument('--worker',default='v828_goal_dynamic_confirmation');a=ap.parse_args()
own=repo/'experiments'/a.worker
spec=importlib.util.spec_from_file_location('supervisor_under_test',own/'recovery_supervisor.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
cell=repo/'runs/v828_goal_dynamic_confirmation/main_slot02/paired/geometry_memory'
row=next(json.loads(s)for s in(cell/'control_decisions.jsonl').open()if '"BACKUP_RETURN"'in s and json.loads(s)['step']==527 and json.loads(s)['stage']=='NOMINAL')
rows=[]
for c in row['candidates']:
 if c.get('reason')is not None:continue
 z=np.load(cell/'nominal_forecasts'/c['nominal_saved_forecast'])
 rows.append((float(c['score']),np.asarray(c['first_command']),z['poses'].copy(),float(c['minimum_clearance_m']),float(c['self_domain_margin_m'])))
rows.sort(key=lambda x:x[0],reverse=True)
z=np.load(cell/'nominal_forecasts'/row['candidates'][6]['nominal_saved_forecast']);current=z['initial_pose'].copy();goal=np.array([4.,-2.])
distance=np.linalg.norm(current[:2]-goal)
eligible=[x for x in rows if distance-np.linalg.norm(x[2][-1,:2]-goal)>=.02]
assert len(eligible)>0 and distance-np.linalg.norm(rows[0][2][-1,:2]-goal)<.02
attempts=[]
class Predictor:
 ranked_safe_candidates=rows;last_diagnostics=row['candidates'];prediction_steps=0
 def select(self,*args):return rows[0][1].copy(),dict(row['summary'])
class Reserve:
 cache={'created_step':490};cursor=288;last_handover_attempt={'status':'DIAGNOSTIC_ONLY_ALWAYS_REJECT'}
 def check_current_contract(self,*args):pass
 def try_handover(self,data,command,*args,**kwargs):attempts.append(np.asarray(command).tolist());return None
out=repo/'runs/v829_return_saved_diagnosis';out.mkdir(exist_ok=True)
module.emit=lambda cell,name,value:None
s=module.RecoverySupervisor(out);s.path=np.c_[z['reference'],np.ones(len(z['reference']))];s.index=0;s.first_step=491
env=SimpleNamespace(goal_xy=goal,inner=SimpleNamespace(wheel_base=.3,max_steer=.6981317007977318),data=object())
s._try_return_impl(env,None,None,Reserve(),Predictor(),current,z['last_command'],527)
result=dict(worker=a.worker,actual_saved_step=527,top_goal_progress_m=float(distance-np.linalg.norm(rows[0][2][-1,:2]-goal)),eligible_saved_forecasts=len(eligible),eligible_distinct_commands=len({tuple(x[1])for x in eligible}),complete_admission_attempts=len(attempts),new_models=0,new_integrations=0,safety_admission_stub='always reject; no physical feasibility claimed')
print(json.dumps(result),flush=True)
assert attempts,'REAL527_RETURN_SEARCH_SKIPPED_ALL_EXISTING_PROGRESS_ELIGIBLE_CANDIDATES'
