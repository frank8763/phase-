"""Source-authorized dual frozen actors on saved input, no plant or training."""
from common import *
import traceback,signal,importlib.abc

def main():
 a,files=authority();assert not(O/'WORKER_ONCE.json').exists();dump(O/'WORKER_ONCE.json',dict(pid=os.getpid(),unix=time.time(),physical_models=0))
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,n,*_):
   if n.split('.')[0]in {'mujoco','jax','factory','vehicle','kernel','fast_predict','OpenGL','rclpy'}:raise AssertionError('SCCR_ACTOR_COMPONENT_NO_PLANT:'+n)
 from environment_guard import PinnedLibraries
 sys.meta_path.insert(0,PinnedLibraries());sys.meta_path.insert(0,Ban());signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SCCR_DUAL_ACTOR_COMPONENT_TIMEOUT')));signal.setitimer(signal.ITIMER_REAL,a['absolute_end_unix']-time.time())
 import numpy as np,torch,importlib.metadata
 from actors import FrozenActor
 from saved_inputs import packet,observation
 from gymnasium.spaces import Box
 from stable_baselines3.sac.policies import SACPolicy
 assert importlib.metadata.version('stable-baselines3')=='2.9.0'
 result=dict(passed=False,closed=False,physical_models=0,physics=0,replay=0,training_updates=0,formal_tasks=0,explicit_direct_actor_constructors=0,explicit_SB3_reference_policy_constructors=0,weight_deserializations=0,internal_torch_network_modules_and_operations=None,direct_forward_calls={107:0,186:0},reference_batch_forward_calls={107:0,186:0},first_error=None,constructor_inflight=None,reference_inflight=None,forward_inflight=None,constructor_attempts=0)
 try:
  direct={};references={}
  for d in [107,186]:
   result['constructor_attempts']+=1;result['constructor_inflight']=d;dump(O/'INFERENCE_PROGRESS.json',result)
   direct[d]=FrozenActor(d);result['constructor_inflight']=None;result['explicit_direct_actor_constructors']+=1;result['weight_deserializations']+=1
   result['reference_inflight']='constructor_'+str(d);dump(O/'INFERENCE_PROGRESS.json',result)
   ref=SACPolicy(Box(-np.inf,np.inf,shape=(d,),dtype=np.float32),Box(-1.,1.,shape=(2,),dtype=np.float32),lambda _:0.,net_arch=[256,256],use_sde=False);ref.load_state_dict(direct[d].state,strict=True);ref.set_training_mode(False);ref.requires_grad_(False);references[d]=ref;result['explicit_SB3_reference_policy_constructors']+=1;result['reference_inflight']=None;dump(O/'INFERENCE_PROGRESS.json',result)
  negative=[]
  for d in [107,186]:
   for label,x in [('dimension',np.zeros(d+1,np.float32)),('nonfinite',np.full(d,np.nan,np.float32))]:
    try:direct[d].predict_component(x,receipt_id='preflight_invalid_'+label)
    except AssertionError:negative.append(str(d)+'_'+label)
    else:raise AssertionError('INVALID_ACTOR_INPUT_ACCEPTED')
   assert direct[d].calls==direct[d].returns==0 and not direct[d].poisoned
  inputs={107:[],186:[]};outputs={107:[],186:[]};cases=[]
  for index in range(3):
   p=packet(np,index);assert not p['producer_proof']['actual_fresh_sensor'];seen=[]
   def provider(x):
    inputs[107].append(x.copy());result['forward_inflight']=[107,index];dump(O/'INFERENCE_PROGRESS.json',result);y=direct[107].predict_component(x,receipt_id=str(index));result['forward_inflight']=None;outputs[107].append(y.copy());result['direct_forward_calls'][107]+=1;dump(O/'INFERENCE_PROGRESS.json',result);seen.append(True);return y
   obs,parts=observation(np,p,provider);assert len(seen)==1;inputs[186].append(obs.copy());result['forward_inflight']=[186,index];dump(O/'INFERENCE_PROGRESS.json',result);y=direct[186].predict_component(obs,receipt_id=str(index));outputs[186].append(y.copy());result['direct_forward_calls'][186]+=1;result['forward_inflight']=None;dump(O/'INFERENCE_PROGRESS.json',result)
   dump(O/f'CASE_{index:02d}_RESULT.json',dict(native=5*index,inputs={107:inputs[107][-1],186:obs},actions={107:outputs[107][-1],186:y},original_phase6_actor_used_in_base_block=True,Phase21_fusion_executed=False,TRACK_mode_component_fixture=True,not_real_fresh_policy_input=True,physical_authority=False))
   cases.append(dict(native=5*index,actor107_action=outputs[107][-1].tolist(),actor186_action=y.tolist(),observation186_sha256=__import__('hashlib').sha256(obs.tobytes()).hexdigest()))
  parity={}
  for d in [107,186]:
   result['reference_inflight']='forward_'+str(d);dump(O/'INFERENCE_PROGRESS.json',result)
   with torch.inference_mode():expected=references[d].actor(torch.from_numpy(np.stack(inputs[d])),deterministic=True).cpu().numpy()
   result['reference_batch_forward_calls'][d]+=1;result['reference_inflight']=None;dump(O/'INFERENCE_PROGRESS.json',result);got=np.stack(outputs[d]);error=float(abs(expected-got).max());assert error<=1e-6,'FROZEN_ACTOR_SB3_EQUIVALENCE_REFUSED'
   parity[d]=dict(max_absolute_action_error=error,byte_exact=bool(np.array_equal(expected,got)),direct_actions=got.tolist(),reference_actions=expected.tolist(),weights_sha256=direct[d].weights_sha256)
   for label,x,rid in [('duplicate',inputs[d][0],'0'),('count_cap',inputs[d][0],'extra')]:
    try:direct[d].predict_component(x,receipt_id=rid)
    except AssertionError:negative.append(str(d)+'_'+label)
    else:raise AssertionError('ACTOR_ONCE_NEGATIVE_ACCEPTED')
  result.update(passed=True,parity=parity,cases=cases,negative_cases=negative,full_SCCR_or_navigation_qualified=False,live_sensor_and_risk_fusion_pending=True,all_source_SHA_after=all(sha(R/n)==h for n,h in files.items()))
  assert result['all_source_SHA_after']
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 result['closed']=True;result['actor_final_counters']={d:dict(attempts=v.calls,returns=v.returns,inflight=v.inflight,poisoned=v.poisoned)for d,v in direct.items()};result['all_source_SHA_after']=all(sha(R/n)==h for n,h in files.items());dump(O/'RESULT.json',result);print(json.dumps(dict(passed=result['passed'],closed=True,direct_calls=result['direct_forward_calls'],reference_calls=result['reference_batch_forward_calls'],physical_native=0,full_SCCR_qualified=False)));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
