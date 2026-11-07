"""Install the one reference-continuation candidate before its first model."""
from pathlib import Path
import ast

repo = Path(__file__).resolve().parents[2]
own = repo/'experiments/v836_reference_recovery_development'
assert not (own/'CANDIDATE_FREEZE.json').exists()
p = own/'geometry_predictor.py'
text = p.read_text()
text += '''

_OriginalGeometryPredictor = RobotPredictor
class RobotPredictor(_OriginalGeometryPredictor):
    def predict(self, real, target_command, ids, last_command, horizon=240, brake_after=None):
        from reference_recovery import budget, predict_schedule
        budget(self, horizon)
        if horizon == 320 and getattr(self, 'recovery_successor_mode', False):
            return predict_schedule(self, real, target_command, ids, last_command, brake_after)
        return super().predict(real, target_command, ids, last_command, horizon, brake_after)
'''
p.write_text(text)
p = own/'reserved_recovery.py'
old = p.read_text()
start = old.index('    def admit_nominal(')
end = old.index('    def check_current_contract(')
new = '''    def set_reference(self,path,index,goal,wheel_base=.60):
        self.reference=None
        if path is not None and len(path)>=2 and int(path[min(index+1,len(path)-1),3])==1:
            self.reference={'path':np.asarray(path,float).tolist(),'index':int(index),'goal_xy':np.asarray(goal,float).tolist(),'wheel_base':float(wheel_base)}
    def admit_nominal(self,real,proposal,field,state,step):
        from reference_recovery import LOOKAHEADS,WHEELS,DRIVE_TICKS,predict_follow
        self.predictor.command_map.assert_first(proposal,real.ctrl[self.ids])
        reference=getattr(self,'reference',None)
        active=reference is not None and state['center']is not None
        self.last_attempt={'step':int(step),'status':'CHECKING','prefix_self_domain_margin_m':None,'candidates':[],'reference_successor_active':active,'reference':reference}
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
        forward=[(steer,wheel)for steer in [-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]for wheel in [4.]]
        groups=[('ORIGINAL',original),('FORWARD_EXTENSION',forward)]
        if active:groups.append(('REFERENCE_FOLLOW',[(look,(wheel,brake))for look in LOOKAHEADS for wheel in WHEELS for brake in DRIVE_TICKS]))
        for library,choices in groups:
            if library!='ORIGINAL'and best is not None:break
            for steer,wheel in choices:
                following=library=='REFERENCE_FOLLOW'
                if following:
                    lookahead=steer;wheel,brake_after=wheel;kind='REFERENCE_FOLLOW_BRAKE'
                    trajectory=predict_follow(self.predictor,d,self.ids,np.asarray(proposal),reference,lookahead,wheel,brake_after)
                    target=self.predictor.reference_prediction['targets'][0].copy()
                else:
                    brake_only=steer is None;kind='BRAKE_ONLY'if brake_only else'FORWARD_BRAKE'if wheel>0 else'REVERSE_BRAKE'
                    target=np.r_[proposal[:2],0.,0.]if brake_only else self.target(steer,wheel)
                    brake_after=240 if kind=='FORWARD_BRAKE'else160
                    self.predictor.recovery_successor_mode=active
                    try:trajectory=self.predictor.predict(d,target,self.ids,np.asarray(proposal),horizon=320,brake_after=brake_after)
                    finally:self.predictor.recovery_successor_mode=False
                extended=self.predictor.reference_prediction if active else None
                signed=float((trajectory[-1,:2]-initial_q[:2])@np.array([math.cos(yaw),math.sin(yaw)]))
                complete=np.vstack((prefix,trajectory));geometry_start=time.perf_counter();proof=evaluate_rejection(field,complete);geometry_seconds=time.perf_counter()-geometry_start
                values=proof['full_values'];minimum=None if values is None else float(np.min(values))
                successor_min=None
                if active and not proof['rejected']:
                    extra_values=field.causal_values_at_times(extended['poses'][320:],np.arange(329,337)*.01)
                    successor_min=min(minimum,float(extra_values.min()))
                witness_file=None
                if proof['full_minimum_not_evaluated']:
                    directory=self.cell/'rejection_witnesses';directory.mkdir(exist_ok=True);file=directory/f'witness_{next(_witness_counter):07d}.npz'
                    assert not file.exists();np.savez(file,poses=complete,step=int(step),witness_native_tick=proof['witness_native_tick'],witness_value=proof['witness_value_m'],state_sha256=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest(),target=target,prefix_command=proposal)
                    witness_file=str(file.relative_to(self.cell))
                bodymargin=min(margin,self.predictor.prediction_self_margin)
                goal_gain=None if not following else float(np.linalg.norm(real.qpos[:2]-reference['goal_xy'])-np.linalg.norm(trajectory[-1,:2]-reference['goal_xy']))
                reason='TIME_CLEARANCE'if proof['rejected']else'SELF_DOMAIN'if bodymargin<.002 else'TERMINAL_SPEED'if self.predictor.terminal_speed>.025 else'SUCCESSOR_CLEARANCE'if active and successor_min<.155 else'SUCCESSOR_SELF'if active and extended['self_margin']<.002 else'SUCCESSOR_TERMINAL_SPEED'if active and extended['terminal_speed']>.025 else'INSUFFICIENT_REVERSE'if kind=='REVERSE_BRAKE'and signed>-.02 else'INSUFFICIENT_FORWARD'if kind in('FORWARD_BRAKE','REFERENCE_FOLLOW_BRAKE')and signed<.02 else'ESCAPE_NO_GOAL_PROGRESS'if following and goal_gain<.02 else None
                detail={'kind':kind,'library':library,'brake_after_native_ticks':brake_after,'target_command':target.tolist(),'minimum_clearance_m':minimum,'minimum_clearance_native_tick':None if values is None else int(np.argmin(values))+1,'full_minimum_not_evaluated':proof['full_minimum_not_evaluated'],'early_rejection_witness_native_tick':proof['witness_native_tick'],'early_rejection_witness_value_m':proof['witness_value_m'],'early_rejection_witness_file':witness_file,'geometry_checked_native_ticks':proof['checked_native_samples'],'geometry_wall_s':geometry_seconds,'self_domain_margin_m':float(bodymargin),'terminal_speed_m_s':float(self.predictor.terminal_speed),'signed_displacement_m':signed,'complete_goal_progress_m':goal_gain,'reason':reason,'successor_minimum_m':successor_min,'successor_required':active}
                if following:detail.update(lookahead_m=lookahead,wheel_speed=wheel)
                self.last_attempt['candidates'].append(detail)
                if reason is not None:continue
                safe_count+=1
                score=minimum+.1*(goal_gain if following else signed if kind=='FORWARD_BRAKE'else-signed)-.02*abs(0. if following else(steer or 0.))
                if best is not None and score<=best['score']:continue
                controls=extended['controls'][:320].copy()if active else self.controls(target,proposal,brake_after)
                best={'score':score,'recovery_kind':kind,'created_step':int(step),'created_time':float(real.time),'start_time':float(d.time),'initial_qpos':initial_q.copy(),'initial_qvel':initial_v.copy(),'prefix_command':np.asarray(proposal).copy(),'qpos':self.predictor.last_forecast_qpos.copy(),'qvel':self.predictor.last_forecast_qvel.copy(),'poses':trajectory.copy(),'controls':controls,'brake_after_native_ticks':brake_after,'forecast_state':json.loads(json.dumps(state)),'minimum_causal_predicted_clearance_m':minimum,'minimum_predicted_self_domain_margin_m':bodymargin,'terminal_speed_m_s':self.predictor.terminal_speed,'signed_reverse_displacement_m':signed,'signed_longitudinal_displacement_m':signed,'target':target.copy(),'prefix_poses':prefix.copy()}
                if active:
                    best['one_cycle_continuation']={'minimum_clearance_m':successor_min,'minimum_self_margin_m':min(margin,extended['self_margin']),'terminal_speed_m_s':extended['terminal_speed'],'extra_controls':extended['controls'][320:].tolist(),'extra_qpos':extended['qpos'][320:].tolist(),'extra_qvel':extended['qvel'][320:].tolist(),'extra_poses':extended['poses'][320:].tolist(),'no_future_observations_assumed':True,'absolute_end_time':float(real.time)+3.36}
                if following:best['reference_following']={**reference,'lookahead_m':lookahead,'wheel_speed':wheel,'drive_ticks':brake_after,'targets':extended['targets'].tolist()}
                if not following and brake_only:break
        self.last_attempt['status']='APPENDABLE_BACKUP_FOUND'if best is not None else'NO_APPENDABLE_BACKUP'
        if best is None:return None
        self.cache=best;self.cursor=0;self.expected=(initial_q,initial_v);self.expected_ctrl=np.asarray(proposal).copy();self.finish_pending=False
        return {'status':best['recovery_kind']+'_TAIL_RESERVED','recovery_kind':best['recovery_kind'],'safe_reserve_candidates':safe_count,'reserve_minimum_clearance_m':best['minimum_causal_predicted_clearance_m'],'reserve_signed_longitudinal_displacement_m':best['signed_longitudinal_displacement_m'],'reserve_signed_reverse_displacement_m':best['signed_longitudinal_displacement_m'],'reserve_target':best['target'].tolist(),'reserve_total_native_ticks':328,'reserve_braking_after_native_ticks':8+best['brake_after_native_ticks'],'causal_forecast_horizon_s':3.28,'successor_certificate':best.get('one_cycle_continuation')}
'''
new = new.replace('else160', 'else 160')
text = old[:start]+new+old[end:]
text = text.replace("candidate.allow_forward_escape=True;candidate.escape_goal_xy=np.asarray(metadata['public_goal_xy'],float)", "candidate.allow_forward_escape=False;candidate.escape_goal_xy=np.asarray(metadata['public_goal_xy'],float);candidate.reference=getattr(self,'reference',None)")
p.write_text(text)
p = own/'joint_admission.py'
text = p.read_text().replace("    unique=[];seen=set()", "    reserved.set_reference(path,index,getattr(reserved,'public_goal_xy',path[-1,:2]),.60)\n    unique=[];seen=set()")
p.write_text(text)
p = own/'recovery_supervisor.py'
text = p.read_text().replace("        ranked=predictor.ranked_safe_candidates", "        reserved.set_reference(path,index,env.goal_xy,float(env.inner.wheel_base))\n        ranked=predictor.ranked_safe_candidates")
p.write_text(text)
p = own/'run_static.py'
text = p.read_text().replace('        reserved=ReservedRecovery(predictor,mujoco,recovery_ids,cell)', '        reserved=ReservedRecovery(predictor,mujoco,recovery_ids,cell)\n        reserved.public_goal_xy=np.asarray(env.goal_xy).copy()')
text = text.replace("                            cache=reserved.cache\n", "                            cache=reserved.cache\n                            if 'one_cycle_continuation'in cache:\n                                directory=cell/'successor_certificates';directory.mkdir(exist_ok=True)\n                                with gzip.open(directory/f'certificate_{step:04d}.json.gz','wt')as stream:json.dump(cache,stream,default=lambda x:x.tolist()if isinstance(x,np.ndarray)else x.item())\n")
p.write_text(text)
for path in own.glob('*.py'):
    ast.parse(path.read_text(), filename=str(path))
print('ONE_REFERENCE_FOLLOWING_AND_SUCCESSOR_CANDIDATE_INSTALLED_BEFORE_MODELS')
