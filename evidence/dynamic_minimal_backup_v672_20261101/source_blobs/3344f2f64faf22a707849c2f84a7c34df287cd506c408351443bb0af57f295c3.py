"""Private initial-state stop forecast and command-rate checks. No navigation."""
from pathlib import Path
from types import SimpleNamespace,MethodType
import os,json,sys,time,hashlib
import numpy as np
import mujoco
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);src=Path(__file__).resolve().parent
from geometry_predictor import RobotPredictor
from reserved_recovery import ReservedRecovery
from motion_tracker import install_time_gate
from exact_footprint import pose_values
old=repo/'runs/v670_dynamic_empty_samples/dev38_95000011_empty/paired';protocol=json.loads((old/'STATIC_PROTOCOL.json').read_text());m=mujoco.MjModel.from_binary_path(str(old/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];d.qvel[:]=0.;mujoco.mj_forward(m,d)
predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,mujoco.mj_step)
ids=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_ACTUATOR,n)for n in ['left_front_steer_act','right_front_steer_act','left_rear_wheel_act','right_rear_wheel_act']]
state=json.loads((old/'geometry_memory/motion_estimate.jsonl').read_text().splitlines()[0]);bounds=np.asarray(protocol['footprint_bounds']);field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));field.pose_values=MethodType(pose_values,field);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
trajectory=predictor.predict(d,np.zeros(4),ids,np.zeros(4),horizon=320,brake_after=160);idle_speed=predictor.terminal_speed;idle_margin=predictor.prediction_self_margin
root=repo/'runs/v672_dynamic_minimal_backup';root.mkdir(exist_ok=True);manager=ReservedRecovery(predictor,mujoco,ids,root)
summary=manager.admit_nominal(d,np.asarray([0.,0.,.7,.7]),field,state,0);assert summary is not None and summary['recovery_kind']=='BRAKE_ONLY'
ctrl=manager.cache['controls'][::8];initial=np.asarray([0.,0.,.7,.7]);delta=np.diff(np.vstack((initial,ctrl)),axis=0)
checks={'valid_brake_kind':manager.cache['recovery_kind']=='BRAKE_ONLY','native_idle_terminal_speed':idle_speed<=.025,'native_idle_self_domain':idle_margin>=.002,'full_certificate':summary['reserve_minimum_clearance_m']>=.155,'terminal_speed':manager.cache['terminal_speed_m_s']<=.025,'steering_hold':np.max(abs(ctrl[:,:2]-initial[:2]))==0,'slew_limits':np.max(abs(delta[:,:2]))<=.10+1e-12 and np.max(abs(delta[:,2:]))<=.70+1e-12,'full_finite_state_controls':len(manager.cache['qpos'])==len(manager.cache['qvel'])==len(manager.cache['controls'])==320}
result={'status':'PASS'if all(checks.values())else'FAIL','checks':checks,'summary':summary,'private_prediction_integrations':predictor.prediction_steps,'actual_navigation_native_steps':0,'control_log_replay_native_steps':0,'navigation_tasks':0,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in src.glob('*.py')},'scope':'fixed initial private model and command schedule checks, not full-state real execution validation'}
(root/'PRE_NAV_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='source_sha256'},indent=2));assert all(checks.values())
