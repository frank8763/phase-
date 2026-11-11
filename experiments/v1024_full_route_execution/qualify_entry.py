"""Real imports, finite braking and causal scene adapter, every model blocked."""
import copy,importlib.abc,importlib.util,json,sys,time,types
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1024_full_route_execution';sys.path[:0]=[str(C),str(R/'experiments/v1023_dense_input_route')]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());import worker
from causal import Evidence,brake
fixture=next(x for x in json.loads((R/'records/nav2_v1022_20261111/DYNAMIC_REJECTION_FIXTURES.json').read_text())if x['route']=='we');p=fixture['packet'];source=fixture['source'];setup=fixture['setup'];e=Evidence(setup['known'])
# A synthetic envelope for a finite brake: axes are outer supports, plus the
# original measured source/time. This is not an actor trajectory or new success.
from geometry_model import ref
geometry=ref._old.Geometry(setup['known'],source['periodic']);poly=geometry.center_polygon
from causal import NORMALS
e.first={'from_saved_causal_prior':True};e.envelope.support=poly@NORMALS.T;e.envelope.support=e.envelope.support.max(axis=0);e.envelope.when=p['sim_time'];e.last_scan=dict(native_tick=p['native_tick'])
b=brake(setup,p,e);assert b['passed']and len(b['planned_body_requests'])==200
checks=dict(actual_worker_import_blocked_all_models=True,fixed_causal_200_brake_qualified=True)
q=copy.deepcopy(p);q['sim_time']+=.052
try:brake(setup,q,e)
except AssertionError as ex:assert str(ex)=='BRAKE_SOURCE_STALE';checks['stale_brake_rejected']=True
else:raise AssertionError('STALE_BRAKE_ACCEPTED')
# Poison truth keys: source adapter must never read them.
scan=dict(native_tick=0,time=0.,xy=[-4.,-2.],yaw=0.,ranges=[3.]*32,raw_lidar=object(),actor_xy=object(),phase=object(),future=object())
clear=Evidence(setup['known']);assert not clear.update(scan);checks['scan_truth_keys_excluded']=True
out=dict(passed=all(checks.values()),checks=checks,minimum_saved_brake_raw_m=b['minimum_raw_clearance_m'],models=0,integrations=0,physical_ready=False)
(O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
