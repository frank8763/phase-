"""Actual admission control-flow tests with an explicitly synthetic no-physics backend."""
import importlib.abc,json,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('QUALIFICATION_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
repo=Path(__file__).resolve().parents[2];own=repo/'experiments/v832_forward_escape_development';sys.path.insert(0,str(own))
import reserved_recovery as module
class MJ:
 def MjData(self,*args):return SimpleNamespace(qpos=np.array([0.,0.,0.,1.,0.,0.,0.]),qvel=np.zeros(6),act=np.zeros(0),qacc_warmstart=np.zeros(6),ctrl=np.zeros(4),time=0.)
 def mj_resetData(self,*args):pass
 def mj_forward(self,*args):pass
 def mj_kinematics(self,*args):pass
mj=MJ();real=mj.MjData(None)
class Command:
 def assert_first(self,c,last):assert np.all(abs(c-last)<=[.1,.1,.7,.7])
 def sequence(self,target,last,horizon,brake):return np.zeros((horizon,4))
class Predictor:
 model=None;domain=np.array([-.44,-.375,.44,.375]);self_geometry=SimpleNamespace(actual=lambda *args:np.array([-.43,-.365,.43,.365]));command_map=Command()
 prediction_steps=0;prediction_self_margin=.01;terminal_speed=0.;last_forecast_qpos=np.repeat([real.qpos],320,axis=0);last_forecast_qvel=np.zeros((320,6))
 def native(self,*args):pass
 def predict(self,data,target,ids,last,horizon,brake_after):self.prediction_steps+=horizon;return np.zeros((horizon,3))
def rejected(*args):return dict(rejected=True,full_values=None,full_minimum_not_evaluated=False,witness_native_tick=328,witness_value_m=0.,checked_native_samples=1)
original=module.evaluate_rejection;module.evaluate_rejection=rejected
try:
 samples=[]
 for allow in[False,True]:
  r=module.ReservedRecovery(Predictor(),mj,range(4),own);r.allow_forward_escape=allow
  assert r.admit_nominal(real,np.zeros(4),None,{},0)is None;samples.append(r.last_attempt['candidates'])
 assert len(samples[0])==21 and len(samples[1])==31
 for a,b in zip(samples[0],samples[1][:21]):assert {k:v for k,v in a.items()if k!='geometry_wall_s'}=={k:v for k,v in b.items()if k!='geometry_wall_s'}
 assert all(x['library']=='RETURN_FORWARD_ESCAPE'and x['brake_after_native_ticks']==160 and x['target_command'][2]in[8.,12.]and x['target_command'][3]==x['target_command'][2]for x in samples[1][21:])
 module.evaluate_rejection=lambda *args:dict(rejected=False,full_values=np.full(328,.2),full_minimum_not_evaluated=False,witness_native_tick=None,witness_value_m=None,checked_native_samples=328)
 r=module.ReservedRecovery(Predictor(),mj,range(4),own);r.allow_forward_escape=True;summary=r.admit_nominal(real,np.zeros(4),None,{},0)
 assert summary['recovery_kind']=='BRAKE_ONLY'and len(r.last_attempt['candidates'])==1,'OLD_LIBRARY_PRIORITY_LOST'
 # New provenance audit must reject an escape that appears in ordinary admission.
 from audit_forward_escape import audit
 root=repo/'runs/forward_escape_night_20261105/qualification';negative=root/'negative_escape/paired';cell=negative/'geometry_memory';cell.mkdir(parents=True)
 (cell/'control_decisions.jsonl').write_text(json.dumps(dict(step=0,stage='BACKUP_APPEND',candidate_role='ORDINARY',detail=dict(candidates=samples[1])))+'\n')
 try:audit(negative)
 except AssertionError:rejected_negative=True
 else:rejected_negative=False
 assert rejected_negative
 result=dict(passed=True,ordinary_library_candidates=21,return_library_candidates=31,old21_order_exact=True,old_brake_only_priority_preserved=True,new10_brake160_registered=True,ordinary_escape_negative_rejected=True,synthetic_backend_not_feasibility=True,models=0,integrations=0)
 (root/'LIBRARY_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
finally:module.evaluate_rejection=original
