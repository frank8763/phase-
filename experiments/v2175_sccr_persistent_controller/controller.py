"""Pure persistent controller protocol; no numerical backend or physical authority."""
from pathlib import Path
import importlib.util,sys,copy,json,hashlib,math
import numpy as np
R=Path(__file__).resolve().parents[2]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
inner=load('sccr_cp_original_inner',R/'experiments/v2173_sccr_inner_control_readout/readout.py')
risk=load('sccr_cp_original_risk',R/'experiments/v2171_sccr_control_contract_readout/study.py')
# No sys.path mutation or ambiguous global module named domain.
assembly=load('sccr_cp_complete_observation',R/'experiments/v2170_sccr_live_source_scope/assemble.py')
domain=load('sccr_cp_domain_base',R/'experiments/v2174_shared_virtual_command_domain/domain.py')
IDENTITY='SCCR_CP_SHARED_ROUTE_V1'
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def projection(x):
 y=domain.project(x)
 for k in ['raw_bicycle_velocity_m_s','raw_bicycle_curvature_m_inv','raw_bicycle_yaw_rate_rad_s','projected_curvature_m_inv','speed_delta_m_s','curvature_delta_m_inv']:
  if not math.isfinite(y[k]):raise ValueError('NONFINITE_DERIVED_TRACE:'+k)
 return y

def measured(packet):
 required={'body','native_tick','sim_time'}
 if type(packet)is not dict or not required<=set(packet):raise ValueError('MEASURED_PACKET_SCHEMA')
 b=packet['body'];k=packet['native_tick'];t=packet['sim_time']
 if type(k)is not int or k<0 or k%5 or type(t)not in(int,float)or not math.isfinite(t)or abs(t-.01*k)>1e-8:raise ValueError('MEASURED_NATIVE_CLOCK')
 if type(b)is not list or len(b)!=5 or any(type(x)not in(int,float)or not math.isfinite(x)for x in b):raise ValueError('MEASURED_BODY')
 return b,k,float(t)

