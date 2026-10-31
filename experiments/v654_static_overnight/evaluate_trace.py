"""Offline truth-only evaluation. Never imported or called by online control."""
import argparse,json,math
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from exact_footprint import pose_values
p=argparse.ArgumentParser();p.add_argument('paired');a=p.parse_args();root=Path(a.paired);protocol=json.loads((root/'STATIC_PROTOCOL.json').read_text())
unknowns=protocol.get('physical_unknown_obstacles')
if unknowns is None:
 add=root/'EVALUATION_SCENE_ADDENDUM.json'
 if add.exists():unknowns=json.loads(add.read_text())['physical_unknown_obstacles']
 else:raise RuntimeError('PHYSICAL_UNKNOWN_INVENTORY_REQUIRED_FOR_TRUTH_EVALUATION')
b=np.array(protocol['footprint_bounds']);circles=protocol['known_circles']+[[*u['xy'],u['radius']]for u in unknowns]
field=SimpleNamespace(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.array(protocol['known_rectangles']).reshape(-1,4),circles=np.array(circles).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
rows=[]
for trace in sorted(root.glob('*/trace.json')):
 t=json.loads(trace.read_text());res=json.loads((trace.parent/'result.json').read_text());poses=np.array([r['pose']for r in t]).reshape(-1,3)
 if not len(poses):continue
 margin=pose_values(field,poses);length=float(np.linalg.norm(np.diff(poses[:,:2],axis=0),axis=1).sum());row={'condition':res['condition'],'outcome':res['outcome'],'strict_safe_arrival':res['strict_safe_arrival'],'path_length_m':length,'minimum_true_envelope_clearance_at_public_samples_m':float(margin.min()),'public_samples_true_clearance_below_015':int((margin<.15).sum()),'simulation_s':res['physics_steps']*.01,'wall_s':res['elapsed_s'],'wall_to_simulation_ratio':res['elapsed_s']/(res['physics_steps']*.01)}
 admission=trace.parent/'model_admission.jsonl'
 if admission.exists():
  entries=[json.loads(x)for x in admission.read_text().splitlines()];errors=[]
  for e in entries:
   if e['step']>=len(t):continue
   predicted=np.array(e['predicted_next_pose']);actual=poses[e['step']];errors.append([np.linalg.norm(predicted[:2]-actual[:2]),abs((predicted[2]-actual[2]+np.pi)%(2*np.pi)-np.pi)])
  if errors:
   errors=np.array(errors);row['prediction_next_xy_error_p95_m']=float(np.quantile(errors[:,0],.95));row['prediction_next_xy_error_max_m']=float(errors[:,0].max());row['prediction_next_yaw_error_p95_rad']=float(np.quantile(errors[:,1],.95))
 fitfile=trace.parent/'circle_estimate.jsonl'
 if fitfile.exists()and len(unknowns)==1:
  fits=[json.loads(x)for x in fitfile.read_text().splitlines()];fits=[x for x in fits if x['status']=='CYLINDER_ESTIMATE'];truth=unknowns[0]
  if fits:
   errs=np.array([np.linalg.norm(np.array(x['center'])-truth['xy'])for x in fits]);cover=np.array([x['envelope_radius_m']>=truth['radius']+err for x,err in zip(fits,errs)])
   row['accepted_fit_frames']=len(fits);row['descriptive_true_circle_enclosed_frames']=int(cover.sum());row['fit_center_error_max_m']=float(errs.max());row['fit_coverage_scope']='correlated development frames, not calibrated independent coverage'
 rows.append(row)
result={'scope':'offline evaluator uses physical scene geometry and the recorded fixed planning envelope transformed by root pose; actual articulated primitive geometry is audited separately; public-sample clearance is not a continuous-time guarantee; native contact audit covers the full robot body subtree','rows':rows}
(root/'EVALUATION_METRICS.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
