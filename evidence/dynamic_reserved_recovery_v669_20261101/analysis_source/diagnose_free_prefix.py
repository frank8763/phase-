"""Unused free-prefix information in fixed recorded packets; no tracker update."""
import os,json,gzip,time
from pathlib import Path
import numpy as np
repo=Path(os.environ['PHASE_REPO']);root=repo/'runs/v669_dynamic_reserved_recovery/dev37_95000011_reserve/paired'
with gzip.open(root/'geometry_memory/sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
states=[json.loads(s)for s in(root/'geometry_memory/motion_estimate.jsonl').read_text().splitlines()];config=json.loads((root/'DYNAMIC_PROTOCOL.json').read_text())
started=time.monotonic();records=[]
for packet,state in zip(packets,states):
    lo=np.asarray(state['position_lower']);hi=np.asarray(state['position_upper']);points=[]
    for ray in packet['rays']:
        ds=np.arange(0,3.000001,.08);ds=ds[ds<ray[4]-ray[5]-1e-4]
        origin=np.asarray(ray[:2],np.float32);direction=np.asarray(ray[2:4],np.float32)
        sample=(origin[None,:]+ds.astype(np.float32)[:,None]*direction).astype(float)
        near=np.all(sample>=lo-.1001,axis=1)&np.all(sample<=hi+.1001,axis=1)
        points.extend(sample[near])
    points=np.asarray(points).reshape(-1,2)
    centers=np.stack(np.meshgrid(np.arange(lo[0],hi[0]+1e-8,.01),np.arange(lo[1],hi[1]+1e-8,.01),indexing='ij'),axis=-1).reshape(-1,2)
    incompatible=np.any(np.sum((centers[:,None,:]-points[None,:,:])**2,axis=-1)<(.10-1e-4)**2,axis=1)if len(points)else np.zeros(len(centers),bool)
    truth=np.asarray(config['anchor_xy'])+np.sin(state['time']*config['omega_rad_s']+config['phase_rad'])*config['amplitude_m']*np.asarray(config['axis_xy'])
    true_excluded=bool(len(points)and np.any(np.linalg.norm(points-truth,axis=1)<.10-1e-4))
    records.append({'step':packet['step'],'nearby_guaranteed_unhit_sample_points':len(points),'diagnostic_grid_centers':len(centers),'grid_centers_inconsistent_with_free_prefix':int(sum(incompatible)),
     'incompatible_fraction':float(np.mean(incompatible)),'evaluator_true_center_excluded':true_excluded,'actor_observed_this_frame':state['observed_this_frame']})
output={'status':'DIAGNOSTIC_NO_TRUE_CENTER_EXCLUSION'if not any(r['evaluator_true_center_excluded']for r in records)else'DIAGNOSTIC_SENSOR_CONSISTENCY_FAILURE',
 'frames':len(records),'simulation_steps':0,'navigation_tasks':0,'tracker_updates':0,'elapsed_s':time.monotonic()-started,
 'frames_with_unused_nearby_empty_samples':sum(r['nearby_guaranteed_unhit_sample_points']>0 for r in records),
 'mean_incompatible_grid_fraction':float(np.mean([r['incompatible_fraction']for r in records])),
 'terminal_frame':records[-1],'records':records,
 'scope':'frozen recorded inputs only, approximate point-hypothesis diagnostic; not a certified continuous posterior, fourth algorithm candidate, control change or navigation result'}
out=repo/'runs/v669_dynamic_reserved_recovery/FREE_PREFIX_INFORMATION_DIAGNOSIS.json';out.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({k:v for k,v in output.items()if k!='records'},indent=2))
