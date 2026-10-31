"""Numeric dynamics and self-support validation; no actual navigation/training."""
import argparse,json,os,time,shutil,hashlib
from pathlib import Path
import numpy as np
from factory import initialize
from instrumentation import dump,install_physical_contract
from geometry_predictor import RobotPredictor,SELF_DOMAIN
from serial_predictor import RobotPredictor as Reference
from self_geometry import SelfGeometry,quaternion_matrices
p=argparse.ArgumentParser();p.add_argument('--name',required=True);a=p.parse_args();out=Path(os.environ['PHASE_RUNS'])/'v649_static_stability'/a.name;out.mkdir()
snap=out/'source_snapshot';snap.mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copy2(f,snap/f.name)
started=time.monotonic();c,native=initialize(91000002,out/'paired');env=c['env'];mj=__import__('mujoco');install_physical_contract(env)
new=RobotPredictor(env,c['B'].PROJECT,mj,native);ref=Reference(env,c['B'].PROJECT,mj,native)
for name in ('jnt_range','jnt_limited'):getattr(ref.model,name)[:]=getattr(env.model,name)
ids=[env.inner.id_lf_steer,env.inner.id_rf_steer,env.inner.id_lr_wheel,env.inner.id_rr_wheel];rng=np.random.default_rng(64926);records=[]
for case in range(10):
 target=np.r_[rng.uniform(-.52,.52,2),rng.uniform(-6,6,2)];last=np.zeros(4)
 trajectory=ref.predict(env.data,target,ids,last,horizon=240,brake_after=80);predicted=new.predict(env.data,target,ids,last,horizon=240,brake_after=80)
 error=float(np.max(abs(trajectory-predicted)));speed_error=abs(ref.terminal_speed-new.terminal_speed);assert error<1e-11 and speed_error<1e-11,(case,error,speed_error)
 if case==0:
  explicit=[]
  for qpos in np.vstack((env.data.qpos,new.last_forecast_qpos)):
   new.data.qpos[:]=qpos;mj.mj_kinematics(new.model,new.data);explicit.append(new.self_geometry.actual(new.model,new.data))
  sensor_geometry_error=float(np.max(abs(np.asarray(explicit)-new.last_self_bounds)));assert sensor_geometry_error<1e-11,sensor_geometry_error
 records.append({'case':case,'pose_error_max':error,'terminal_speed_error':speed_error,'minimum_self_domain_margin_m':new.prediction_self_margin,'admitted_self_configuration':bool(new.prediction_self_contained)})
# Independent parametric cylinder surface points against the analytic AABB.
max_escape=0.;max_extrema_gap=0.
for _ in range(200):
 q=rng.normal(size=4);q/=np.linalg.norm(q);R=quaternion_matrices(q[None,:])[0];r,h=rng.uniform(.01,.3,2);angles=np.arange(512)*2*np.pi/512
 surface=np.vstack([np.c_[r*np.cos(angles),r*np.sin(angles),np.full(len(angles),sign*h)]for sign in [-1,1]])@R.T
 axis=R[:2,2];extent=h*abs(axis)+r*np.sqrt(np.maximum(0,1-axis**2));max_escape=max(max_escape,float((abs(surface[:,:2])-extent).max()));max_extrema_gap=max(max_extrema_gap,float((extent-abs(surface[:,:2]).max(axis=0)).max()))
assert max_escape<1e-12 and max_extrema_gap<1e-5,(max_escape,max_extrema_gap)
result={'status':'PASS','prediction_equivalence':records,'sensor_geometry_vs_explicit_kinematics_error_max_m':sensor_geometry_error,'cylinder_surface_cases':200,'cylinder_points_per_case':1024,'maximum_support_escape_m':max_escape,'maximum_sampling_extrema_gap_m':max_extrema_gap,'self_admission_domain_xy':SELF_DOMAIN.tolist(),'required_forecast_self_margin_m':.002,'joint_range_matches_live_model':True,'elapsed_s':time.monotonic()-started,'actual_navigation_steps':0,'prediction_steps_per_engine':2400,'training_updates':0,'scope':'robot/floor model checks; not unknown-obstacle success or global safety proof'}
dump(c['out']/'geometry_prediction_check.json',result);print(json.dumps(result,indent=2))
