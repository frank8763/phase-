"""Synthetic actual-admission seam: new full certificate and public goal rejection, zero physics."""
import importlib.abc,sys,json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('QUALIFICATION_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels());repo=Path(__file__).resolve().parents[2];own=repo/'experiments/v834_timed_escape_development';sys.path.insert(0,str(own));import reserved_recovery as module
class MJ:
 def MjData(self,*args):return SimpleNamespace(qpos=np.array([0.,0.,0.,1.,0.,0.,0.]),qvel=np.zeros(6),act=np.zeros(0),qacc_warmstart=np.zeros(6),ctrl=np.zeros(4),time=0.)
 def mj_resetData(self,*args):pass
 def mj_forward(self,*args):pass
 def mj_kinematics(self,*args):pass
mj=MJ();real=mj.MjData(None)
class Commands:
 def assert_first(self,*args):pass
 def sequence(self,target,last,horizon,brake):return np.zeros((horizon,4))
class Predictor:
 model=None;domain=np.array([-.44,-.375,.44,.375]);self_geometry=SimpleNamespace(actual=lambda *args:np.array([-.43,-.365,.43,.365]));command_map=Commands();prediction_steps=0;prediction_self_margin=.01;terminal_speed=0.
 def native(self,*args):pass
 def predict(self,data,target,ids,last,horizon,brake_after):
  self.prediction_steps+=horizon;self.last_forecast_qpos=np.repeat([real.qpos],horizon,axis=0);self.last_forecast_qpos[:,0]=.2;self.last_forecast_qvel=np.zeros((horizon,6));return np.c_[np.full(horizon,.2),np.zeros((horizon,2))]
original=module.evaluate_rejection;reports=[]
try:
 for goal,expect in[(np.array([10.,0.]),True),(np.array([-10.,0.]),False)]:
  calls=[0]
  def evaluate(*args):
   calls[0]+=1;reject=calls[0]<=21
   return dict(rejected=reject,full_values=None if reject else np.full(328,.2),full_minimum_not_evaluated=False,witness_native_tick=328 if reject else None,witness_value_m=0. if reject else None,checked_native_samples=1 if reject else 328)
  module.evaluate_rejection=evaluate;r=module.ReservedRecovery(Predictor(),mj,range(4),own);r.allow_forward_escape=True;r.escape_goal_xy=goal;summary=r.admit_nominal(real,np.zeros(4),None,{},0)
  assert bool(summary is not None)==expect and len(r.last_attempt['candidates'])==166
  if expect:assert summary['recovery_kind']=='FORWARD_TIMED_ESCAPE_BRAKE'and r.cache['brake_after_native_ticks']in[160,176,192,208,224,240]and r.cache['minimum_causal_predicted_clearance_m']==.2
  else:assert all(c['reason']=='ESCAPE_NO_GOAL_PROGRESS'for c in r.last_attempt['candidates'][21:])
  reports.append(dict(public_goal=goal.tolist(),accepted=expect,full328_required=True,new_library_count=145))
 result=dict(passed=True,records=reports,actual_admission_selection_and_goal_gate_exercised=True,synthetic_interface_only_not_physical_feasibility=True,models=0,integrations=0)
 (repo/'runs/timed_escape_night_20261105/qualification/TIMED_GATE_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
finally:module.evaluate_rejection=original
