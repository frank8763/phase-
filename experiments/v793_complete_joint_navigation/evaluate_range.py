"""Descriptive offline coverage of retained circle models, never planner input."""
import argparse,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('paired');a=p.parse_args();root=Path(a.paired);protocol=json.loads((root/'STATIC_PROTOCOL.json').read_text());unknown=protocol['physical_unknown_obstacles'];rows=[]
for log in sorted(root.glob('*/range_estimate.jsonl')):
    entries=[json.loads(x)for x in log.read_text().splitlines()];covered_frames=0;all_models_frames=0;slacks=[];statuses={}
    for x in entries:
        models=np.asarray(x['models']).reshape(-1,3)
        for fit in x['fits']:statuses[fit['status']]=statuses.get(fit['status'],0)+1
        if not len(models):continue
        all_models_frames+=1
        each=[max(m[2]-u['radius']-np.linalg.norm(m[:2]-u['xy'])for m in models)for u in unknown]
        slacks.append(min(each));covered_frames+=int(min(each)>=0)
    rows.append({'condition':log.parent.name,'sensor_frames':len(entries),'frames_with_models':all_models_frames,'frames_all_true_circles_enclosed':covered_frames,'minimum_descriptive_enclosure_slack_m':min(slacks)if slacks else None,'fit_status_frame_counts':statuses,'scope':'correlated development frames; missing/merged models count against all-object coverage, no calibrated or formal guarantee'})
result={'scope':'truth-only post-run descriptive diagnostic, no policy or simulation steps','rows':rows};(root/'RANGE_COVERAGE_AUDIT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
