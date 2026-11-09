"""Counterfactual request reconstruction on saved inputs, no model execution."""
import gzip,importlib.abc,json,sys,time
from pathlib import Path
from collections import Counter
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v922_reference_consistency_diagnosis';N=R/'runs/v858_nav2_verified/v920/main_we'
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','factory','physical','vehicle','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Block());sys.path.insert(0,str(R/'experiments/v920_native_ingress'))
from command_tube import admit
rows=json.loads(gzip.decompress((N/'COMMAND_TUBES.json.gz').read_bytes()));known=json.loads((N/'physics/SETUP.json').read_text())['known'];counts=Counter();timings=[];reconstructed=[]
for row in rows:
 p=row['proof']
 if [p['v'],p['w']]==row['wanted']:continue
 before=time.perf_counter();a=admit(row['packet'],row['source'],*row['wanted'],known,p['issued_at']);timings.append(time.perf_counter()-before)
 reasons=[k for k in ['static_lower_m','dynamic_lower_m','terminal_cycle_lower_m']if a[k]is not None and a[k]<.155]
 counts.update(reasons);reconstructed.append(dict(tick=p['body_native_tick'],wanted=row['wanted'],fallback=[p['v'],p['w']],reasons=reasons,wanted_proof=a))
j=json.loads(gzip.decompress((N/'INGRESS.json.gz').read_bytes()));ros=json.load(open(N/'ROS_RESULT.json'));last=j['receipts'][-1];stop=j['receipts'][-2]
result=dict(models=0,integrations=0,full_saved_decisions=len(rows),reconstructed_fallbacks=len(reconstructed),failure_categories=dict(counts),all_original_requests_refused=all(not r['wanted_proof']['passed']for r in reconstructed),geometry_recompute_wall_s=dict(median=float(np.median(timings)),p99=float(np.quantile(timings,.99)),maximum=max(timings)),recompute_not_historical_latency_attribution=True,original_runtime_sequence=dict(last_observation_sent_at=ros['last_observation']['sent_at'],stop_issued_at=stop['packet']['issued_at'],stop_received_at=stop['received_at'],stop_reason=stop['packet']['reason'],late_command_issue=last['packet']['issued_at'],late_command_receive=last['received_at'],late_command_age=last['received_at']-last['packet']['issued_at'],late_sequence=last['packet']['sequence'],old_sequence_retained=last['prior_sequence'],native_error=last.get('error'),original_stale_observation_error=ros['error']),reconstructed_requests=reconstructed)
(O/'SAVED_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='reconstructed_requests'},indent=2))
