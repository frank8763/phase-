"""Zero-integration check of current rectangular and circular-Minkowski gates."""
import os,sys,json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(os.environ['PHASE_REPO']);sys.path.insert(0,str(repo/'experiments/v670_dynamic_empty_samples'))
from exact_footprint import pose_values
from motion_tracker import paired_rectangle_clearance
root=repo/'runs/v670_dynamic_empty_samples/dev38_95000011_empty/paired';model=json.loads((root/'STATIC_PROTOCOL.json').read_text());cell=root/'geometry_memory';trace=json.loads((cell/'trace.json').read_text());states={r['step']:r for r in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};events=[r for r in map(json.loads,(cell/'gear_transitions.jsonl').read_text().splitlines())if r['status']=='RESERVED_RECOVERY_START'];bounds=np.asarray(model['footprint_bounds']);field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(model['known_rectangles']).reshape(-1,4),circles=np.asarray(model['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));rows=[]
for e in events:
 k=e['step'];s=states[k];pose=np.asarray(trace[k-1]['pose']);lo=np.asarray(s['position_lower']);hi=np.asarray(s['position_upper']);old=SimpleNamespace(**{**field.__dict__,'rectangles':np.asarray([*model['known_rectangles'],s['current_outer_rectangle']])});square=float(pose_values(old,[pose])[0]);minkowski=float(min(pose_values(field,[pose])[0],paired_rectangle_clearance(field,pose[None,:],((lo+hi)/2)[None,:],((hi-lo)/2)[None,:])[0]));rows.append({'activation_step':k,'square_expanded_current_box_clearance_m':square,'circular_minkowski_current_box_clearance_m':minkowski,'hard_floor_forced_by_current_box':square<.15-1e-5})
out={'status':'ZERO_INTEGRATION_TRIGGER_ANALYSIS','events':rows,'simulation_integrations':0,'navigation_tasks':0};(repo/'runs/v671_dynamic_consistency_diagnosis/BACKUP_TRIGGER_DIAGNOSIS.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
