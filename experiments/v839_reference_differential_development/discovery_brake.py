"""One finite full-state 328-native-tick stop at first causal detection."""
import gzip,json
import numpy as np
from instrumentation import dump

class DiscoveryBrake:
 def __init__(self,cell):
  self.cell=cell;self.first_step=None;self.certificate=None;self.cursor=0;self.active=False;self.finished_step=None;self.finished_speed=None
 def begin(self,env,predictor,field,state,last,step,rows,path,index,reserved):
  assert self.first_step is None and state['center']is not None
  speed=float(np.linalg.norm(env.data.qvel[:2]));progress=float(np.linalg.norm(env.data.qpos[:2]-__import__('unseen_prior').ORIGIN))
  # Normal movement is checked from already executed full public states,
  # never a requested command or a scene-time trigger.
  executed=[json.loads(s)for s in(self.cell/'v648_execution.jsonl').read_text().splitlines()]
  moving=len(executed)>=10 and all(np.linalg.norm(np.asarray(x['qvel_full'])[:2])>=.10 for x in executed[-10:])
  discovery={'step':step,'time':float(env.data.time),'speed_before_m_s':speed,'forward_progress_before_m':progress,'last10_actual_states_moving':bool(moving),'qpos':env.data.qpos.tolist(),'qvel':env.data.qvel.tolist(),'ctrl':env.data.ctrl.tolist(),'old_path':None if path is None else np.asarray(path).tolist(),'old_path_index':index,'old_backup_executing':bool(reserved.executing),'causal_state':state,'trigger':'first certified sensor unknown ray only','hidden_truth_trigger':False,'progress_metric':'Euclidean displacement from declared public initial robot origin'}
  dump(self.cell/'FIRST_DISCOVERY.json',discovery)
  assert progress>=.30 and speed>=.15 and moving,'DISCOVERY_NOT_DURING_REGISTERED_NORMAL_MOTION'
  target=np.r_[np.asarray(last)[:2],0.,0.]
  poses=predictor.predict(env.data,target,predictor.command_map.ids,last,horizon=328,brake_after=0)
  minimum=float(np.min(field.trajectory_values(poses,.01)));margin=float(predictor.prediction_self_margin);terminal=float(predictor.terminal_speed)
  checks={'minimum_clearance':minimum>=.155,'self_domain':margin>=.002,'terminal_speed':terminal<=.025}
  dump(self.cell/'DISCOVERY_BRAKE_ADMISSION.json',{'step':step,'checks':checks,'minimum_clearance_m':minimum,'self_domain_margin_m':margin,'terminal_speed_m_s':terminal,'private_native_steps':328})
  assert all(checks.values()),'DISCOVERY_BRAKE_NOT_CERTIFIED'
  controls=predictor.command_map.sequence(target,last,328,0)
  self.certificate={'created_step':step,'start_time':float(env.data.time),'initial_qpos':env.data.qpos.tolist(),'initial_qvel':env.data.qvel.tolist(),'prefix_command':np.asarray(last).tolist(),'target':target.tolist(),'controls':controls.tolist(),'qpos':predictor.last_forecast_qpos.tolist(),'qvel':predictor.last_forecast_qvel.tolist(),'poses':poses.tolist(),'forecast_state':state,'minimum_causal_predicted_clearance_m':minimum,'minimum_predicted_self_domain_margin_m':margin,'terminal_speed_m_s':terminal,'total_native_ticks':328,'brake_after_native_ticks':0,'hidden_world_geometry_used':False}
  with gzip.open(self.cell/'discovery_stop_certificate.json.gz','wt')as stream:json.dump(self.certificate,stream)
  # Commit only after the complete new proof is admitted from the real state.
  reserved.cache=None;reserved.cursor=0;reserved.executing=False;reserved.expected=None;reserved.expected_ctrl=None;reserved.finish_pending=False
  self.first_step=step;self.cursor=0;self.active=True
 def command(self,env,reserved,predictor):
  c=self.certificate;i=self.cursor;assert self.active and i<328
  q=c['initial_qpos']if i==0 else c['qpos'][i-1];v=c['initial_qvel']if i==0 else c['qvel'][i-1]
  assert max(np.max(abs(env.data.qpos-q)),np.max(abs(env.data.qvel-v)))<=1e-8,'DISCOVERY_BRAKE_STATE_MISMATCH'
  assert abs(env.data.time-c['start_time']-i*.01)<=1e-8,'DISCOVERY_BRAKE_TIME_MISMATCH'
  end=i+8;command=np.asarray(c['controls'][i]);reserved.expected=(np.asarray(c['qpos'][end-1]),np.asarray(c['qvel'][end-1]));reserved.expected_ctrl=command.copy();self.cursor=end
  gate={'status':'DISCOVERY_BRAKE_CONTRACT','hidden_world_geometry_used':False,'dynamic_time_gate':True,'active_gear':None,'prediction_horizon_steps':328-i,'braking_tail_after_physics_steps':0,'terminal_speed_threshold_m_s':.025,'predicted_minimum_clearance_m':c['minimum_causal_predicted_clearance_m'],'predicted_self_domain_margin_m':c['minimum_predicted_self_domain_margin_m'],'contract_native_cursor':i,'prediction_steps_total':predictor.prediction_steps,'first_detection_step':self.first_step,'observation_initialization':False}
  return command,gate
 def after_public(self,env,step):
  if not self.active or self.cursor!=328:return False
  self.finished_speed=float(np.linalg.norm(env.data.qvel[:2]));assert self.finished_speed<=.025,'DISCOVERY_STOP_NOT_REACHED'
  self.active=False;self.finished_step=step
  dump(self.cell/'DISCOVERY_BRAKE_COMPLETION.json',{'first_detection_step':self.first_step,'finished_step':step,'actual_public_steps':41,'actual_native_steps':328,'actual_terminal_speed_m_s':self.finished_speed,'full_stop_before_replanning':True,'integrations_outside_native':0})
  return True
