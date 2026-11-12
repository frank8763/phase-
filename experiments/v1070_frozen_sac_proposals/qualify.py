"""Policy parity + real saved-state safety seam; zero vehicle models/integrations."""
import importlib.abc,sys,time,json
from pathlib import Path
class NoPhysics(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy'}:raise AssertionError('NO_VEHICLE_MODELS '+name)
sys.meta_path.insert(0,NoPhysics());C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1070_frozen_sac_proposals';sys.path.insert(0,str(C))
import numpy as np,torch
from policy import FrozenActor,SACProposer,PHASE20,PHASE6
from observation import BLOCKS,assemble
from integration import ShieldedSAC
from stable_baselines3 import SAC
started=time.monotonic();torch.set_num_threads(1);rng=np.random.default_rng(1070);parity=[]
for path,dim in [(PHASE6,107),(PHASE20,186)]:
 fast=FrozenActor(path,dim);reference=SAC.load(str(path),device='cpu');obs=rng.uniform(-1,1,(257,dim)).astype(np.float32);expected=reference.predict(obs,deterministic=True)[0];actual=fast.predict(obs);error=float(np.max(abs(expected-actual)));assert error<=2e-6;parity.append(dict(dimension=dim,max_action_error=error,policy_sha256=fast.sha256));del reference
shield=ShieldedSAC();blocks={key:np.zeros(size,np.float32)for key,size in BLOCKS.items()}
for key in ['lidar','phase7_depth','outer_lidar','outer_depth']:blocks[key].fill(1)
x=json.loads((R/'experiments/v1068_recovery_value_diagnosis/fixtures/NS_ACTUAL_INPUT.json').read_text());n=x['packet']['native_tick'];obs=assemble(blocks,shield.policy.base,n,n);assert obs.shape==(186,)
result=shield.propose(x['setup'],x['packet'],x['source'],blocks,n,[.08,0.,False]);assert result['certificate']is None or len(result['certificate']['planned_body_requests'])==2205
negatives=[]
for name,b,stamp in [('missing_depth',{k:v for k,v in blocks.items()if k!='outer_depth'},n),('stale_measurement',blocks,n-1),('privileged_actor_input',dict(blocks,actor_truth=np.zeros(2)),n),('wrong_dimensions',dict(blocks,lidar=np.zeros(31)),n)]:
 try:assemble(b,shield.policy.base,n,stamp);raise RuntimeError('NEGATIVE_ACCEPTED '+name)
 except AssertionError:negatives.append(name)
try:shield.policy.predict(np.zeros(32));raise RuntimeError('WRONG_RAW_LIDAR_ACCEPTED')
except AssertionError:negatives.append('raw32_as186')
full=np.vstack([np.tile([.08,0.,False],(5,1)),np.zeros((2200,3))]);goal_check=shield.propose_goal_profile(x['setup'],x['packet'],x['source'],blocks,n,full,np.asarray(x['goal']));assert not goal_check['admitted']and goal_check['functional_goal_success']is False;negatives.append('finite_stop_is_not_original_goal')
try:shield.propose_goal_profile(x['setup'],x['packet'],x['source'],blocks,n,full[:-1],np.asarray(x['goal']));raise RuntimeError('TRUNCATED_STOP_ACCEPTED')
except AssertionError:negatives.append('truncated_complete_stop')
out=dict(passed=True,policy_parity=parity,negative_cases=negatives,observation_assembly='Exact layout on synthetic feature blocks only; not actual186-channel sensing',actual_saved_vehicle_state_used=True,synthetic_policy_observation=True,safety_gate_admitted=result['admitted'],safety_gate_checks=None if result['certificate']is None else result['certificate']['checks'],counts=result['counts'],vehicle_model_initializations=0,vehicle_integrations=0,training_updates=0,policy_networks=2,physical_ready=False,live_observation_backend_qualified=False,wall_s=time.monotonic()-started);(O/'QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
