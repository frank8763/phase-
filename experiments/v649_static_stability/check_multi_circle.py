"""Synthetic circular-ray mixture test; truth belongs only to the test generator."""
import math,json
from pathlib import Path
import numpy as np
from multi_circle_memory import MultiCircleMemory
rng=np.random.default_rng(64924);memory=MultiCircleMemory();centers=[np.array([-.8,0.]),np.array([.8,.3])];radii=[.2,.25]
for step,x in enumerate(np.linspace(-3,3,100)):
 origin=np.array([x,-1.6]);hits=[]
 for center,radius in zip(centers,radii):
  bearing=math.atan2(*(center-origin)[::-1])
  for offset in np.linspace(-.22,.22,17):
   direction=np.array([math.cos(bearing+offset),math.sin(bearing+offset)]);d=origin-center;b=d@direction;disc=b*b-d@d+radius**2
   if disc<=0:continue
   distance=-b-math.sqrt(disc);measured=np.ceil(distance/.08)*.08+np.clip(rng.normal(0,.03),-.09,.09);hits.append(origin+measured*direction)
 models,remaining,stats=memory.update(hits,[],[],step,origin)
assert len(models)==2,(models,stats)
errors=[float(np.min(np.linalg.norm(models[:,:2]-c,axis=1)))for c in centers];assert max(errors)<.06
result={'status':'PASS','models':models.tolist(),'center_errors_m':errors,'simulation_steps':0,'scope':'synthetic separated static cylinders only, not navigation or calibration'}
out=Path(__file__).resolve().parents[2]/'runs/v649_static_stability/multi_circle_synthetic.json';out.write_text(json.dumps(result,indent=2));print(result)
