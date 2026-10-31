"""Synthetic quantized/noisy range-model check, no hidden truth to the estimator."""
import json,math,time
from pathlib import Path
import numpy as np
from range_circle_memory import fit_ranges
rng=np.random.default_rng(64925);results=[];started=time.monotonic()
for case in range(3):
 center=rng.uniform(-1,1,2);radius=float(rng.uniform(.18,.3));rays=[]
 for x in np.linspace(-2,2,35):
  origin=center+[x,-1.5];bearing=np.arctan2(*(center-origin)[::-1])
  for offset in np.linspace(-.2,.2,17):
   d=np.array([np.cos(bearing+offset),np.sin(bearing+offset)]);delta=center-origin;along=delta@d;disc=radius**2-(delta@delta-along**2)
   if disc<=0:continue
   h=math.sqrt(disc);sample=math.ceil((along-h)/.08-1e-7)*.08
   if sample>along+h:continue
   b=.09;sigma=.03;z=sample+np.clip(rng.normal(0,sigma),-b,b);rays.append([*origin,*d,z,b,sigma])
 initial=np.r_[center+rng.normal(0,.03,2),radius+rng.normal(0,.02)]
 model,stats=fit_ranges(np.asarray(rays),initial);assert model is not None,stats
 err=float(np.linalg.norm(model[:2]-center));covered=bool(model[2]>=radius+err)
 assert err<.02 and covered,(model,center,radius,stats)
 results.append({'center_error_m':err,'true_radius_m':radius,'envelope_radius_m':float(model[2]),'test_circle_enclosed':covered,'stats':stats})
result={'status':'PASS','cases':results,'elapsed_s':time.monotonic()-started,'navigation_steps':0,'scope':'synthetic model consistency only; not continuous coverage proof or held-out navigation'}
p=Path(__file__).resolve().parents[2]/'runs/v649_static_stability/range_model_synthetic.json';p.write_text(json.dumps(result,indent=2));print(result)
