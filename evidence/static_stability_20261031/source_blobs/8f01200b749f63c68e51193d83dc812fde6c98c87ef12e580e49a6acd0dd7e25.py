"""Numerical and timing equivalence in robot/floor models, no navigation."""
import os,time,hashlib,shutil
from pathlib import Path
import numpy as np
from factory import initialize
from instrumentation import dump
from serial_predictor import RobotPredictor as Serial
from robot_predictor import RobotPredictor as Fast
root=Path(os.environ['PHASE_RUNS'])/'v649_static_stability'/'rollout_equivalence_01';root.mkdir(parents=True)
for f in Path(__file__).parent.glob('*.py'):
 target=root/'source_snapshot'/f.name;target.parent.mkdir(exist_ok=True);shutil.copy2(f,target)
begin=time.monotonic();c,native=initialize(91000004,root/'paired');env=c['env'];import mujoco
slow=Serial(env,c['B'].PROJECT,mujoco,native);fast=Fast(env,c['B'].PROJECT,mujoco,native);ids=[env.inner.id_lf_steer,env.inner.id_rf_steer,env.inner.id_lr_wheel,env.inner.id_rr_wheel]
rng=np.random.default_rng(64923);cases=[]
for n in range(10):
 steer=float(rng.uniform(-.6,.6));wheel=float(rng.uniform(-8,8));command=np.asarray(env.inner._ackermann_from_steer_speed(steer,wheel));last=rng.uniform(-1,1,4);last[:2]*=.3
 t=time.monotonic();a=slow.predict(env.data,command,ids,last,horizon=240,brake_after=80);ts=time.monotonic()-t;vs=slow.terminal_speed
 t=time.monotonic();b=fast.predict(env.data,command,ids,last,horizon=240,brake_after=80);tf=time.monotonic()-t;vf=fast.terminal_speed
 err=float(np.max(np.abs(a-b)));verr=abs(vs-vf);assert err<1e-10 and verr<1e-10,(n,err,verr)
 cases.append({'case':n,'max_pose_error':err,'terminal_speed_error':verr,'serial_s':ts,'cpp_s':tf})
result={'status':'PASS','cases':cases,'serial_total_s':sum(x['serial_s']for x in cases),'cpp_total_s':sum(x['cpp_s']for x in cases),'actual_navigation_steps':0,'prediction_steps_per_engine':2400,'elapsed_s':time.monotonic()-begin,'scope':'same robot/floor model, command profiles, initial self state; does not validate unknown environment safety'}
dump(c['out']/'equivalence.json',result);print(result,flush=True)
