"""Synthetic measurement test; truth is used only to create/evaluate test data."""
import json,math
from pathlib import Path
import numpy as np
from circle_memory import CircleMemory
rng=np.random.default_rng(64817);model=CircleMemory();truth=np.array([.4,-.2]);radius=.25;est=None
for step,angle in enumerate(np.linspace(-1.,1.,50)):
 origin=truth+1.7*np.array([math.sin(angle),math.cos(angle)]);bearing=math.atan2(*(truth-origin)[::-1]);hits=[]
 for offset in np.linspace(-.17,.17,17):
  direction=np.array([math.cos(bearing+offset),math.sin(bearing+offset)]);d=origin-truth;b=d@direction;disc=b*b-d@d+radius*radius
  if disc<=0:continue
  distance=-b-math.sqrt(disc);measured=np.ceil(distance/.08)*.08+np.clip(rng.normal(0,.03),-.09,.09);hits.append(origin+measured*direction)
 est,stats=model.update(hits,[],[],step,origin)
assert est is not None,stats
error=float(np.linalg.norm(est[:2]-truth));assert error<.06
result={'status':'PASS','center_error_m':error,'fitted_envelope_radius_m':float(est[2]),'true_radius_m':radius,'covers_test_circle':bool(est[2]>=radius+error),'scope':'one synthetic bounded-noise sensor case, not calibration or navigation validation','physics_steps':0}
p=Path(__file__).resolve().parents[2]/'runs/v648_static_unknown/circle_memory_check.json';p.write_text(json.dumps(result,indent=2));print(json.dumps(result))