class Controller:
 def __init__(self,episode_id):
  if type(episode_id)is not str or not episode_id:raise ValueError('EPISODE_ID')
  self.episode_id=episode_id;self.pending=None;self.poisoned=False;self.closed=False;self.expected_native=0
  self.outer=None;self.leaf=None;self.previous_virtual=[0.,0.];self.previous_commit=None;self.proposals=0;self.commits=0;self.path_digest=None
 def alive(self):
  if self.poisoned or self.closed:raise ValueError('CLOSED_OR_POISONED_CONTROLLER')
 def fail(self,e):
  self.poisoned=True;raise e
 def previous_action(self):
  self.alive()
  if self.pending is not None:raise ValueError('PREVIOUS_ACTION_UNCOMMITTED')
  return {'virtual_action':self.previous_virtual.copy(),'units':'virtual_steer_rad_and_wheel_rad_s','commit':copy.deepcopy(self.previous_commit),'episode_id':self.episode_id}
 def propose(self,record,*,episode_id):
  try:
   self.alive()
   if episode_id!=self.episode_id:raise ValueError('FOREIGN_EPISODE')
   if self.pending is not None:raise ValueError('PENDING_PROPOSAL_NOT_COMMITTED')
   p=record['sensor_packet'];risk.validate_packet(p)
   if digest(p)!=record['sensor_packet_sha256']:raise ValueError('SENSOR_PACKET_HASH')
   b,k,t=measured(dict(body=p['body'],native_tick=p['native'],sim_time=p['sim_time']))
   if k!=self.expected_native:raise ValueError('STALE_OR_SKIPPED_PROPOSAL_NATIVE')
   rb,rk,rt=measured(record['receipt']['packet'])
   if rb!=b or rk!=k or rt!=t:raise ValueError('SENSOR_RECEIPT_ORIGIN_MISMATCH')
   if p['previous_body_command']!=self.previous_virtual:raise ValueError('PREVIOUS_VIRTUAL_ACTION_NOT_COMMITTED')
   proof=p['producer_proof']
   if proof.get('previous_action_units')!='virtual_steer_rad_and_wheel_rad_s' or not proof.get('actual_fresh_sensor')or not proof.get('no_hidden_actor_truth')or proof.get('native')!=k:raise ValueError('SENSOR_SOURCE_PROOF')
   if proof.get('episode_id')!=episode_id or proof.get('previous_action_commit')!=self.previous_commit:raise ValueError('PREVIOUS_ACTION_EPISODE_OR_PREFIX_PROOF')
   path_hash=digest(p['path_world'])
   if self.path_digest is None:self.path_digest=path_hash
   if path_hash!=self.path_digest:raise ValueError('UNREGISTERED_SHARED_ROUTE_CHANGE')
   a=np.asarray(record['residual_action'],dtype=np.float32);base=np.asarray(record['assembly']['base_action_2'],dtype=np.float32)
   obs=np.asarray(record['observation186'],dtype=float)
   if a.shape!=(2,)or base.shape!=(2,)or obs.shape!=(186,)or not(np.isfinite(a).all()and np.isfinite(base).all()and np.isfinite(obs).all())or max(float(abs(a).max()),float(abs(base).max()))>1.000001:raise ValueError('POLICY_INPUT_OR_OUTPUT_DOMAIN')
   rebuilt,parts=assembly.build(np,p,lambda _:base.copy())
   if not np.array_equal(rebuilt,obs.astype(np.float32))or parts!=record['assembly']:raise ValueError('FULL_POLICY_INPUT_ARITHMETIC_MISMATCH')
   counts=record['model_counts']
   if counts['forward_attempts']!=counts['forward_returns']or counts['inflight']is not None:raise ValueError('POLICY_FORWARD_INCOMPLETE')
   if self.outer is None:self.outer,self.leaf=inner.bind(p,base.tolist())
   o,z=self.outer,self.leaf
   # Fresh read-only measurement binding; persistent controller state is never reconstructed/reset.
   z.robot_xy=np.asarray(b[:2],dtype=np.float32);z.robot_yaw=float(b[2]);z.goal_xy=np.asarray(p['goal_xy'],dtype=np.float32)
   z.path_world=np.asarray(p['path_world'],dtype=np.float32);z.dense_path=z.path_world.copy();z.lidar36=np.asarray(p['core_lidar36_raw_m'],dtype=np.float32)
   o._base_action=lambda _:base.copy();o._phase14_apply_p10p11_params()
   rs=risk.shell(p);rs._phase21_compute_corridor_state();safe=rs._phase17_apply_safety_shield(a)
   trace=o.step(np.clip(safe,-1.,1.)*float(o.phase14_assist_scale))
   virtual=[trace['virtual_steer_rad'],trace['virtual_wheel_rad_s']]
   projected=projection(dict(virtual_steer_rad=virtual[0],virtual_wheel_rad_s=virtual[1],wheel_radius_m=z.wheel_radius,wheelbase_m=z.wheel_base))
   token=digest(dict(episode_id=episode_id,native=k,packet_sha256=record['sensor_packet_sha256'],virtual=virtual,request=projected['request']))
   self.pending=dict(token=token,origin_native=k,origin_sim_time=t,request=projected['request'],virtual=virtual,packet_sha256=record['sensor_packet_sha256'])
   self.proposals+=1
   return dict(identity=IDENTITY,episode_id=episode_id,token=token,origin_native=k,origin_sim_time=t,request=projected['request'],projection=projected,
               virtual=virtual,source_inner_motor_trace=trace,risk=float(rs.phase21_last_risk),shield_reason=rs.phase17_shield_reason,
               recovery_stage=z.recovery_stage,recovery_timer=z.recovery_timer,controller_memory=self.memory(),physical_authority=False)
  except BaseException as e:self.fail(e)
 def commit(self,packet,*,episode_id,token,applied_rows):
  try:
   self.alive()
   if episode_id!=self.episode_id or self.pending is None or token!=self.pending['token']:raise ValueError('FOREIGN_OR_MISSING_COMMIT')
   b,k,t=measured(packet);pending=self.pending
   if k!=pending['origin_native']+5 or abs(t-pending['origin_sim_time']-.05)>1e-8:raise ValueError('COMMIT_NATIVE_OR_CLOCK')
   if type(applied_rows)is not list or len(applied_rows)!=5:raise ValueError('INCOMPLETE_APPLIED_PREFIX')
   for i,row in enumerate(applied_rows):
    if type(row)is not dict or set(row)!={'episode_id','before_native','request','applied'}or row['episode_id']!=episode_id or row['before_native']!=pending['origin_native']+i or row['request']!=pending['request']or row['applied']is not True:raise ValueError('APPLIED_PREFIX_MISMATCH')
   # Original Residual.step updates this from post-physics info['goal_dist']; use its measured equivalent.
   self.leaf.robot_xy=np.asarray(b[:2],dtype=np.float32);self.leaf.robot_yaw=float(b[2]);self.leaf.prev_goal_dist_residual=float(self.leaf._goal_distance())
   self.previous_virtual=pending['virtual'].copy();self.previous_commit=dict(token=token,origin_native=pending['origin_native'],end_native=k,applied_prefix_sha256=digest(applied_rows),episode_id=episode_id)
   self.expected_native=k;self.commits+=1;self.pending=None
   return self.previous_action()
  except BaseException as e:self.fail(e)
 def memory(self):
  if self.leaf is None:return None
  z=self.leaf
  return dict(recovery_stage=z.recovery_stage,recovery_timer=z.recovery_timer,path_stuck_counter=z.path_stuck_counter,
              prev_goal_dist_residual=z.prev_goal_dist_residual,motor_arithmetic_memory=[z.last_lf_steer,z.last_rf_steer,z.last_lr_wheel,z.last_rr_wheel],
              proposals=self.proposals,commits=self.commits)
 def close(self):
  self.closed=True
