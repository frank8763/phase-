"""C0 physical route-following diagnostic with the frozen V680 command stack."""
import os,sys,json,math,time,signal,hashlib,fcntl,gzip,traceback,shutil,argparse
from pathlib import Path
from types import MethodType
import numpy as np
src=Path(__file__).resolve().parent;repo=src.parents[1];core=repo/'experiments/v680_dynamic_later_stop_reserve'
sys.path.insert(1,str(core))
from factory import initialize
from instrumentation import Audit,dump,install_physical_contract
from geometry_predictor import RobotPredictor,SELF_DOMAIN
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import build,pose_values
from reserved_recovery import ReservedRecovery
from joint_admission import admit_ranked
from recovery_supervisor import emit
from planner import wrap
from motion_tracker import install_time_gate
from arena import prepare
p=argparse.ArgumentParser();p.add_argument('--course',choices=['straight','turn','bypass'],required=True);p.add_argument('--name',required=True);p.add_argument('--max-steps',type=int,required=True);a=p.parse_args()
out=repo/'runs/v687_control_curriculum'/a.name/'paired';out.mkdir(parents=True,exist_ok=False)
lock=(repo/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
snapshot=out.parent/'source_snapshot';snapshot.mkdir()
for f in src.glob('*.py'):shutil.copy2(f,snapshot/f.name)
shutil.copy2(src/'PROTOCOL.md',snapshot/'PROTOCOL.md')
started=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('C0_450S_HARD_LIMIT')));signal.alarm(450)
rows=[];result=None;status='FAILED';error=None;count=0;private=0
try:
    context,native=initialize(95000011,out);env=context['env'];B=context['B'];F=context['F'];H=context['H'];shift=context['shift'];model=context['model']
    import mujoco
    from contact_contract import GeometryCatalog,ContactRecorder
    reference,construction=prepare(context,mujoco,a.course,repo)
    changed=install_physical_contract(env)
    env.phase21_v3_enable_detour=False;env.REVALIDATE_MAX_REPLANS=0
    env._phase21_v8_replan=MethodType(lambda *a,**k:False,env);env.inner.goal_threshold=.45
    obs=env._phase19_refresh_initial_observation(context['obs'])
    bounds=SELF_DOMAIN.tolist();geometry=SelfGeometry(env.model,mujoco)
    world=H.world_input(env,[]);world.update(rectangles=[],circles=[],sensor_points=[],footprint_bounds=bounds)
    field=build(F,world);field.guard=.15
    assert float(np.min(field.pose_values(reference[:,:3])))>=.155
    cell=out/'geometry_memory';cell.mkdir();audit=Audit();audit.begin(env,cell,a.course)
    recorder=ContactRecorder(GeometryCatalog(env.model,mujoco,context['xml']),cell)
    predictor=RobotPredictor(env,B.PROJECT,mujoco,native);command_map=predictor.command_map
    reserved=ReservedRecovery(predictor,mujoco,command_map.ids,cell)
    dump(out/'C0_PROTOCOL.json',construction)
    dump(cell/'ACTUATOR_COMMAND_CONTRACT.json',{'ids':command_map.ids,'limits':np.c_[command_map.lower,command_map.upper],'rate':command_map.rate})
    mujoco.mj_saveModel(env.model,str(out/'scene_model.mjb'),None)
    dump(out/'STATIC_PROTOCOL.json',{'known_rectangles':[],'known_circles':[],'footprint_bounds':bounds,'start_qpos':env.data.qpos,'start_qvel':env.data.qvel,'goal_xy':env.goal_xy,'full_model_sha256':B.sha(out/'scene_model.mjb'),'physics_contract':changed,'course':a.course,'active_obstacles':0})
    start_hash,parts=B.state_hash(env,shift,include_model=True,components=True)
    dump(cell/'initial_state_components.json',parts)
    model_positions=env.model.geom_pos.copy();last=np.zeros(4);desired=None;expected=None;self_margins=[];clearances=[];matches=[];public=-1;backup_steps=0
    def pose():
        q=env.data.qpos;return np.array([q[0],q[1],math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))])
    native_log=gzip.open(cell/'native.jsonl.gz','wt')
    def observed(m,d,*args,**kwargs):
        global count
        assert expected is not None and np.max(abs(d.ctrl-expected))<=1e-12
        audit.before_native(m,d);native(m,d,*args,**kwargs);audit.after_native(m,d);count+=1
        assert np.max(abs(d.ctrl-expected))<=1e-12 and np.array_equal(m.geom_pos,model_positions)
        mujoco.mj_kinematics(m,d);actual=geometry.actual(m,d);margin=float(containment_margin(actual,bounds));self_margins.append(margin)
        gfield=type('Field',(),{})();gfield.half=(actual[2:]-actual[:2])/2;gfield.center_local=(actual[2:]+actual[:2])/2;gfield.rectangles=[];gfield.circles=[];gfield.sensor_points=[];gfield.sensor_extra=0.;gfield.config=field.config
        clear=float(pose_values(gfield,[pose()])[0]);clearances.append(clear)
        recorder.record(d,count,public)
        native_log.write(json.dumps({'native_step':count,'public_step':public,'clearance_m':clear,'self_margin_m':margin,'actual_ctrl':d.ctrl.tolist(),'expected_ctrl':expected.tolist()})+'\n')
        assert margin>=0 and clear>=.15-1e-8 and recorder.first_anomaly is None,'NATIVE_PHYSICAL_SAFETY_ANOMALY'
    original_apply=env.inner._apply_wheel_ctrl
    def apply(self,lf,rf,lr,rr):
        global last,expected
        assert desired is not None;command_map.assert_first(desired,last)
        env.data.ctrl[:]=0;env.data.ctrl[command_map.ids]=desired;expected=env.data.ctrl.copy();last=desired.copy()
        self.last_lf_steer,self.last_rf_steer,self.last_lr_wheel,self.last_rr_wheel=map(float,desired)
    env.inner._apply_wheel_ctrl=MethodType(apply,env.inner);mujoco.mj_step=observed
    index=0;outcome='HORIZON';ordinary_targets=0
    try:
        for step in range(a.max_steps):
            public=step;current=pose();distance=float(np.linalg.norm(current[:2]-env.goal_xy))
            if distance<=.45:outcome='GOAL';break
            if time.monotonic()-started>=420:outcome='BOUNDED_WALL_STOP';break
            state={'center':None,'time':float(env.data.time),'hidden_world_geometry_used':False,'scope':'C0 declared no-actor task; dynamic forecast not applicable'}
            install_time_gate(field,state,'predictive',[],[])
            if reserved.executing:
                proposal,gate=reserved.command(env.data);backup_steps+=1
            else:
                nearest=index+int(np.argmin(np.linalg.norm(reference[index:min(len(reference),index+40),:2]-current[:2],axis=1)));index=nearest
                target_index=min(index+1,len(reference)-1);arc=0.
                while target_index<len(reference)-1 and arc<.45:
                    arc+=float(np.linalg.norm(reference[target_index+1,:2]-reference[target_index,:2]));target_index+=1
                rel=reference[target_index,:2]-current[:2];lateral=-math.sin(current[2])*rel[0]+math.cos(current[2])*rel[1]
                steer=float(np.clip(math.atan2(2*float(env.inner.wheel_base)*lateral,max(float(rel@rel),.02)),-env.inner.max_steer,env.inner.max_steer))
                speed=min(.60,.50/(1+abs(steer)))
                if distance<1:speed*=.65
                # Preserve the original preliminary Ackermann call (before select's own library).
                actual_speed=float(env.data.qvel[0]*math.cos(current[2])+env.data.qvel[1]*math.sin(current[2]));wheel=float(np.clip((speed+1.3*(speed-actual_speed))/float(env.inner.wheel_radius),-12,12))
                env.inner._ackermann_from_steer_speed(steer,wheel)
                proposal,gate=predictor.select(env,field,reference,index,current,steer,speed,last)
                emit(cell,'control_decisions.jsonl',{'step':step,'candidate_role':'ORDINARY','stage':'NOMINAL','summary':gate,'candidates':predictor.last_diagnostics})
                proposal,gate,summary=admit_ranked(reserved,predictor,env.data,proposal,gate,field,state,step,reference,index,cell)
                if summary is not None:gate['recovery_reserve']=summary;ordinary_targets+=1
                elif reserved.cache is not None:proposal,gate=reserved.start(env.data,step);backup_steps+=1
                else:outcome='NO_RESERVED_CONTROL';dump(cell/'rejected_control.json',{'step':step,'gate':gate});break
            desired=np.asarray(proposal,float)
            emit(cell,'model_admission.jsonl',{'step':step,**gate})
            action,_=model.predict(obs,deterministic=True);before=count;obs,_,term,trunc,info=B.finish_api(env.step(action))
            assert count==before+8
            if reserved.expected is not None:
                q,v=reserved.expected;err=max(float(np.max(abs(env.data.qpos-q))),float(np.max(abs(env.data.qvel-v))),float(np.max(abs(env.data.ctrl[command_map.ids]-reserved.expected_ctrl))))
                matches.append({'step':step,'maximum_full_state_and_ctrl_error':err});assert err<=1e-8,'PREDICTION_EXECUTION_MISMATCH'
            finished=reserved.after_public(env.data)
            if finished:index=int(np.argmin(np.linalg.norm(reference[:,:2]-pose()[:2],axis=1)))
            audit.after_public(env,step)
            current=pose();distance=float(np.linalg.norm(current[:2]-env.goal_xy))
            rows.append({'step':step,'pose':current.tolist(),'goal_distance_m':distance,'path_index':index,'applied_ctrl':env.data.ctrl.tolist(),'nominal_sac_action':action.tolist(),'reserved':bool(gate['status']=='RETAINED_REVERSE_BRAKE_CONTRACT')})
            if step%25==0:
                dump(cell/'partial_progress.json',{'course':a.course,'public_steps':len(rows),'native_steps':count,'goal_distance_m':distance,'elapsed_s':time.monotonic()-started});print(a.course,step,round(distance,4),flush=True)
            if distance<=.45:outcome='GOAL';break
            if term or trunc:outcome='NATIVE_TERMINATION';break
        contacts=recorder.summary();distance=float(np.linalg.norm(pose()[:2]-env.goal_xy))
        result={'course':a.course,'outcome':outcome,'strict_safe_arrival':bool(distance<=.45 and recorder.first_anomaly is None),'goal_distance_m':distance,'public_steps':len(rows),'physics_steps':count,'prediction_steps':predictor.prediction_steps,'backup_steps':backup_steps,'ordinary_steps':ordinary_targets,'minimum_native_clearance_m':min(clearances),'minimum_actual_self_domain_margin_m':min(self_margins),'contacts':contacts,'root_mutations_outside_mjstep':0,'static_obstacle_pose_unchanged':np.array_equal(env.model.geom_pos,model_positions),'active_obstacles':0,'initial_state_hash':start_hash,'elapsed_s':time.monotonic()-started,'training_updates':0,'dynamic_success':False,'source_revision':'C0_fixed_route_V680_nominal'}
        dump(cell/'result.json',result);status='COMPLETE'
    finally:
        private=predictor.prediction_steps;dump(cell/'trace.json',rows);dump(cell/'prediction_state_matches.json',matches);native_log.close();recorder.close();mujoco.mj_step=native;env.inner._apply_wheel_ctrl=original_apply
except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
    signal.alarm(0);dump(out/'completion.json',{'status':status,'result':result,'error':error,'executed_native_steps':count,'private_prediction_integrations':private,'training_updates':0,'elapsed_s':time.monotonic()-started});print(json.dumps({'status':status,'error':error,'result':result}),flush=True)
if status!='COMPLETE':sys.exit(1)
