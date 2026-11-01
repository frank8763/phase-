"""Independently verify all saved causal drive-prefix route projections; zero integration."""
import json,sys,os,argparse,hashlib
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
p=argparse.ArgumentParser();p.add_argument('paired');a=p.parse_args();root=Path(a.paired);repo=Path(os.environ['PHASE_REPO']);sys.path.insert(0,str(root.parent/'source_snapshot'))
from exact_footprint import pose_values
read=lambda p:json.loads(p.read_text());states={x['step']:x for x in map(json.loads,(root/'geometry_memory/motion_estimate.jsonl').read_text().splitlines())};checks=[]
for file in sorted((root/'geometry_memory').glob('planning_*.json')):
 row=read(file);state=states[row['step']];world=row['causal_input'];actual=row['causal_route_input'];meta=row['route_projection'];expected=dict(world);expected['sensor_points']=[]
 if state['center']is not None:
  t=np.linspace(0,.8,9)[:,None];lo=np.asarray(state['position_lower']);hi=np.asarray(state['position_upper']);vl=np.asarray(state['velocity_lower']);vu=np.asarray(state['velocity_upper']);lower=np.maximum(lo+t*vl-.02*t*t,lo-.12*t);upper=np.minimum(hi+t*vu+.02*t*t,hi+.12*t);padding=.12*.05+1e-5;low=lower.min(axis=0)-padding;high=upper.max(axis=0)+padding;expected['rectangles']=[*world['rectangles'],[*((low+high)/2),*((high-low)/2+.1)]]
 projection=all(np.allclose(np.asarray(actual[k]).reshape(-1,4 if k=='rectangles'else 3 if k=='circles'else 2),np.asarray(expected[k]).reshape(-1,4 if k=='rectangles'else 3 if k=='circles'else 2),atol=1e-12,rtol=0)for k in ['rectangles','circles','sensor_points']);geometry=True;minimum=None
 if row['path']is not None:
  path=np.asarray(row['path']);dense=[]
  for first,last in zip(path[:-1],path[1:]):
   diff=last[:3]-first[:3];diff[2]=(diff[2]+np.pi)%(2*np.pi)-np.pi
   for frac in np.arange(5)/5:dense.append(first[:3]+frac*diff)
  dense.append(path[-1,:3]);bounds=np.asarray(actual['footprint_bounds']);field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(actual['rectangles']).reshape(-1,4),circles=np.asarray(actual['circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));minimum=float(np.min(pose_values(field,dense)));geometry=minimum>=row['stats']['guard_m']-1e-8 and abs(minimum-row['stats']['minimum_clearance_m'])<=1e-8
 ck={'only_registered_causal_projection':projection,'horizon':row['route_projection_horizon_s']==.8 and(meta.get('horizon_s',.8)==.8),'no_truth_input':meta['hidden_world_geometry_used']is False,'all_dense_edges':geometry};checks.append({'step':row['step'],'checks':{k:bool(v)for k,v in ck.items()},'minimum_clearance_m':minimum,'passed':bool(all(ck.values()))})
out={'status':'ALL_CAUSAL_PREFIX_ROUTE_PROJECTIONS_PASS'if checks and all(x['passed']for x in checks)else'FAIL','records':checks,'simulation_integrations':0,'helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'spatial proposals only, not physical dynamics or complete temporal trajectory feasibility'};(root/'PREFIX_ROUTE_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'],len(checks));assert out['status']!='FAIL'
