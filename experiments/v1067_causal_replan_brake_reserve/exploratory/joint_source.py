"""Common 2-D sinusoidal coefficients, retaining every old causal constraint.

Eight independent projected polytopes describe ONE shared six-coefficient
trajectory. A verified nonnegative LP dual supplies each extra outer plane.
No actor anchor, actual phase, axis, or future observation is accepted here.
"""
import copy,itertools,math,sys,time,warnings
from pathlib import Path
import numpy as np
from kernel import R,O,load
sys.path.insert(0,str(O/'dependencies'))
from scipy.spatial import ConvexHull,HalfspaceIntersection
from scipy.optimize import linprog
original=load('v1067_original_polytope',R/'experiments/v1029_declared_course_source/fast_periodic.py')
BOX=np.array([8.,8.,.25,.25,.25,.25])
EPS=2e-7

def constraints(prior):
 matrices=[];bounds=[];faces=[];projections=[]
 for i,vertices in enumerate(prior['vertices']):
  v=np.asarray(vertices,float);equations=ConvexHull(v).equations;normal=np.unique(np.round(equations[:,:3],9),axis=0);b=(v@normal.T).max(axis=0)+2e-8;faces.append((normal,b));n=np.array([math.cos(i*math.pi/8),math.sin(i*math.pi/8)]);p=np.zeros((3,6));p[0,:2]=n;p[1,2:4]=n;p[2,4:]=n;projections.append(p);matrices.append(normal@p);bounds.extend(b)
 matrices.extend([np.eye(6),-np.eye(6)]);bounds.extend(BOX);bounds.extend(BOX);A=np.vstack(matrices);b=np.array(bounds)
 assert A.shape==(len(b),6)and np.isfinite(A).all()and np.isfinite(b).all()
 return A,b,faces,projections

def upper(A,b,q):
 with warnings.catch_warnings():
  warnings.filterwarnings('ignore',message='Unrecognized options detected')
  result=linprog(-q,A_ub=A,b_ub=b,bounds=[(None,None)]*6,method='highs',options=dict(time_limit=3.,dual_feasibility_tolerance=1e-9,primal_feasibility_tolerance=1e-9,threads=1,parallel=False))
 assert result.success,('JOINT_SOURCE_LP_FAILED',result.status)
 multipliers=np.maximum(0.,-np.asarray(result.ineqlin.marginals));residual=q-A.T@multipliers;roundoff=1e-10*(1+float(abs(b*multipliers).sum())+float(abs(A).T@multipliers@BOX));bound=float(b@multipliers+abs(residual)@BOX+roundoff+EPS)
 assert bound>=float(q@result.x)-1e-8,'DUAL_BOUND_BELOW_PRIMAL'
 return bound,dict(nonnegative_dual=multipliers.tolist(),residual=residual.tolist(),residual_box=BOX.tolist(),outward_roundoff_m=roundoff+EPS,upper=bound)

def tighten(source,phase_planes=0):
 begun=time.monotonic();prior=source['periodic'];A,b,faces,projections=constraints(prior);result=copy.deepcopy(source);allplanes=[];vertices=[];old_width=[];new_width=[]
 normals=[*np.eye(3),*-np.eye(3)]
 for t in np.arange(phase_planes)*2*math.pi/max(1,phase_planes):
  n=np.array([1.,math.sin(t),math.cos(t)]);normals.extend([n,-n])
 for i,(v,(normal,bounds),projection)in enumerate(zip(prior['vertices'],faces,projections)):
  rows=[];new_a=[*normal];new_b=[*bounds]
  for n in normals:
   bound,certificate=upper(A,b,n@projection);new_a.append(n);new_b.append(bound);rows.append(dict(normal=np.array(n).tolist(),**certificate))
  new_a=np.asarray(new_a);new_b=np.asarray(new_b);center=linprog([0.,0.,0.,-1.],A_ub=np.c_[new_a,np.linalg.norm(new_a,axis=1)],b_ub=new_b,bounds=[(None,None)]*3+[(0.,None)],method='highs',options=dict(time_limit=3.));assert center.success and center.x[3]>1e-10,'JOINT_PROJECTION_NO_STRICT_INTERIOR'
  points=HalfspaceIntersection(np.c_[new_a,-new_b],center.x[:3]).intersections;assert len(points)<5000,'BOUNDED_JOINT_PROJECTION_VERTEX_LIMIT'
  points=(points[:,None,:]+np.asarray(list(itertools.product([-EPS,EPS],repeat=3)))[None,:,:]).reshape(-1,3);points=points[ConvexHull(points).vertices]
  vertices.append(points.tolist());allplanes.append(rows);old_width.append(np.ptp(np.asarray(v),axis=0).tolist());new_width.append(np.ptp(points,axis=0).tolist())
 result['periodic']['vertices']=vertices;result['periodic']['common_2d_coefficients']=True;result['periodic']['joint_projection_outer_guard']=EPS
 proof=dict(passed=True,scope='OUTER_PROJECTION_OF_THE_SAME_CAUSAL_SHARED_6D_COEFFICIENT_CLASS',A=A.tolist(),b=b.tolist(),planes=allplanes,old_coefficient_widths=old_width,new_coefficient_widths=new_width,phase_planes=phase_planes,wall_s=time.monotonic()-begun,models=0,integrations=0,no_privileged_actor_inputs=True)
 return result,proof
