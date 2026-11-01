"""Finite native-certified recovery tail, retained across one nominal action."""
import gzip,json,math
from pathlib import Path
import numpy as np
from self_geometry import containment_margin

class ReservedRecovery:
    def __init__(self,predictor,mj,ids,cell):
        self.predictor=predictor;self.mj=mj;self.ids=list(ids);self.cell=Path(cell)
        self.scratch=mj.MjData(predictor.model);self.cache=None;self.cursor=0;self.executing=False
        self.expected=None;self.finish_pending=False;self.activations=0;self.executed_steps=0
        self.last_attempt=None;self.handovers=0;self.expected_ctrl=None
    @staticmethod
    def poses(q):
        q=np.asarray(q);yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
        return np.c_[q[:,:2],yaw]
    @staticmethod
    def target(steer,wheel):
        if abs(steer)<1e-9:return np.array([0.,0.,wheel,wheel])
        r=.60/math.tan(abs(steer));inner=math.atan2(.60,r-.27);outer=math.atan2(.60,r+.27)
        return np.array([inner,outer,wheel,wheel]if steer>0 else[-outer,-inner,wheel,wheel])
    def controls(self,target,last):
        return self.predictor.command_map.sequence(target,last,320,160)
    def admit_nominal(self,real,proposal,field,state,step):
        self.predictor.command_map.assert_first(proposal,real.ctrl[self.ids])
        self.last_attempt={'step':int(step),'status':'CHECKING','prefix_self_domain_margin_m':None,'candidates':[]}
        m=self.predictor.model;d=self.scratch;self.mj.mj_resetData(m,d)
        for name in ['qpos','qvel','act','qacc_warmstart']:getattr(d,name)[:]=getattr(real,name)
        d.time=float(real.time);d.ctrl[:]=0.;d.ctrl[self.ids]=proposal
        self.mj.mj_forward(m,d);d.qacc_warmstart[:]=real.qacc_warmstart
        prefix=[];margin=float('inf')
        for _ in range(8):
            self.predictor.native(m,d);self.predictor.prediction_steps+=1
            self.mj.mj_kinematics(m,d);prefix.append(d.qpos.copy())
            margin=min(margin,float(containment_margin(self.predictor.self_geometry.actual(m,d),self.predictor.domain)))
        self.last_attempt['prefix_self_domain_margin_m']=float(margin)
        if margin<.002:
            self.last_attempt['status']='PREFIX_SELF_DOMAIN_REJECTED';return None
        prefix=self.poses(prefix);initial_q=d.qpos.copy();initial_v=d.qvel.copy();self.last_prefix_qpos=initial_q.copy();self.last_prefix_qvel=initial_v.copy();yaw=float(prefix[-1,2]);best=None;safe_count=0
        original=[(None,0.)]+[(steer,wheel)for steer in [-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]for wheel in [-12.,-8.,-4.]]
        forward=[(steer,wheel)for steer in [-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]for wheel in [4.,8.,12.]]
        for library,choices in [('ORIGINAL',original),('FORWARD_EXTENSION',forward)]:
            if library=='FORWARD_EXTENSION'and best is not None:break
            for steer,wheel in choices:
                brake_only=steer is None;kind='BRAKE_ONLY'if brake_only else'FORWARD_BRAKE'if wheel>0 else'REVERSE_BRAKE'
                target=np.r_[proposal[:2],0.,0.]if brake_only else self.target(steer,wheel)
                trajectory=self.predictor.predict(d,target,self.ids,np.asarray(proposal),horizon=320,brake_after=160)
                signed=float((trajectory[-1,:2]-initial_q[:2])@np.array([math.cos(yaw),math.sin(yaw)]))
                values=field.trajectory_values(np.vstack((prefix,trajectory)),.01);minimum=float(np.min(values))
                bodymargin=min(margin,self.predictor.prediction_self_margin)
                reason='TIME_CLEARANCE'if minimum<.155 else'SELF_DOMAIN'if bodymargin<.002 else'TERMINAL_SPEED'if self.predictor.terminal_speed>.025 else'INSUFFICIENT_REVERSE'if kind=='REVERSE_BRAKE'and signed>-.02 else'INSUFFICIENT_FORWARD'if kind=='FORWARD_BRAKE'and signed<.02 else None
                self.last_attempt['candidates'].append({'kind':kind,'library':library,'target_command':target.tolist(),'minimum_clearance_m':minimum,'minimum_clearance_native_tick':int(np.argmin(values))+1,'self_domain_margin_m':float(bodymargin),'terminal_speed_m_s':float(self.predictor.terminal_speed),'signed_displacement_m':signed,'reason':reason})
                if reason is not None:continue
                safe_count+=1;score=minimum+.1*(signed if kind=='FORWARD_BRAKE'else-signed)-.02*abs(steer or 0.)
                if best is not None and score<=best['score']:continue
                best={'score':score,'recovery_kind':kind,'created_step':int(step),'created_time':float(real.time),'start_time':float(d.time),
                    'initial_qpos':initial_q.copy(),'initial_qvel':initial_v.copy(),'prefix_command':np.asarray(proposal).copy(),
                    'qpos':self.predictor.last_forecast_qpos.copy(),'qvel':self.predictor.last_forecast_qvel.copy(),
                    'poses':trajectory.copy(),'controls':self.controls(target,proposal),
                    'forecast_state':json.loads(json.dumps(state)),
                    'minimum_causal_predicted_clearance_m':minimum,'minimum_predicted_self_domain_margin_m':bodymargin,
                    'terminal_speed_m_s':self.predictor.terminal_speed,'signed_reverse_displacement_m':signed,'signed_longitudinal_displacement_m':signed,
                    'target':target.copy(),'prefix_poses':prefix.copy()}
                if brake_only:break
        self.last_attempt['status']='APPENDABLE_BACKUP_FOUND'if best is not None else'NO_APPENDABLE_BACKUP'
        if best is None:return None
        self.cache=best;self.cursor=0;self.expected=(initial_q,initial_v);self.expected_ctrl=np.asarray(proposal).copy();self.finish_pending=False
        return {'status':best['recovery_kind']+'_TAIL_RESERVED','recovery_kind':best['recovery_kind'],'safe_reserve_candidates':safe_count,'reserve_minimum_clearance_m':best['minimum_causal_predicted_clearance_m'],
                'reserve_signed_longitudinal_displacement_m':best['signed_longitudinal_displacement_m'],'reserve_signed_reverse_displacement_m':best['signed_reverse_displacement_m'],'reserve_target':best['target'].tolist(),
                'reserve_total_native_ticks':328,'reserve_braking_after_native_ticks':168,'causal_forecast_horizon_s':3.28}
    def check_current_contract(self,real):
        assert self.executing and self.cache is not None,'NO_ACTIVE_CONTRACT'
        c=self.cache;i=self.cursor
        q=c['initial_qpos']if i==0 else c['qpos'][i-1];v=c['initial_qvel']if i==0 else c['qvel'][i-1]
        qe=float(np.max(abs(real.qpos-q)));ve=float(np.max(abs(real.qvel-v)))
        assert max(qe,ve)<=1e-8,'HANDOVER_OLD_STATE_MISMATCH'
        assert abs(real.time-c['start_time']-i*.01)<=1e-8,'HANDOVER_OLD_TIME_MISMATCH'
        return qe,ve
    def try_handover(self,real,proposal,field,state,step,metadata):
        old=self.cache;old_cursor=self.cursor;old_expected=self.expected
        qe,ve=self.check_current_contract(real)
        candidate=ReservedRecovery(self.predictor,self.mj,self.ids,self.cell)
        summary=candidate.admit_nominal(real,proposal,field,state,step)
        self.last_handover_attempt=candidate.last_attempt
        if summary is None:
            assert self.cache is old and self.cursor==old_cursor and self.expected is old_expected and self.executing,'FAILED_HANDOVER_MUTATED_OLD_CONTRACT'
            return None
        directory=self.cell/'handover_certificates';directory.mkdir(parents=True,exist_ok=True)
        value={k:(v.tolist()if isinstance(v,np.ndarray)else v)for k,v in candidate.cache.items()}
        value.update(handover_step=int(step),old_created_step=int(old['created_step']),old_native_cursor=int(old_cursor),
                     old_state_qpos_error=qe,old_state_qvel_error=ve,real_entry_qpos=real.qpos.tolist(),real_entry_qvel=real.qvel.tolist(),
                     real_entry_time=float(real.time),first_command=np.asarray(proposal).tolist(),metadata=metadata,
                     hidden_world_geometry_used=False,scope='new complete prefix and backup certificate; old backup partially executed')
        file=directory/f'handover_{step:04d}.json.gz'
        with gzip.open(file,'wt')as stream:json.dump(value,stream)
        self.cache=candidate.cache;self.cursor=0;self.expected=candidate.expected;self.finish_pending=False;self.executing=False
        self.expected_ctrl=candidate.expected_ctrl
        self.last_prefix_qpos=candidate.last_prefix_qpos;self.last_prefix_qvel=candidate.last_prefix_qvel
        self.handovers+=1
        return {**summary,'handover_certificate':str(file.name),'old_created_step':int(old['created_step']),'old_native_cursor':int(old_cursor)}
    def start(self,real,step):
        assert self.cache is not None and not self.executing,'NO_RETAINED_RECOVERY_CONTRACT'
        self.executing=True;self.activations+=1
        directory=self.cell/'recovery_contracts';directory.mkdir(parents=True,exist_ok=True)
        value={k:(v.tolist()if isinstance(v,np.ndarray)else v)for k,v in self.cache.items()}
        value.update(activation_step=int(step),actual_initial_time=float(real.time),hidden_world_geometry_used=False,
                     scope='finite retained causal recovery tail; no infinite parking or liveness guarantee')
        with gzip.open(directory/f'contract_{step:04d}.json.gz','wt')as f:json.dump(value,f)
        return self.command(real)
    def command(self,real):
        assert self.executing and self.cache is not None
        c=self.cache;i=self.cursor
        q=c['initial_qpos']if i==0 else c['qpos'][i-1];v=c['initial_qvel']if i==0 else c['qvel'][i-1]
        assert max(np.max(abs(real.qpos-q)),np.max(abs(real.qvel-v)))<=1e-8,'RETAINED_CONTRACT_INITIAL_STATE_MISMATCH'
        assert abs(real.time-c['start_time']-i*.01)<=1e-8,'RETAINED_CONTRACT_TIME_MISMATCH'
        end=min(i+8,320);command=c['controls'][i].copy();self.cursor=end;self.expected=(c['qpos'][end-1],c['qvel'][end-1]);self.finish_pending=end==320;self.executed_steps+=1;self.expected_ctrl=command.copy()
        gate={'status':'RETAINED_REVERSE_BRAKE_CONTRACT','hidden_world_geometry_used':False,'dynamic_time_gate':True,'active_gear':None,
            'backup_margin_recovery':True,'recovery_kind':c['recovery_kind'],'prediction_horizon_steps':320-i,'braking_tail_after_physics_steps':max(0,160-i),
            'predicted_minimum_clearance_m':c['minimum_causal_predicted_clearance_m'],'predicted_self_domain_margin_m':c['minimum_predicted_self_domain_margin_m'],
            'predicted_next_pose':c['poses'][end-1].tolist(),'predicted_end_pose':c['poses'][-1].tolist(),'terminal_speed_threshold_m_s':.025,
            'candidate_count_safe':1,'prediction_steps_total':self.predictor.prediction_steps,'retained_from_step':c['created_step'],
            'retained_forecast_age_s':float(real.time-c['created_time']),'contract_native_cursor':i,'finite_contract_complete_after_public':bool(self.finish_pending)}
        return command,gate
    def after_public(self,real):
        if self.expected is None:return False
        q,v=self.expected
        assert max(np.max(abs(real.qpos-q)),np.max(abs(real.qvel-v)))<=1e-8,'RETAINED_OR_NOMINAL_PREFIX_STATE_MISMATCH'
        assert self.expected_ctrl is not None and np.max(abs(real.ctrl[self.ids]-self.expected_ctrl))<=1e-12,'CERTIFIED_APPLIED_CTRL_MISMATCH'
        self.expected=None;self.expected_ctrl=None
        if self.finish_pending:
            self.finish_pending=False;self.executing=False;self.cache=None;return True
        return False
