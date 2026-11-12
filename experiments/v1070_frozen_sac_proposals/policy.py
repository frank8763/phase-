"""Frozen Phase6 + Phase20 SAC inference. No environment or optimizer is loaded."""
import hashlib,io,zipfile
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
PHASE20=R/'runtime/mk-mini/training/phase20_unknown_obstacle_adaptation/checkpoints/stage_b_randomized/phase20_stage_b_325000_steps.zip'
PHASE6=R/'runtime/mk-mini/training/phase6_clean/confirmed/phase6_v1_lidar_main_camera_goal_55k_confirmed.zip'
EXPECTED6='75f6ad4e6c522fd5caa881fb2672754499616f4b0550d109d55c560ba481665a'
EXPECTED20='4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f'
class FrozenActor:
 def __init__(self,path,dimension):
  import torch
  path=Path(path);self.sha256=hashlib.sha256(path.read_bytes()).hexdigest();self.dimension=dimension
  if path==PHASE20:assert self.sha256==EXPECTED20,'FROZEN_PHASE20_CHANGED'
  if path==PHASE6:assert self.sha256==EXPECTED6,'FROZEN_PHASE6_CHANGED'
  with zipfile.ZipFile(path)as z:state=torch.load(io.BytesIO(z.read('policy.pth')),map_location='cpu',weights_only=True)
  names=['actor.latent_pi.0','actor.latent_pi.2','actor.mu'];self.layers=[]
  for name in names:
   w=state[name+'.weight'].detach().cpu().numpy().copy();b=state[name+'.bias'].detach().cpu().numpy().copy();w.flags.writeable=False;b.flags.writeable=False;self.layers.append((w,b))
  assert self.layers[0][0].shape[1]==dimension and self.layers[-1][0].shape[0]==2,'LEGACY_POLICY_SCHEMA_CHANGED'
 def predict(self,observation):
  x=np.asarray(observation,dtype=np.float32);assert x.ndim in [1,2]and x.shape[-1]==self.dimension and np.isfinite(x).all(),'EXACT_FINITE_OBSERVATION_REQUIRED'
  for index,(w,b)in enumerate(self.layers):
   x=x@w.T+b;x=np.maximum(x,0)if index<2 else np.tanh(x)
  return x
class SACProposer:
 def __init__(self):self.base=FrozenActor(PHASE6,107);self.residual=FrozenActor(PHASE20,186)
 def predict(self,observation):
  obs=np.asarray(observation,dtype=np.float32);assert obs.shape==(186,)and np.isfinite(obs).all(),'EXACT_186_MEASURED_FEATURES_REQUIRED'
  base=self.base.predict(obs[:107]);residual=self.residual.predict(obs);action=np.clip(base+.18*residual,-1.,1.)
  return dict(base_phase6_action=base.tolist(),phase20_residual_action=residual.tolist(),combined_normalized_action=action.tolist(),policy_sha256=self.residual.sha256,base_policy_sha256=self.base.sha256,training_updates=0,executed=False,role='LEARNED_NOMINAL_PROPOSAL_ONLY')
