"""Locked final V691 state: finite causal actuator trajectories, never online rescue."""
import os,sys,json,gzip,math,time,signal,hashlib,traceback
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
import mujoco
import mujoco.rollout

repo=Path(os.environ['PHASE_REPO']);src=Path(__file__).resolve().parent
base=repo/'runs/v691_discovery_in_motion/moving_discovery01/paired';cell=base/'geometry_memory'
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
sys.path.insert(0,str(repo/'experiments/v691_discovery_in_motion'))
from geometry_predictor import RobotPredictor
from reserved_recovery import ReservedRecovery
from motion_tracker import install_time_gate
from exact_footprint import pose_values
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin,quaternion_matrices

os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=repo/'runs/v692_discovery_escape_diagnosis/fixed408';out.mkdir(exist_ok=False)
window=read(out.parent/'ROUND_WINDOW.json');assert not window['round_closed'] and time.time()+185<window['absolute_deadline_unix']
def dump(name,value):
    (out/name).write_text(json.dumps(value,indent=2,default=lambda x:x.tolist()if isinstance(x,np.ndarray)else x.item(),allow_nan=False)+'\n')
rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()]
states=[json.loads(s)for s in(cell/'motion_estimate.jsonl').read_text().splitlines()]
assert len(rows)==408 and len(states)==409
state=states[-1];protocol=read(base/'STATIC_PROTOCOL.json');config=read(base/'DYNAMIC_PROTOCOL.json')
motion=Motion(config);m=mujoco.MjModel.from_binary_path(str(base/'scene_model.mjb'));d=mujoco.MjData(m)
d.qpos[:]=protocol['start_qpos'];d.qvel[:]=0.;motion.apply(m,d);mujoco.mj_forward(m,d)
geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,base/'assets/isolated_indoor.xml')
predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,mujoco.mj_step)
ids=predictor.command_map.ids;bounds=np.asarray(protocol['footprint_bounds'])
static=dict(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,
    rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),
    sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
steps=forecast=private_execute=bad=0;worst=np.zeros(3);minimum=selfmargin=1e9;records=[];best={};status='FAILED';error=None
started=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FIXED408_180S')));signal.alarm(180)

def predict(controls):
    global forecast
    pm=predictor.model;pd=predictor.data;mujoco.mj_resetData(pm,pd)
    for name in ('qpos','qvel','act','qacc_warmstart'):getattr(pd,name)[:]=getattr(d,name)
    pd.time=float(d.time);pd.ctrl[:]=0.;mujoco.mj_forward(pm,pd)
    spec=mujoco.mjtState.mjSTATE_FULLPHYSICS;initial=np.empty(mujoco.mj_stateSize(pm,spec));mujoco.mj_getState(pm,pd,initial,spec)
    ctrl=np.zeros((1,328,pm.nu));ctrl[0][:,ids]=controls
    ss,sensors=mujoco.rollout.rollout(pm,pd,initial,ctrl,initial_warmstart=d.qacc_warmstart.copy(),persistent_pool=True)
    forecast+=328;q=ss[0,:,1:1+pm.nq];v=ss[0,:,1+pm.nq:1+pm.nq+pm.nv];packet=sensors[0]
    geoms=packet[:,7:].reshape(328,-1,7)
    body=predictor.self_geometry.bounds(geoms[:,:,:3],quaternion_matrices(geoms[:,:,3:]),packet[:,:3],packet[:,3:7])
    pd.qpos[:]=q[-1];pd.qvel[:]=v[-1];mujoco.mj_kinematics(pm,pd)
    margin=min(float(containment_margin(body,predictor.domain).min()),float(containment_margin(predictor.self_geometry.actual(pm,pd),predictor.domain)))
    return ReservedRecovery.poses(q),q.copy(),v.copy(),margin

def verify_serial(saved):
    global private_execute
    pm=predictor.model;pd=mujoco.MjData(pm)
    for name in ('qpos','qvel','act','qacc_warmstart'):getattr(pd,name)[:]=getattr(d,name)
    pd.time=float(d.time);pd.ctrl[:]=d.ctrl;mujoco.mj_forward(pm,pd);pd.qacc_warmstart[:]=d.qacc_warmstart
    errors=np.zeros(3)
    for tick,command in enumerate(saved['controls']):
        if tick%8==0:predictor.command_map.assert_first(command,pd.ctrl[ids])
        pd.ctrl[:]=0.;pd.ctrl[ids]=command;mujoco.mj_step(pm,pd);private_execute+=1
        errors=np.maximum(errors,[np.max(abs(pd.qpos-saved['qpos'][tick])),np.max(abs(pd.qvel-saved['qvel'][tick])),np.max(abs(pd.ctrl[ids]-command))])
    assert errors.max()<=1e-8,'PRIVATE_FULL_NATIVE_STATE_COMMAND_MISMATCH'
    return errors.tolist()

