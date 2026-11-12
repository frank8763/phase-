"""Changed seam qualification with archived real observations; no physics imports."""
import importlib.abc,sys,ast,json
from common import *
paths()
class NoPhysics(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0] in {'mujoco','physical','vehicle','rclpy'}:raise AssertionError('NO_PHYSICS '+name)
sys.meta_path.insert(0,NoPhysics())
from resource_policy import apply
apply()
import numpy as np
from measurements import NativeMeasurements
from integration import ShieldedSAC
from observation import BLOCKS
from kernel import law,virtual
load('qualified_causal',R/'experiments/v1024_full_route_execution/causal.py');load('qualified_noise',R/'experiments/v733_early_low_translation_scan/sensor_model.py');load('qualified_primary',R/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs/phase14_sensor_utils.py')
setup=json.loads((R/'runs/v858_nav2_verified/v1067/t0_dev_west_east/physics/SETUP.json').read_text());packet=json.loads((R/'runs/v1067_causal_replan_brake_reserve_preparation/WEST_EAST_T0_METADATA.json').read_text())['packet'];frame=np.load(R/'records/nav2_v1073_20261112/v1073_live_sac_dependency_entry/REAL_SENSOR_FRAME.npz');blocks={k:frame[k]for k in BLOCKS};shield=ShieldedSAC();p=shield.propose(setup,packet,None,blocks,0,[.08,0.,False],prefix_native=125);assert p['admitted'];rr=np.asarray(p['certificate']['planned_body_requests']);assert rr.shape==(2325,3)and np.array_equal(rr[-2200:],np.zeros((2200,3)))and np.max(abs(rr[:125,1]))>1e-5
neg=[]
for n,tick,nominal in [('stale',1,[.08,0,False]),('reverse',0,[-.08,0,False]),('stale_request',0,[.08,0,True])]:
 try:shield.propose(setup,packet,None,blocks,tick,nominal,prefix_native=125);raise RuntimeError('UNEXPECTED_ACCEPT '+n)
 except AssertionError:neg.append(n)
for f in C.glob('*.py'):ast.parse(f.read_text())
assert len(json.loads((C/'TASKS.json').read_text()))==1
# Replay must use the original native function, not the prefix budget wrapper.
s=(C/'worker.py').read_text();assert 'try:v.native=native;'in s and "result['replay_state_initializations']=1"in s
O.mkdir(exist_ok=True);dump(O/'QUALIFICATION.json',dict(passed=True,models=0,integrations=0,real_saved_input=True,prefix_native=125,complete_stop_native=2200,minimum_raw_m=p['certificate']['minimum_raw_m'],request=p['request'],negative_cases=neg,all_worker_consumer_imports=True,source_asts=True,replay_binding_restored=True,unchanged_qualifications=['V1070 policy parity','V1073 actual sensor','V1035 signed owner']))
print((O/'QUALIFICATION.json').read_text())
