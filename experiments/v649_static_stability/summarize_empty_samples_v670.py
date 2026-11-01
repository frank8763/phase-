"""Post-run information/progress accounting. No controller or simulator imports."""
from pathlib import Path
import json,gzip,math
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v670_dynamic_empty_samples';path=root/'dev38_95000011_empty/paired/geometry_memory'
read=lambda p:json.loads(p.read_text())
rows=[json.loads(s)for s in(path/'motion_estimate.jsonl').read_text().splitlines()]
r=read(path/'result.json')if(path/'result.json').exists()else read(path/'interrupted.json');trace=read(path/'trace.json')
native=[]
with gzip.open(path/'dynamic_native.jsonl.gz','rt')as f:native=[json.loads(line)for line in f]
r['goal_distance_m']=trace[-1]['goal_distance_m'];r['minimum_dynamic_native_clearance_m']=min(row['actual_clearance_m']for row in native)
contracts=[s['empty_sample_contract']for s in rows]
nonempty=[s for s in contracts if s['removed_cells']>0]
full_erasure=[s for s in nonempty if s['area_after_m2']>=s['area_before_m2']-1e-12]
points=np.asarray([t['pose'][:2]for t in trace]);distance=np.asarray([t['goal_distance_m']for t in trace])if 'goal_distance_m'in trace[0]else np.asarray([np.linalg.norm(np.asarray(t['pose'][:2])-read(path.parent/'STATIC_PROTOCOL.json')['goal_xy'])for t in trace])
result={'status':'COMPLETED_DEVELOPMENT_DIAGNOSIS','strict_arrival':r['strict_safe_arrival'],'outcome':r['outcome'],'decision_frames':len(rows),'public_steps':r['public_steps'],'native_steps':r['physics_steps'],'minimum_actual_native_clearance_m':r['minimum_dynamic_native_clearance_m'],
'frames_with_continuous_cells_removed':len(nonempty),'frames_whose_outer_rectangle_erased_all_current_cell_removal':len(full_erasure),'full_hull_refill_fraction_among_pruned_frames':len(full_erasure)/len(nonempty)if nonempty else None,
'average_removed_cell_fraction':float(np.mean([x['removed_cells']/1024 for x in contracts])),
'average_immediate_area_reduction_fraction':float(np.mean([1-x['area_after_m2']/x['area_before_m2']for x in contracts])),
'frames_without_certified_unknown_return':sum(not x['observed_this_frame']for x in rows),'maximum_age_s':max(x['age_s']for x in rows),'terminal_position_box_area_m2':contracts[-1]['area_after_m2'],
'path_length_m':float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum()),'best_goal_distance_m':float(distance.min()),'final_goal_distance_m':r['goal_distance_m'],'simulation_integrations':0,
'scope':'real executed development negative result; hull refilling is a representational loss diagnostic, not a proof that union tracking solves navigation'}
(root/'INFORMATION_PROGRESS_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
