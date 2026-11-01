"""Only old73 replay and a complete ordinary-plus-retained-tail certificate."""
import os,sys,json,gzip,math,time,signal,traceback,importlib.util
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
repo=Path(os.environ['PHASE_REPO']);root=repo/'runs/v695_discovery_verified_fixture';out=root/'fixed73'
sys.path.insert(1,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
sys.path.insert(1,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
from geometry_predictor import RobotPredictor
from reserved_recovery import ReservedRecovery
from dynamic_scene import Motion
from motion_tracker import install_time_gate
from exact_footprint import build,pose_values
from self_geometry import SelfGeometry,containment_margin
from dynamic_contact import GeometryCatalog
from factory import initialize
read=lambda p:json.loads(p.read_text());pre=read(root/'PRE_NAV_VALIDATION.json');assert pre['status']=='PASS'
pair=repo/'runs/v691_discovery_in_motion/moving_discovery01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()][:73]
m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];d.qvel[:]=0.;motion=Motion(config);motion.apply(m,d);mujoco.mj_forward(m,d)
context,_=initialize(95000011,out);inner=context['env'].inner;env=SimpleNamespace(model=m,data=d,inner=inner)
predictor=RobotPredictor(env,repo/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids
geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,pair/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds'])
spec=importlib.util.spec_from_file_location('v693_physical_field',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);sys.modules[spec.name]=F;spec.loader.exec_module(F)
steps=extra=bad=0;worst=np.zeros(3);minimum=selfmargin=1e9;status='FAILED';error=None;summary=None
started=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FIXED73_180S')));signal.alarm(180)
try:
    for k,row in enumerate(rows):
        d.ctrl[:]=row['ctrl']
        for _ in range(8):
            mujoco.mj_step(m,d);motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);steps+=1
            b=geometry.actual(m,d);selfmargin=min(selfmargin,float(containment_margin(b,bounds)));q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
            actual=SimpleNamespace(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.empty((0,4)),circles=np.asarray([[*motion.xy(d.time),.1]]),sensor_points=np.empty((0,2)),sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));minimum=min(minimum,float(pose_values(actual,[[q[0],q[1],yaw]])[0]))
            for c in d.contact:bad+=catalog.classify(c,steps,k,float(d.time))['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']
            assert minimum>=.15-1e-8 and selfmargin>=0 and bad==0,'REPLAY_PHYSICAL_ANOMALY'
        worst=np.maximum(worst,[np.max(abs(d.qpos-row['qpos_full'])),np.max(abs(d.qvel-row['qvel_full'])),np.max(abs(d.mocap_pos-row['mocap_pos']))]);assert worst.max()<=1e-8
    path=np.asarray(pre['route']);current=np.asarray(pre['pose']);field=build(F,pre['causal_world']);install_time_gate(field,pre['causal_state'],'predictive',[],[])
    assert abs(d.time-pre['causal_state']['time'])<=1e-8
    target=path[min(len(path)-1,13),:2];rel=target-current[:2];lateral=-math.sin(current[2])*rel[0]+math.cos(current[2])*rel[1]
    steer=float(np.clip(math.atan2(2*inner.wheel_base*lateral,max(float(rel@rel),.02)),-inner.max_steer,inner.max_steer));speed=min(.60,.50/(1+abs(steer)))
    proposal,gate=predictor.select(env,field,path,0,current,steer,speed,d.ctrl[ids])
    assert proposal is not None,'NO_SAFE_FIRST_PROPOSAL'
    manager=ReservedRecovery(predictor,mujoco,ids,out);summary=manager.admit_nominal(d,proposal,field,pre['causal_state'],73)
    (out/'ATTEMPT.json').write_text(json.dumps({'gate':gate,'proposal':proposal.tolist(),'reserve_attempt':manager.last_attempt},indent=2)+'\n')
    assert summary is not None,'NO_COMPLETE_APPENDABLE_TAIL'
    with gzip.open(out/'CERTIFICATE.json.gz','wt')as f:json.dump({k:v.tolist()if isinstance(v,np.ndarray)else v for k,v in manager.cache.items()},f)
    pd=mujoco.MjData(predictor.model)
    for name in ('qpos','qvel','act','qacc_warmstart'):getattr(pd,name)[:]=getattr(d,name)
    pd.time=float(d.time);mujoco.mj_forward(predictor.model,pd);pd.qacc_warmstart[:]=d.qacc_warmstart;pd.ctrl[:]=0.;pd.ctrl[ids]=proposal
    for _ in range(8):mujoco.mj_step(predictor.model,pd);extra+=1
    manager.after_public(pd);command,_=manager.start(pd,74)
    for public in range(40):
        predictor.command_map.assert_first(command,pd.ctrl[ids]);pd.ctrl[:]=0.;pd.ctrl[ids]=command
        for _ in range(8):mujoco.mj_step(predictor.model,pd);extra+=1
        done=manager.after_public(pd)
        if public<39:command,_=manager.command(pd)
    assert done and extra==328 and predictor.prediction_steps+extra<=20000
    status='FULL_PREFIX_AND_TAIL_PASS'
except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
    signal.alarm(0);value={'status':status,'error':error,'replay_native_steps':steps,'private_prediction_integrations':predictor.prediction_steps+extra,'forecast_integrations':predictor.prediction_steps,'private_execute_integrations':extra,'maximum_old_public_errors':worst.tolist(),'private_full_state_ctrl_matching':status=='FULL_PREFIX_AND_TAIL_PASS','minimum_replay_native_clearance_m':minimum,'minimum_replay_self_margin_m':selfmargin,'bad_contacts':bad,'elapsed_s':time.monotonic()-started,'summary':summary,'new_navigation_tasks':0};print(json.dumps(value,indent=2),flush=True);(out/'COMPLETION.json').write_text(json.dumps(value,indent=2)+'\n');context['env'].close();assert status=='FULL_PREFIX_AND_TAIL_PASS',error
