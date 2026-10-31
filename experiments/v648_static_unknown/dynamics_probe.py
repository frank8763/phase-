"""Diagnostic model-only steering response. No environment world geometry or robot actuation."""
import os,math,time,json
from pathlib import Path
import numpy as np
from factory import initialize
from instrumentation import dump
from robot_predictor import RobotPredictor
started=time.monotonic();root=Path(os.environ['PHASE_RUNS'])/'v648_static_unknown'/'dynamics_probe_10';root.mkdir()
c,native=initialize(91000002,root/'paired');e=c['env'];import mujoco
r=RobotPredictor(e,c['B'].PROJECT,mujoco,native)
ids=[e.inner.id_lf_steer,e.inner.id_rf_steer,e.inner.id_lr_wheel,e.inner.id_rr_wheel]
rows=[]
for steer in [0.,.25,.45,-.45]:
 for gain in [1.,8.]:
  speed=6.;k=math.tan(steer)/float(e.inner.wheel_base);delta=gain*k*float(e.inner.track_width)/2
  command=np.array([steer,steer,speed*(1-delta),speed*(1+delta)])
  path=r.predict(e.data,command,ids,np.zeros(4),horizon=300)
  delta_yaw=(path[-1,2]-path[0,2]+np.pi)%(2*np.pi)-np.pi
  length=np.linalg.norm(np.diff(path[:,:2],axis=0),axis=1).sum()
  rows.append({'steer':steer,'diff_gain':gain,'command':command.tolist(),'length_m':length,'delta_yaw':delta_yaw,'curvature':delta_yaw/max(length,1e-6),'path':path.tolist()})
dump(c['out']/'response.json',{'self_metadata':{k:getattr(e.inner,k)for k in ['wheel_base','track_width','wheel_radius','diff_gain','max_steer']},'rows':rows,'actual_physics_steps':0,'prediction_steps':r.prediction_steps,'elapsed_s':time.monotonic()-started})
print([(x['steer'],x['diff_gain'],round(x['length_m'],3),round(x['curvature'],3))for x in rows])