try:
    for k,row in enumerate(rows):
        d.ctrl[:]=row['ctrl']
        for _ in range(8):
            mujoco.mj_step(m,d);motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);steps+=1
            b=geometry.actual(m,d);selfmargin=min(selfmargin,float(containment_margin(b,bounds)))
            q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
            actual=SimpleNamespace(**{**static,'half':(b[2:]-b[:2])/2,'center_local':(b[2:]+b[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(d.time),config['radius_m']]]).reshape(-1,3)})
            minimum=min(minimum,float(pose_values(actual,[[q[0],q[1],yaw]])[0]))
            for c in d.contact:bad+=catalog.classify(c,steps,k,float(d.time))['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']
            assert minimum>=.15-1e-8 and selfmargin>=0 and bad==0,'PHYSICAL_REPLAY_ANOMALY'
        worst=np.maximum(worst,[np.max(abs(d.qpos-row['qpos_full'])),np.max(abs(d.qvel-row['qvel_full'])),np.max(abs(d.mocap_pos-row['mocap_pos']))])
        assert worst.max()<=1e-8,'FULL_REPLAY_MISMATCH'
    assert abs(d.time-state['time'])<=1e-10
    field=SimpleNamespace(**static);field.pose_values=MethodType(pose_values,field)
    install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
    current=d.ctrl[ids].copy();q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
    choices=[dict(family='STOP',steer=None,wheel=0.,brake_after=0,straight_after=None)]
    angles=[-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]
    choices += [dict(family='CONSTANT_THEN_STOP',steer=s,wheel=w,brake_after=b,straight_after=None)for s in angles for w in [-12.,-8.,-4.,4.,8.,12.]for b in [80,160,240]]
    choices += [dict(family='TURN_STRAIGHT_STOP',steer=s,wheel=w,brake_after=240,straight_after=t)for s in angles[:2]for w in [8.,12.]for t in [80,160]]
    assert len(choices)==99
    dump('REGISTERED_MATRIX.json',choices)
    dump('REPLAYED_INITIAL_STATE.json',{'qpos':d.qpos,'qvel':d.qvel,'act':d.act,'qacc_warmstart':d.qacc_warmstart,'ctrl':d.ctrl,'time':d.time,'causal_state':state})
    for index,c in enumerate(choices):
        target=np.r_[current[:2],0.,0.]if c['steer']is None else ReservedRecovery.target(c['steer'],c['wheel'])
        command=current.copy();controls=[]
        for tick in range(0,328,8):
            active=target.copy()
            if c['straight_after']is not None and tick>=c['straight_after']:active[:2]=0.
            if tick>=c['brake_after']:active[2:]=0.
            command=predictor.command_map.step(active,command);controls.extend([command.copy()for _ in range(8)])
        controls=np.asarray(controls);trajectory,qq,vv,margin=predict(controls)
        values=field.trajectory_values(trajectory,.01);speed=float(np.linalg.norm(vv[-1,:2]));clear=float(values.min())
        signed=float((trajectory[-1,:2]-d.qpos[:2])@np.array([math.cos(yaw),math.sin(yaw)]))
        reasons=[]
        if clear<.155:reasons.append('TIME_CLEARANCE')
        if margin<.002:reasons.append('SELF_DOMAIN')
        if speed>.025:reasons.append('TERMINAL_SPEED')
        rec={'index':index,**c,'minimum_clearance_m':clear,'minimum_clearance_native_tick':int(np.argmin(values))+1,'minimum_self_margin_m':margin,'terminal_speed_m_s':speed,'signed_displacement_m':signed,'terminal_pose':trajectory[-1].tolist(),'reasons':reasons,'passed':not reasons}
        records.append(rec)
        if not reasons and(c['family']not in best or clear>best[c['family']]['record']['minimum_clearance_m']):
            best[c['family']]={'record':rec,'controls':controls,'qpos':qq,'qvel':vv,'trajectory':trajectory}
        assert forecast+private_execute<=35000,'PRIVATE_CAP'
    for family,saved in best.items():
        saved['serial_maximum_qpos_qvel_ctrl_errors']=verify_serial(saved)
        with gzip.open(out/(family+'_CERTIFICATE.json.gz'),'wt')as f:json.dump(saved,f,default=lambda x:x.tolist()if isinstance(x,np.ndarray)else x.item())
    assert steps==3264 and forecast==32472 and forecast+private_execute<=35000
    status='FIXED_STATE_CERTIFICATE_FOUND'if best else'FINITE_REGISTERED_SET_NO_CERTIFICATE'
except BaseException as e:
    error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
    signal.alarm(0)
    result={'status':status,'error':error,'elapsed_s':time.monotonic()-started,'replay_native_steps':steps,'forecast_integrations':forecast,'private_execution_integrations':private_execute,'private_prediction_integrations':forecast+private_execute,'maximum_old_qpos_qvel_mocap_errors':worst.tolist(),'minimum_replay_native_clearance_m':minimum,'minimum_replay_self_margin_m':selfmargin,'bad_contacts':bad,'records':records,'qualified_candidates':sum(x['passed']for x in records),'verified_families':{k:v['serial_maximum_qpos_qvel_ctrl_errors']for k,v in best.items()},'new_navigation_tasks':0,'gradient_updates':0,'input_sha256':{str(p.relative_to(repo)):sha(p)for p in [cell/'v648_execution.jsonl',cell/'motion_estimate.jsonl',base/'scene_model.mjb',base/'STATIC_PROTOCOL.json',base/'DYNAMIC_PROTOCOL.json']},'scope':'fixed saved state finite causal command feasibility only; not arrival or global impossibility'}
    dump('COMPLETION.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['records','input_sha256']},indent=2))
    assert status!='FAILED',error
