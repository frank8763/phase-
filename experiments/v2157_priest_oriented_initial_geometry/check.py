"""Fixed exact rectangle initial witness, no optimizer or physical recomputation."""
from pathlib import Path
import json,hashlib,math,os
R=Path(__file__).resolve().parents[2];S=R/'runs/v2157_priest_oriented_initial_geometry';assert os.sched_getaffinity(0)=={1}and not(S/'RESULT.json').exists()
a=R/'runs/v2122_priest_quiescent_handoff/vehicle/actual';p=a/'PRIEST_OPTIMIZER_REQUEST.json';o=a/'cycle_000000_origin.json';x=json.loads(p.read_text());body=json.loads(o.read_text())['receipt']['packet']['body'];points=x['static_points_world'];required=.24353421020226934;grid=.05/math.sqrt(2);rear=[body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]]
def rectangle(point,pose):
 x,y,t=pose;c,s=math.cos(t),math.sin(t);dx,dy=point[0]-x,point[1]-y;u=c*dx+s*dy;v=-s*dx+c*dy;local=[u-.3,v];q=[abs(local[0])-.44,abs(local[1])-.375];z=[max(t,0.)for t in q]
 if max(q)<=0:
  j=0 if q[0]>=q[1]else 1;g=[0.,0.];g[j]=1. if local[j]>=0 else-1.;d=q[j]
 else:
  d=math.hypot(*z);g=[z[i]/d*(1. if local[i]>=0 else-1.)for i in range(2)]
 gradient=[-c*g[0]+s*g[1],-s*g[0]-c*g[1],g[0]*v-g[1]*u]
 return d-required-grid,gradient
margins=[rectangle(z,rear)[0]for z in points];maxfd=0.;tests=0
for i in range(80):
 pose=[rear[0]+.01*math.sin(i),rear[1]+.01*math.cos(i),.01+i*.017];point=[pose[0]+1.3*math.cos(i*.11),pose[1]+1.3*math.sin(i*.11)];value,g=rectangle(point,pose)
 for j in range(3):
  h=1e-6;plus=pose.copy();minus=pose.copy();plus[j]+=h;minus[j]-=h;fd=(rectangle(point,plus)[0]-rectangle(point,minus)[0])/(2*h);maxfd=max(maxfd,abs(fd-g[j]));tests+=1
assert maxfd<1e-7
negative=rectangle([body[0],body[1]],rear)[0];assert negative<0
v=dict(passed=True,closed=True,scope='EXACT_ORIENTED_RECTANGLE_NECESSARY_INITIAL_WITNESS_ONLY',fixed_initial_pose=rear,body_half_extents=[.44,.375],rear_to_body_center=.3,original_required_clearance_m=required,original_grid_uncertainty_m=grid,points=len(points),initial_violations=sum(z<0 for z in margins),minimum_initial_margin_m=min(margins),initial_geometry_feasible=all(z>=0 for z in margins),independent_FD_gradient_cases=tests,maximum_FD_error=maxfd,occupied_negative_margin_m=negative,original_singleellipse_and_fourdisc_failures_retained=True,author_PRIEST_future_orientation_coupling_qualified=False,optimizer_calls=0,models=0,physics=0,replay=0,formal_tasks=0,input_SHA256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest(),str(o.relative_to(R)):hashlib.sha256(o.read_bytes()).hexdigest()},helper_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
raw=json.dumps(v,indent=2).encode()+b'\n';assert len(raw)<65536;(S/'RESULT.json').write_bytes(raw);print(json.dumps(v))
