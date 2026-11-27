"""No tensor/module/weight deserialization until exact CPU2 source authority."""
from common import R,sha,authority
import io,json,zipfile
SPECS={107:('runtime/mk-mini/training/phase6_clean/confirmed/phase6_v1_lidar_main_camera_goal_55k_confirmed.zip','75f6ad4e6c522fd5caa881fb2672754499616f4b0550d109d55c560ba481665a'),186:('runtime/mk-mini/training/phase20_unknown_obstacle_adaptation/checkpoints/stage_b_randomized/phase20_stage_b_325000_steps.zip','4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f')}
class FrozenActor:
 def __init__(self,dimension):
  self.authority,self.files=authority();assert dimension in SPECS;self.dimension=dimension;self.calls=0;self.returns=0;self.seen=set();self.poisoned=False;self.inflight=False
  name,wanted=SPECS[dimension];path=R/name;assert sha(path)==wanted and self.files[name]==wanted
  import torch
  self.torch=torch;torch.set_num_threads(1)
  with zipfile.ZipFile(path)as z:
   metadata=json.loads(z.read('data'));assert metadata['policy_kwargs']=={'net_arch':[256,256],'use_sde':False}and metadata['use_sde']is False
   state=torch.load(io.BytesIO(z.read('policy.pth')),map_location='cpu',weights_only=True)
  mapping={'0.weight':'actor.latent_pi.0.weight','0.bias':'actor.latent_pi.0.bias','2.weight':'actor.latent_pi.2.weight','2.bias':'actor.latent_pi.2.bias','4.weight':'actor.mu.weight','4.bias':'actor.mu.bias'}
  assert tuple(state[mapping['0.weight']].shape)==(256,dimension)and all(state[k].dtype==torch.float32 for k in mapping.values())
  n=torch.nn;self.actor=n.Sequential(n.Linear(dimension,256),n.ReLU(),n.Linear(256,256),n.ReLU(),n.Linear(256,2),n.Tanh())
  self.actor.load_state_dict({k:state[v]for k,v in mapping.items()},strict=True);self.actor.requires_grad_(False);self.actor.eval();self.state=state;self.weights_sha256=wanted
 def predict_component(self,features,*,receipt_id):
  assert not self.poisoned and receipt_id not in self.seen and self.calls<3,'SCCR_ACTOR_DUPLICATE_POISON_OR_COUNT'
  import numpy as np
  x=np.asarray(features,np.float32);assert x.shape==(self.dimension,)and np.isfinite(x).all(),'SCCR_ACTOR_INPUT_DIM_OR_FINITE'
  self.poisoned=True;self.inflight=True;self.seen.add(receipt_id);self.calls+=1
  with self.torch.inference_mode():y=self.actor(self.torch.from_numpy(x)).cpu().numpy()
  assert y.shape==(2,)and np.isfinite(y).all()and(abs(y)<=1).all()
  self.returns+=1;self.inflight=False;self.poisoned=False;return y
