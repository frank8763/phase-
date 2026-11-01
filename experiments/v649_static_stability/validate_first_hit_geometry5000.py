"""Independent sample-ray geometry and causal packet validation; zero integration."""
from pathlib import Path
import os,sys,json,gzip,hashlib,importlib.util,time
import numpy as np
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);src=repo/'experiments/v667_dynamic_first_hit'
sys.path.insert(0,str(src))
from motion_tracker import capsule_constraints,Tracker,future_boxes
spec=importlib.util.spec_from_file_location('old_interval_tracker',repo/'experiments/v666_dynamic_dense_navigation/motion_tracker.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
rng=np.random.default_rng(66701);worst=-float('inf');usable=0;started=time.monotonic()
for i in range(5000):
    origin=rng.uniform(-1,1,2).astype(np.float32)
    angle=rng.uniform(-np.pi,np.pi);direction=np.asarray([np.cos(angle),np.sin(angle)],np.float32)
    center=origin+rng.uniform(.20,2.70)*direction+rng.uniform(-.08,.08)*np.array([-direction[1],direction[0]])
    ds=np.arange(0,3.000001,.08)
    points=(origin[None,:]+ds.astype(np.float32)[:,None]*direction).astype(float)
    ids=np.flatnonzero(np.linalg.norm(points-center,axis=1)<=.10)
    if not len(ids):continue
    hit=ds[ids[0]];bound=[.06,.09][i%2];z=float(hit+rng.uniform(-bound,bound))
    ray=np.r_[origin,direction,z,bound,0.]
    A,b,count=capsule_constraints(np.asarray([ray]),[],[])
    assert count==1,'INDEPENDENT_GENERATOR_SHOULD_CERTIFY_UNKNOWN'
    excess=float(np.max(A@center-b));worst=max(worst,excess);usable+=1
    assert excess<=1e-7,('FIRST_HIT_PLANE_EXCLUDES_TRUE_CENTER',i,excess)
assert usable==5000,'MUST_PRODUCE_5000_FIRST_HITS'
result={'status':'PASS','first_hits_checked':usable,'maximum_constraint_excess_m':worst,'elapsed_s':time.monotonic()-started,'simulation_steps':0,'navigation_tasks':0,'random_seed':66701,'scope':'independent known-radius disk/discrete-ray generator with guaranteed intersecting chord; original22 nonreturns retained, not counted as constraint checks'}
out=repo/'runs/v667_dynamic_first_hit/OFFLINE_5000_FIRST_HIT_GEOMETRY.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
