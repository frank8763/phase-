"""One causal full-state observation contract; no prior trajectory commands."""
import gzip,json
import numpy as np
from self_geometry import containment_margin
from instrumentation import dump

class EarlyScan:
    def __init__(self,cell):
        self.cell=cell;self.active=False;self.first_step=None;self.finished_step=None;self.cursor=0;self.certificate=None
    def should_start(self,step,state):
        return step==32 and self.first_step is None and state['center']is None
    def begin(self,env,predictor,field,state,last,step,reserved):
        assert step==32 and state['center']is None and not reserved.executing
        m=predictor.model;mj=predictor.mj;scratch=mj.MjData(m);mj.mj_resetData(m,scratch)
        for n in ['qpos','qvel','act','qacc_warmstart']:getattr(scratch,n)[:]=getattr(env.data,n)
        scratch.time=float(env.data.time);scratch.ctrl[:]=0.;scratch.ctrl[predictor.command_map.ids]=last;mj.mj_forward(m,scratch);scratch.qacc_warmstart[:]=env.data.qacc_warmstart
        pq=[];pv=[];margin=float('inf')
        for _ in range(8):
            predictor.native(m,scratch);predictor.prediction_steps+=1;mj.mj_kinematics(m,scratch);pq.append(scratch.qpos.copy());pv.append(scratch.qvel.copy());margin=min(margin,float(containment_margin(predictor.self_geometry.actual(m,scratch),predictor.domain)))
        target=np.array([0.,0.,8.,-8.]);tail=predictor.predict(scratch,target,predictor.command_map.ids,last,horizon=320,brake_after=160);q=np.vstack([pq,predictor.last_forecast_qpos]);v=np.vstack([pv,predictor.last_forecast_qvel]);yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));poses=np.c_[q[:,:2],yaw];controls=np.vstack([np.repeat([last],8,axis=0),predictor.command_map.sequence(target,last,320,160)]);minimum=float(field.trajectory_values(poses,.01).min());margin=min(margin,predictor.prediction_self_margin);angular=float(np.linalg.norm(v[-1,3:6]));speed=float(np.linalg.norm(v[-1,:2]));checks=dict(clearance=minimum>=.155,self_domain=margin>=.002,terminal_speed=speed<=.025,terminal_angular_speed=angular<=.025)
        dump(self.cell/'OBSERVATION_SCAN_ADMISSION.json',dict(step=step,checks=checks,minimum_causal_clearance_m=minimum,minimum_self_margin_m=margin,terminal_speed_m_s=speed,terminal_angular_speed_rad_s=angular,private_integrations=328,causal_forecast=True,old_saved_commands_used=False))
        assert all(checks.values()),'OBSERVATION_SCAN_NOT_CERTIFIED'
        self.certificate=dict(schema='V735_EARLY_SCAN_01',created_step=step,start_time=float(env.data.time),initial_qpos=env.data.qpos.tolist(),initial_qvel=env.data.qvel.tolist(),prefix_command=np.asarray(last).tolist(),target=target.tolist(),controls=controls.tolist(),qpos=q.tolist(),qvel=v.tolist(),poses=poses.tolist(),forecast_state=state,minimum_causal_predicted_clearance_m=minimum,minimum_predicted_self_domain_margin_m=margin,terminal_speed_m_s=speed,terminal_angular_speed_rad_s=angular,total_native_ticks=328,first_held_command_ticks=8,brake_after_native_ticks=168,hidden_world_geometry_used=False,scope='One early controlled-state development intervention, not a general trigger policy or future-observation safety assumption.')
        with gzip.open(self.cell/'observation_scan_certificate.json.gz','wt')as stream:json.dump(self.certificate,stream)
        reserved.cache=None;reserved.cursor=0;reserved.executing=False;reserved.expected=None;reserved.expected_ctrl=None;reserved.finish_pending=False
        self.first_step=step;self.cursor=0;self.active=True
    def command(self,env,reserved,predictor):
        assert self.active and self.cursor<328;c=self.certificate;i=self.cursor;q=c['initial_qpos']if i==0 else c['qpos'][i-1];v=c['initial_qvel']if i==0 else c['qvel'][i-1]
        assert max(np.max(abs(env.data.qpos-q)),np.max(abs(env.data.qvel-v)))<=1e-8 and abs(env.data.time-c['start_time']-i*.01)<=1e-8,'OBSERVATION_CONTRACT_JOIN_MISMATCH'
        end=i+8;command=np.asarray(c['controls'][i]);reserved.expected=(np.asarray(c['qpos'][end-1]),np.asarray(c['qvel'][end-1]));reserved.expected_ctrl=command.copy();self.cursor=end
        return command,dict(status='OBSERVATION_SCAN_CONTRACT',hidden_world_geometry_used=False,dynamic_time_gate=True,active_gear=None,prediction_horizon_steps=328-i,braking_tail_after_physics_steps=max(0,168-i),terminal_speed_threshold_m_s=.025,predicted_minimum_clearance_m=c['minimum_causal_predicted_clearance_m'],predicted_self_domain_margin_m=c['minimum_predicted_self_domain_margin_m'],contract_native_cursor=i,prediction_steps_total=predictor.prediction_steps,observation_initialization=False)
    def after_public(self,env,step):
        if not self.active or self.cursor!=328:return False
        speed=float(np.linalg.norm(env.data.qvel[:2]));angular=float(np.linalg.norm(env.data.qvel[3:6]));assert max(speed,angular)<=.025,'OBSERVATION_SCAN_DID_NOT_STOP'
        self.active=False;self.finished_step=step;dump(self.cell/'OBSERVATION_SCAN_COMPLETION.json',dict(created_step=self.first_step,finished_step=step,actual_public_steps=41,actual_native_steps=328,actual_terminal_speed_m_s=speed,actual_terminal_angular_speed_rad_s=angular,enable_six_differential_candidates_after_this=True,root_state_writes=0));return True
    def cancel_for_discovery(self,step):
        if self.active:
            self.active=False;dump(self.cell/'OBSERVATION_SCAN_INTERRUPTED_FOR_DISCOVERY.json',dict(step=step,native_cursor=self.cursor,reason='First causal detection takes priority; separate original complete328 brake admission required.'))
