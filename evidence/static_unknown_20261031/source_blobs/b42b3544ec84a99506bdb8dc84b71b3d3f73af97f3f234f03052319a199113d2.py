"""Independent polygon-distance reference for the rectangular footprint geometry."""
import json,math
from types import SimpleNamespace
from pathlib import Path
import numpy as np
from exact_footprint import pose_values
rng=np.random.default_rng(64816)
def corners(center,half,yaw):
 c,s=math.cos(yaw),math.sin(yaw);return np.array([[-1,-1],[-1,1],[1,1],[1,-1]])*half@np.array([[c,s],[-s,c]])+center
def point_segment(p,a,b):
 d=b-a;t=np.clip(np.dot(p-a,d)/np.dot(d,d),0,1);return np.linalg.norm(p-(a+t*d))
def polygon_distance(a,b):
 for polygon in [a,b]:
  for u,v in zip(polygon,np.roll(polygon,-1,axis=0)):
   edge=v-u;axis=np.array([-edge[1],edge[0]]);pa=a@axis;pb=b@axis
   if pa.max()<pb.min()or pb.max()<pa.min():break
  else:continue
  break
 else:return 0.
 return min(point_segment(p,u,v)for p,q in [(p,b)for p in a]+[(p,a)for p in b]for u,v in zip(q,np.roll(q,-1,axis=0)))
field=SimpleNamespace(half=np.array([.43,.395]),center_local=np.zeros(2),config=SimpleNamespace(lower=-100,upper=100),circles=[],sensor_points=[],sensor_extra=.08)
errors=[];positive=0
for _ in range(3000):
 pose=np.r_[rng.uniform(-2,2,2),rng.uniform(-np.pi,np.pi)];r=np.r_[rng.uniform(-2,2,2),rng.uniform(.05,1.,2)];field.rectangles=r[None,:]
 actual=float(pose_values(field,[pose])[0]);expected=polygon_distance(corners(pose[:2],field.half,pose[2]),corners(r[:2],r[2:],0))
 if expected>1e-8:errors.append(abs(actual-expected));positive+=1
 else:assert actual<=1e-8
assert max(errors)<1e-10
result={'status':'PASS','random_cases':3000,'separated_cases':positive,'maximum_distance_error_m':max(errors),'reference':'independent scalar point-to-segment polygon distance plus edge projection overlap','physics_steps':0}
p=Path(__file__).resolve().parents[2]/'runs/v648_static_unknown/exact_footprint_check.json';p.write_text(json.dumps(result,indent=2));print(json.dumps(result))
