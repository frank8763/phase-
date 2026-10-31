"""Robot-only control/braking response diagnostic, not a navigation trial."""
import os,time
from pathlib import Path
import numpy as np
from factory import initialize
from robot_predictor import RobotPredictor
from instrumentation import dump
begin=time.monotonic();root=Path(os.environ['PHASE_RUNS'])/'v648_static_unknown/brake_response_probe_21';root.mkdir();c,native=initialize(91000004,root/'paired');env=c['env'];import mujoco
r=RobotPredictor(env,c['B'].PROJECT,mujoco,native);ids=[env.inner.id_lf_steer,env.inner.id_rf_steer,env.inner.id_lr_wheel,env.inner.id_rr_wheel];rows=[]
for delta in [-.61,-.3,0,.3,.61]:
 for wheel in [2.,5.,8.]:
  cmd=np.array(env.inner._ackermann_from_steer_speed(delta,wheel))
  for brake in [24,80,None]:
   t=r.predict(env.data,cmd,ids,np.zeros(4),horizon=240,brake_after=brake)
   rows.append({'delta':delta,'wheel':wheel,'command':cmd,'brake_after':brake,'pose_end':t[-1],'terminal_speed':r.terminal_speed,'path':t})
   print(delta,wheel,brake,'end',np.round(t[-1],3).tolist(),'terminal',round(r.terminal_speed,4),flush=True)
dump(c['out']/'response.json',{'rows':rows,'elapsed_s':time.monotonic()-begin,'actual_navigation_steps':0,'prediction_steps':r.prediction_steps})
