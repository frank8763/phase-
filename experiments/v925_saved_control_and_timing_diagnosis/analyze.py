import gzip,importlib.abc,json,sys,time
from pathlib import Path
from collections import Counter
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v925_saved_control_and_timing_diagnosis';N=R/'runs/v858_nav2_verified/v924/main_we';begun=time.monotonic()
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','factory','physical','vehicle','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Block());sys.path[:0]=[str(R/'experiments/v924_consistent_polygon_reference'),str(R/'experiments/v887_exact_lidar_software')]
from command_tube import admit
rows=json.loads(gzip.decompress((N/'COMMAND_TUBES.json.gz').read_bytes()));known=json.load(open(N/'physics/SETUP.json'))['known'];cases=[];counts=Counter();tiny=Counter()
for r in rows:
 p=r['proof']
 if [p['v'],p['w']]!=r['wanted']:
  a=admit(r['packet'],r['source'],*r['wanted'],known,p['issued_at']);why=[k for k in ['static_lower_m','dynamic_lower_m','terminal_cycle_lower_m']if a[k]is not None and a[k]<.155];counts.update(why)
  if a['residual_position_m']==.04:tiny['reversal_class']+=1;tiny['reversal_class_measured_speed_below_1mm_s']+=int(abs(p['body'][3])<.001)
for target in [9000,11000,13000,14800]:
 r=[r for r in rows if not r.get('wait_renewal')and r['packet']['native_tick']<=target][-1];now=r['proof']['issued_at'];out=[]
 controls=[[0.,0.]]+[[v,v*k]for v in [-.1,-.05,.05,.1]for k in [-.758770385,0.,.758770385]]
 for v,w in controls:
  a=admit(r['packet'],r['source'],v,w,known,now);out.append(dict(v=v,w=w,passed=a['passed'],static=a['static_lower_m'],dynamic=a['dynamic_lower_m'],terminal=a['terminal_cycle_lower_m'],residual=a['residual_position_m']))
 cases.append(dict(target_tick=target,actual_packet_tick=r['packet']['native_tick'],body=r['packet']['body'],original_requested=r['wanted'],controls=out))
from support_envelope import SupportEnvelope
from exact_lidar import get_lidar_features
from periodic_support import PeriodicSupport
j=json.loads(gzip.decompress((N/'MOTION_ENVELOPE.json.gz').read_bytes()));tracker=SupportEnvelope(known,get_lidar_features);periodic=PeriodicSupport();times=[]
for scan in j['observations']:
 t=time.perf_counter();tracker.update(scan);middle=time.perf_counter();updated=periodic.update(tracker.when,tracker.latest['native_tick'],tracker.support);end=time.perf_counter()
 times.append(dict(native_tick=scan['native_tick'],tracker_s=middle-t,periodic_s=end-middle,periodic_updated=updated,vertices=[len(p.v)for p in periodic.polytopes]));assert time.monotonic()-begun<180
summaries={}
for k in ['tracker_s','periodic_s']:
 a=np.array([x[k]for x in times]);i=int(a.argmax());summaries[k]=dict(total=float(a.sum()),median=float(np.median(a)),p99=float(np.quantile(a,.99)),maximum=float(a.max()),at_tick=times[i]['native_tick'])
report=dict(models=0,integrations=0,unchanged_gate_rejection_counts=dict(counts),conditional_empirical_class_counts=dict(tiny),fixed_cases=cases,causal_observations_recomputed=len(times),recompute_timing=summaries,historical_delay_cpu_attribution_unknown=True,timing_rows=times,elapsed_s=time.monotonic()-begun)
(O/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['fixed_cases','timing_rows']},indent=2));print([(r['actual_packet_tick'],r['body'][3],[(c['v'],c['w'])for c in r['controls']if c['passed']])for r in cases])
