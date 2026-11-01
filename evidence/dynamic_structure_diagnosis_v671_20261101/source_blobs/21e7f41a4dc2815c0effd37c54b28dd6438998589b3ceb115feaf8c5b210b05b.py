"""Geometric fixed-pose forecast comparison only, never an executable stop claim."""
import os,sys,json,gzip
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(os.environ['PHASE_REPO']);sys.path.insert(0,str(repo/'experiments/v670_dynamic_empty_samples'))
from motion_tracker import future_boxes,paired_rectangle_clearance
from exact_footprint import pose_values
from union_belief import future_cells,clearance
with gzip.open(repo/'runs/v671_dynamic_consistency_diagnosis/validated_union_states.jsonl.gz','rt')as f:states={r['step']:r for r in map(json.loads,f)if r['dataset'].startswith('v670_')}
root=repo/'runs/v670_dynamic_empty_samples/dev38_95000011_empty/paired';trace=json.loads((root/'geometry_memory/trace.json').read_text());p=json.loads((root/'STATIC_PROTOCOL.json').read_text());bounds=np.asarray(p['footprint_bounds']);field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));rows=[]
for k in [229,639,687]:
 r=states[k];times=np.arange(1,329)*.01;lo,hi=future_boxes(r['state'],times);poses=np.tile(trace[k-1]['pose'],(len(times),1));old=paired_rectangle_clearance(field,poses,(lo+hi)/2,(hi-lo)/2);new=clearance(field,poses,r['cells'],times)
 u,v=future_cells(r['cells'],[3.28]);hull=np.prod(v.max(axis=1)[0]-u.min(axis=1)[0]);baseline=np.prod(hi[-1]-lo[-1]);rows.append({'step':k,'fixed_pose_box_min_m':float(old.min()),'fixed_pose_union_min_m':float(new.min()),'terminal_union_hull_area_m2':float(hull),'terminal_baseline_area_m2':float(baseline),'current_cover_rectangles':len(r['cells'])})
out={'status':'ZERO_INTEGRATION_GEOMETRIC_FORECAST_ONLY','records':rows,'simulation_integrations':0,'navigation_tasks':0,'scope':'fixed geometric robot pose over3.28s, not dynamically executable instantaneous parking or navigation guarantee'};(repo/'runs/v671_dynamic_consistency_diagnosis/UNION_AT_BACKUP_TRIGGERS.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
