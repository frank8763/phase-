"""Fixed finite geometry/Jacobian checks; never calls an optimizer."""
from pathlib import Path
import os,json,math,hashlib,datetime
import numpy as np
from collocation import Projection,arc,VMAX,AMAX,KMAX,geometry
R=Path(__file__).resolve().parents[2];S=R/'runs/v2177_priest_vector_orientation';assert os.sched_getaffinity(0)=={4}and not(S/'COLLOCATION_SOFTWARE_GATE.json').exists()
known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text());problem=Projection(known);r=problem.evaluate(problem.initial);lo,hi=problem.bounds()
assert abs(r['equalities']).max()<1e-12 and r['minimum_sampled_clearance']>=geometry.REQUIRED and r['inequalities'].min()>-1e-12
assert((problem.initial>=lo)&(problem.initial<=hi)).all()and max(r['speeds'])<=VMAX+1e-15 and abs(np.diff(r['speeds'])/problem.h).max()<=AMAX+1e-15
assert abs(r['curvatures']).max()==0 and r['speeds'][0]==r['speeds'][1]==r['speeds'][-1]==r['speeds'][-2]==0
# Forty preregistered exact-arc Jacobian cases, including straight/rest/reverse.
arc_error=0.;arc_derivatives=0
for i in range(40):
 pose=np.array([.03*i,-.07*i,.013*i]);v0=0. if i%4==0 else .08*math.sin(i);v1=0. if i%5==0 else .08*math.cos(i);k=0. if i%3==0 else .6*math.sin(.7*i);h=.5
 value,jp,j0,j1,jk=arc(pose,v0,v1,k,h);analytic=np.column_stack([jp,j0,j1,jk]);q=np.r_[pose,v0,v1,k]
 for j in range(6):
  a=q.copy();b=q.copy();a[j]+=1e-6;b[j]-=1e-6;up=arc(a[:3],a[3],a[4],a[5],h)[0];dn=arc(b[:3],b[3],b[4],b[5],h)[0];arc_error=max(arc_error,float(abs((up-dn)/2e-6-analytic[:,j]).max()));arc_derivatives+=3
assert arc_error<1e-7
# One fixed off-kink perturbation; it is NOT an optimization/feasibility search.
z=problem.initial+1e-4*np.sin(.9*np.arange(len(problem.initial))+.17);base=problem.evaluate(z);h=1e-7;eqerror=0.;ineqerror=0.;objective_error=0.;checks=0
for j in range(len(z)):
 a=z.copy();b=z.copy();a[j]+=h;b[j]-=h;up=problem.evaluate(a);dn=problem.evaluate(b)
 eqerror=max(eqerror,float(abs((up['equalities']-dn['equalities'])/(2*h)-base['equality_jacobian'][:,j]).max()))
 ineqerror=max(ineqerror,float(abs((up['inequalities']-dn['inequalities'])/(2*h)-base['inequality_jacobian'][:,j]).max()))
 objective_error=max(objective_error,abs((problem.objective(a)[0]-problem.objective(b)[0])/(2*h)-problem.objective(z)[1][j]));checks+=len(base['equalities'])+len(base['inequalities'])
assert eqerror<1e-6 and ineqerror<1e-5 and objective_error<1e-6,(eqerror,ineqerror,objective_error)
blocked=dict(known,known_circles=known['known_circles']+[[-4.,-2.,.1]]);negative=Projection(blocked).evaluate(problem.initial);assert negative['minimum_sampled_clearance']<geometry.REQUIRED and negative['inequalities'].min()<0
result=dict(passed=True,closed=True,scope='DIRECT_ORIENTATION_ARC_COLLOCATION_EQUATIONS_SOFTWARE_ONLY',intervals=problem.N,horizon_s=problem.H,free_variables=len(z),equalities=len(base['equalities']),sampled_inequalities=len(base['inequalities']),geometry_pose_samples=2*problem.N+1,
 positive_initializer_distance_m=float(r['poses'][-1,0]-r['poses'][0,0]),positive_initializer_max_equality_error=float(abs(r['equalities']).max()),positive_initializer_min_inequality=float(r['inequalities'].min()),positive_initializer_min_clearance_m=r['minimum_sampled_clearance'],required_clearance_m=geometry.REQUIRED,
 speed_bound_continuous_from_linear_nodes=True,max_speed=float(max(r['speeds'])),max_piecewise_acceleration=float(abs(np.diff(r['speeds'])/problem.h).max()),max_abs_curvature=float(abs(r['curvatures']).max()),start_end_speed_and_acceleration_zero=True,
 arc_derivative_entries_checked=arc_derivatives,maximum_arc_Jacobian_error=arc_error,full_free_variable_FD_entries=checks,maximum_equality_Jacobian_error=eqerror,maximum_inequality_Jacobian_error=ineqerror,maximum_objective_gradient_error=objective_error,
 occupied_negative_clearance_m=negative['minimum_sampled_clearance'],occupied_negative_refused=True,
 exact_arc_is_ideal_geometry_not_original_physics=True,sampled_geometry_is_not_continuous_or_physical_safety_certificate=True,
 Bernstein_XY_is_reference_only_not_byte_identical_native_PRIEST=True,optimizer_NLP_model_Predictor_Allocator_NN_render_physics_replay_audit_Source_formal_calls=0,
 created_at=datetime.datetime.now().astimezone().isoformat(),source_SHA256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),Path(__file__).parent/'collocation.py',R/'experiments/v2176_sccr_common_plant_component/geometry.py',R/'experiments/v855_renewal_worker/KNOWN_FIELD.json']})
raw=json.dumps(result,indent=2,allow_nan=False)+'\n';assert len(raw.encode())<98304;(S/'COLLOCATION_SOFTWARE_GATE.json').write_text(raw);print(json.dumps(result))
