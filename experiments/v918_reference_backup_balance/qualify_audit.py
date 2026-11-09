"""Synthetic serialization exercise of the exact causal-map audit; zero models.
Original measurements and existing snapshot files are retained; new map outputs
are explicitly synthetic expected records, never reported as physical evidence.
"""
import copy,gzip,importlib.abc,json,os,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v918_reference_backup_balance';S=O/'saved/runs/v858_nav2_verified/v914/main_we';F=O/'audit_fixture';F.mkdir(exist_ok=False);(F/'physics').mkdir()
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Block());sys.path[:0]=[str(C),str(R/'experiments/v891_dynamic_consistency_software'),str(R/'experiments/v862_ready_static'),str(R/'experiments/v881_timing_accounting_continuation'),str(R/'experiments/v884_feasible_rpp')]
from periodic_support import PeriodicSupport,swept_bounds
from cycle_backup import cycle_upper
from support_envelope import raster_support
import hashlib
for name in ['TASK.json','COMMAND_TUBES.json.gz','COSTMAP_SNAPSHOT_INDEX.json','physics/SETUP.json','physics/SENSORS.json.gz']:
 os.link(S/name,F/name)
(F/'COSTMAP_SNAPSHOTS').mkdir()
for p in (S/'COSTMAP_SNAPSHOTS').iterdir():os.link(p,F/'COSTMAP_SNAPSHOTS'/p.name)
j=json.loads(gzip.decompress((S/'MOTION_ENVELOPE.json.gz').read_bytes()));prior=PeriodicSupport();lookup={};prior_lookup={};states={}
for row in j['states']:
 prior.update(row['time'],row['native_tick'],row['support_bounds']);lookup[row['native_tick']]=None if prior.last is None else cycle_upper(prior.snapshot())+.16;prior_lookup[row['native_tick']]=None if prior.last is None else prior.snapshot();states[row['native_tick']]=row
def finite(source):
 st=states[source['source_native_tick']];pr=prior_lookup[source['source_native_tick']]
 if st['support_bounds']is None:return None
 at=source['forecast_sim_time'];high=np.asarray(st['support_bounds'])+.1+.08*(max(0.,at-st['time'])+2.5)
 if pr is not None:high=np.minimum(high,swept_bounds(pr['vertices'],st['time'],at+2.5)+.1)
 return high
for row in j['publications']:
 high=lookup[row['source_native_tick']]if row['map_role']=='GLOBAL_REFERENCE'else finite(row);row['forecast_support']=None if high is None else high.tolist();grid=raster_support(high)
 if row['map_role']=='GLOBAL_REFERENCE':grid[grid>0]=50
 row['map_sha256']=hashlib.sha256(grid.tobytes()).hexdigest()
routes=json.loads((S/'ROUTER_REQUESTS.json').read_text())
for row in routes:
 if 'causal_forecast_source'not in row:continue
 s=row['causal_forecast_source'];high=lookup[s['source_native_tick']];local=finite(s)
 s['forecast_support']=None if local is None else local.tolist();s['reference_support']=None if high is None else high.tolist()
(F/'ROUTER_REQUESTS.json').write_text(json.dumps(routes)+'\n')
def write():
 with gzip.open(F/'MOTION_ENVELOPE.json.gz','wt')as f:json.dump(j,f)
write();from motion_audit import audit
result=audit(F);checks=dict(exact_new_map_audit_positive=result['passed'])
row=next(r for r in j['publications']if r['forecast_support']is not None);row['forecast_support'][0]+=.01;write()
try:audit(F)
except AssertionError:checks['tampered_forecast_rejected']=True
else:checks['tampered_forecast_rejected']=False
row['forecast_support'][0]-=.01;write()
report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,synthetic_expected_serialization_only=True,scope='New whole-cycle map serialization/reconstruction and corrupt-map negative using existing V914 observations; no new physical/forecast coverage claim.')
(O/'AUDIT_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert report['passed']
