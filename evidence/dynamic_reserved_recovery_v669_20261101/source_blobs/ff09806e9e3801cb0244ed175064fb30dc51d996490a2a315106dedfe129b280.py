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
    @staticmethod
    def poses(q):
        q=np.asarray(q);yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
        return np.c_[q[:,:2],yaw]
    @staticmethod
    def target(steer,wheel):
        if abs(steer)<1e-9:return np.array([0.,0.,wheel,wheel])
        r=.60/math.tan(abs(steer));inner=math.atan2(.60,r-.27);outer=math.atan2(.60,r+.27)
        return np.array([inner,outer,wheel,wheel]if steer>0 else[-outer,-inner,wheel,wheel])
    @staticmethod
    def controls(target,last):
        rows=[];command=np.asarray(last).copy()
        for tick in range(0,320,8):
            active=target.copy()
            if tick>=160:active[2:]=0.
            command[:2]=np.clip(active[:2],command[:2]-.10,command[:2]+.10)
            command[2:]=np.clip(active[2:],command[2:]-.70,command[2:]+.70)
            rows.extend([command.copy()for _ in range(8)])
        return np.asarray(rows)
    def admit_nominal(self,real,proposal,field,state,step):
        m=self.predictor.model;d=self.scratch;self.mj.mj_resetData(m,d)
        for name in ['qpos','qvel','act','qacc_warmstart']:getattr(d,name)[:]=getattr(real,name)
        d.time=float(real.time);d.ctrl[:]=0.;d.ctrl[self.ids]=proposal
        self.mj.mj_forward(m,d);d.qacc_warmstart[:]=real.qacc_warmstart
        prefix=[];margin=float('inf')
        for _ in range(8):
            self.predictor.native(m,d);self.predictor.prediction_steps+=1
            self.mj.mj_kinematics(m,d);prefix.append(d.qpos.copy())
            margin=min(margin,float(containment_margin(self.predictor.self_geometry.actual(m,d),self.predictor.domain)))
        if margin<.002:return None
        prefix=self.poses(prefix);initial_q=d.qpos.copy();initial_v=d.qvel.copy();self.last_prefix_qpos=initial_q.copy();self.last_prefix_qvel=initial_v.copy();yaw=float(prefix[-1,2]);best=None;safe_count=0
        for steer in [-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]:
            for wheel in [-12.,-8.,-4.]:
                target=self.target(steer,wheel)
                trajectory=self.predictor.predict(d,target,self.ids,np.asarray(proposal),horizon=320,brake_after=160)
                signed=float((trajectory[-1,:2]-initial_q[:2])@np.array([math.cos(yaw),math.sin(yaw)]))
                minimum=float(np.min(field.trajectory_values(np.vstack((prefix,trajectory)),.01)))
                bodymargin=min(margin,self.predictor.prediction_self_margin)
                if minimum<.155 or bodymargin<.002 or self.predictor.terminal_speed>.025 or signed>-.02:continue
                safe_count+=1;score=minimum+.1*(-signed)-.02*abs(steer)
                if best is not None and score<=best['score']:continue
                best={'score':score,'created_step':int(step),'created_time':float(real.time),'start_time':float(d.time),
                    'initial_qpos':initial_q.copy(),'initial_qvel':initial_v.copy(),
                    'qpos':self.predictor.last_forecast_qpos.copy(),'qvel':self.predictor.last_forecast_qvel.copy(),
                    'poses':trajectory.copy(),'controls':self.controls(target,proposal),
                    'forecast_state':json.loads(json.dumps(state)),
                    'minimum_causal_predicted_clearance_m':minimum,'minimum_predicted_self_domain_margin_m':bodymargin,
                    'terminal_speed_m_s':self.predictor.terminal_speed,'signed_reverse_displacement_m':signed,
                    'target':target.copy(),'prefix_poses':prefix.copy()}
        if best is None:return None
        self.cache=best;self.cursor=0;self.expected=(initial_q,initial_v);self.finish_pending=False
        return {'status':'REVERSE_BRAKE_TAIL_RESERVED','safe_reserve_candidates':safe_count,'reserve_minimum_clearance_m':best['minimum_causal_predicted_clearance_m'],
                'reserve_signed_reverse_displacement_m':best['signed_reverse_displacement_m'],'reserve_target':best['target'].tolist(),
                'reserve_total_native_ticks':328,'reserve_braking_after_native_ticks':168,'causal_forecast_horizon_s':3.28}
    def start(self,real,step):
        assert self.cache is not None and not self.executing,'NO_RETAINED_RECOVERY_CONTRACT'
        self.executing=True;self.activations+=1
        directory=self.cell/'recovery_contracts';directory.mkdir(exist_ok=True)
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
        end=min(i+8,320);command=c['controls'][i].copy();self.cursor=end;self.expected=(c['qpos'][end-1],c['qvel'][end-1]);self.finish_pending=end==320;self.executed_steps+=1
        gate={'status':'RETAINED_REVERSE_BRAKE_CONTRACT','hidden_world_geometry_used':False,'dynamic_time_gate':True,'active_gear':None,
            'backup_margin_recovery':True,'prediction_horizon_steps':320-i,'braking_tail_after_physics_steps':max(0,160-i),
            'predicted_minimum_clearance_m':c['minimum_causal_predicted_clearance_m'],'predicted_self_domain_margin_m':c['minimum_predicted_self_domain_margin_m'],
            'predicted_next_pose':c['poses'][end-1].tolist(),'predicted_end_pose':c['poses'][-1].tolist(),'terminal_speed_threshold_m_s':.025,
            'candidate_count_safe':1,'prediction_steps_total':self.predictor.prediction_steps,'retained_from_step':c['created_step'],
            'retained_forecast_age_s':float(real.time-c['created_time']),'contract_native_cursor':i,'finite_contract_complete_after_public':bool(self.finish_pending)}
        return command,gate
    def after_public(self,real):
        if self.expected is None:return False
        q,v=self.expected
        assert max(np.max(abs(real.qpos-q)),np.max(abs(real.qvel-v)))<=1e-8,'RETAINED_OR_NOMINAL_PREFIX_STATE_MISMATCH'
        self.expected=None
        if self.finish_pending:
            self.finish_pending=False;self.executing=False;self.cache=None;return True
        return False
