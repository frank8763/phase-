"""Whole saved-data interface and independent domain equivalence; no physics."""
import gzip,json,sys,os
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
for path in [own,repo/'experiments/v773_map_conditioned_progress_audit',repo/'experiments/v769_geometry_reachability_qualification',repo/'experiments/v735_scan_differential_navigation',repo/'runs/v771_audit_dependencies/site']:sys.path.insert(0,str(path))
from risk_domain import RiskDomain
from independent_domain import IndependentDomain
from renewal_state import encode
from exact_footprint import pose_values
from types import SimpleNamespace
read=lambda p:json.loads(p.read_text());pair=repo/'runs/v735_scan_differential_navigation/main01/paired';protocol=read(pair/'STATIC_PROTOCOL.json');bounds=np.asarray(protocol['footprint_bounds']);field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
with gzip.open(pair/'geometry_memory/sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f][:33]
with gzip.open(repo/'runs/v767_certified_progress_release/FEEDBACK_MAIN_OBSERVATIONS.json.gz','rt')as f:packets +=[x['packet']for x in json.load(f)]
reference=repo/'runs/v769_geometry_reachability_qualification';branch=read(repo/'runs/v767_certified_progress_release/FEEDBACK_MAIN_SUMMARY.json');decisions={d['local_public']:d for d in branch['decisions']};os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});maxerr=0.;tests=0
for mode in ['MAP_HISTORY','MAP_FUTURE']:
 online=RiskDomain(protocol['start_qpos'][:2],protocol,mode);independent=IndependentDomain(protocol['start_qpos'][:2],protocol,mode)
 for pkt in packets:
  online.update(pkt);independent.update(pkt);assert encode(online)==encode(independent);local=pkt['step']-32
  if local not in [64,96,116]:continue
  for c in decisions[local]['candidates']:
   z=np.load(repo/'runs/v767_certified_progress_release'/(c['label']+'_PRIVATE.npz'));times=online.time+np.arange(1,329)*.01;a=np.minimum(pose_values(field,z['poses']),online.body_lower(z['poses'],times));b=np.minimum(pose_values(field,z['poses']),independent.body_lower(z['poses'],times));ref=np.load(reference/('QUERY_%03d_%02d.npz'%(local,c['action_index'])));expected=ref['B']if mode=='MAP_HISTORY'else np.maximum(ref['B'],ref['C']);err=max(float(np.max(abs(a-b))),float(np.max(abs(a-expected))));assert err<1e-10;maxerr=max(maxerr,err);tests+=1
  if mode=='MAP_FUTURE':
   sets,_=online.future();other,_=independent.future();assert all(np.array_equal(x,y)for x,y in zip(sets,other))
assert tests==90
root=repo/'runs/v772_domain_prelaunch';root.mkdir(exist_ok=False);(root/'RESULT.json').write_text(json.dumps(dict(status='SAVED_DOMAIN_AND_INDEPENDENT_GEOMETRY_INTERFACES_VERIFIED',packets_per_condition=len(packets),queries=tests,maximum_error=maxerr,all_modes_pure_causal=True,new_initializations=0,new_integrations=0),indent=2)+'\n');print(tests,maxerr)
