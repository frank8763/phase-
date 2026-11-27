"""Independent vector-orientation applicability gate; pure geometry, no optimizer."""
from pathlib import Path
import math,json,hashlib,importlib.util,os,datetime
R=Path(__file__).resolve().parents[2];S=R/'runs/v2177_priest_vector_orientation'
G=R/'experiments/v2176_sccr_common_plant_component/geometry.py';K=R/'experiments/v855_renewal_worker/KNOWN_FIELD.json'
assert os.sched_getaffinity(0)=={4}and not(S/'INITIAL_VECTOR_GATE.json').exists()
sp=importlib.util.spec_from_file_location('original_conservative_vector_geometry',G);g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
known=json.loads(K.read_text());assert len(known['known_rectangles'])==10 and len(known['known_circles'])==9
assert abs(g.REQUIRED-.24353421020226934)<1e-15

def vertices(pose,hx=.44,hy=.375):
 x,y,t=pose;c,s=math.cos(t),math.sin(t)
 return [(x+c*u-s*v,y+s*u+c*v)for u,v in [(-hx,-hy),(hx,-hy),(hx,hy),(-hx,hy)]]
def point_segment(p,a,b):
 d=[b[i]-a[i]for i in range(2)];dd=sum(x*x for x in d)
 f=max(0.,min(1.,sum((p[i]-a[i])*d[i]for i in range(2))/dd))if dd else 0.
 return math.hypot(*(p[i]-a[i]-f*d[i]for i in range(2)))
def polygon_distance(a,b):
 separation=-float('inf')
 for polygon in [a,b]:
  for p,q in zip(polygon,polygon[1:]+polygon[:1]):
   nx,ny=-(q[1]-p[1]),q[0]-p[0];norm=math.hypot(nx,ny);nx/=norm;ny/=norm
   pa=[x*nx+y*ny for x,y in a];pb=[x*nx+y*ny for x,y in b]
   separation=max(separation,min(pb)-max(pa),min(pa)-max(pb))
 if separation<=0:return separation
 return min([point_segment(p,u,v)for p in a for u,v in zip(b,b[1:]+b[:1])]+[point_segment(p,u,v)for p in b for u,v in zip(a,a[1:]+a[:1])])
def oracle(pose,field):
 verts=vertices(pose);x,y,t=pose;c,s=math.cos(t),math.sin(t)
 values=[min(a+5 for a,b in verts),min(5-a for a,b in verts),min(b+5 for a,b in verts),min(5-b for a,b in verts)]
 for rx,ry,hx,hy in field['known_rectangles']:values.append(polygon_distance(verts,vertices((rx,ry,0.),hx,hy)))
 for cx,cy,r in field['known_circles']:
  u=(cx-x)*c+(cy-y)*s;v=-(cx-x)*s+(cy-y)*c;qx=abs(u)-.44;qy=abs(v)-.375
  values.append(math.hypot(max(qx,0.),max(qy,0.))+min(max(qx,qy),0.)-r)
 return values
p=[-4.,-2.,0.];v,j,labels=g.feature(p,known);exact=oracle(p,known)
assert all(a<=b+1e-12 for a,b in zip(v,exact));assert min(v)>=g.REQUIRED and min(exact)>=g.REQUIRED
fd_error=0.;derivatives=0;conservatism_error=0.
for i in range(48):
 pose=[-4.+.02*math.sin(i),-2.+.03*math.cos(i),.013+.031*i];value,jac,_=g.feature(pose,known);e=oracle(pose,known)
 conservatism_error=max(conservatism_error,max(a-b for a,b in zip(value,e)))
 assert all(a<=b+1e-10 for a,b in zip(value,e))
 for d in range(3):
  a=pose.copy();b=pose.copy();a[d]+=1e-6;b[d]-=1e-6;up=g.feature(a,known)[0];dn=g.feature(b,known)[0]
  for n in range(len(value)):
   error=abs((up[n]-dn[n])/2e-6-jac[n][d]);fd_error=max(fd_error,error);derivatives+=1
assert fd_error<1e-6
blocked=dict(known,known_circles=known['known_circles']+[[-4.,-2.,.1]])
negative=g.feature(p,blocked)[0];assert min(negative)<g.REQUIRED
rotated=[-4.,-2.,math.pi/2];rotated_margin=min(g.feature(rotated,known)[0])-g.REQUIRED;assert rotated_margin<0
r=dict(passed=True,closed=True,scope='SHARED_VECTOR_ORIENTATION_INITIAL_REPRESENTATION_GATE_ONLY',
 initial_bodycentre_pose=p,body_halfsizes=[.44,.375],original_required_clearance_m=g.REQUIRED,
 initial_conservative_clearance_m=min(v),initial_exact_clearance_m=min(exact),initial_margin_m=min(v)-g.REQUIRED,initial_limiting_feature=labels[v.index(min(v))],
 fixed_90deg_margin_m=rotated_margin,occupied_negative_min_clearance_m=min(negative),
 analytic_FD_cases=derivatives,maximum_FD_error=fd_error,conservative_lower_bound_max_excess_m=conservatism_error,
 old_raster_and_fourdisc_infeasibility_NOT_rerun_or_overwritten=True,no_old_grid_buffer_threshold_changed=True,
 new_shared_vector_representation_must_be_available_to_all_ten_methods=True,
 whole_trajectory_optimizer_native_PRIEST_vehicle_or_navigation_qualified=False,
 solver_model_NN_render_Predictor_Allocator_physics_replay_audit_source_formal_calls=0,
 created_at=datetime.datetime.now().astimezone().isoformat(),source_SHA256={str(z.relative_to(R)):hashlib.sha256(z.read_bytes()).hexdigest()for z in [G,K,Path(__file__)]})
raw=json.dumps(r,indent=2,allow_nan=False)+'\n';assert len(raw.encode())<65536;(S/'INITIAL_VECTOR_GATE.json').write_text(raw)
print(json.dumps(r))
