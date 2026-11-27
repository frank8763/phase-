"""CPU4 full-body lower-bound and derivative checks, no optimizer/model."""
import math,os,random,time,traceback
from common import R,C,S,read,put,sha
import geometry,oracle

def main():
 from common import deny_models
 deny_models()
 assert os.sched_getaffinity(0)=={4};start=time.monotonic();result=dict(passed=False,models=0,solvers=0,physics=0,replay=0)
 try:
  known=read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json');rng=random.Random(2123);lower_max=-1e99;grad_max=0.;checks=0;poses=512
  for i in range(poses):
   p=[rng.uniform(-5.4,5.4),rng.uniform(-5.4,5.4),rng.uniform(-math.pi,math.pi)];values,jacs,labels=geometry.feature(p,known);exact=oracle.distances(p,known)
   lower_max=max(lower_max,max(a-b for a,b in zip(values,exact)));assert lower_max<=2e-12,'NONCONSERVATIVE_BODY_DISTANCE'
   for k in range(3):
    a=p[:];b=p[:];a[k]+=1e-6;b[k]-=1e-6;va=geometry.feature(a,known)[0];vb=geometry.feature(b,known)[0]
    for aa,bb,g in zip(va,vb,jacs):grad_max=max(grad_max,abs((aa-bb)/2e-6-g[k]));checks+=1
  from filter import values_jac
  chain_max=0.;chain_count=0
  for gear in[-1,1]:
   for kind in['PSF','PCBF']:
    z=[.061,.23]*8;case=dict(pose=[-3.9,-1.7,.431],gear=gear);vv,jj,ll=values_jac(z,case,known,kind)
    for k in range(16):
     a=z[:];b=z[:];a[k]+=1e-6;b[k]-=1e-6;va=values_jac(a,case,known,kind)[0];vb=values_jac(b,case,known,kind)[0]
     for aa,bb,j in zip(va,vb,jj):chain_max=max(chain_max,abs((aa-bb)/2e-6-j[k]));chain_count+=1
  assert chain_max<2e-7
  result.update(composite_constraint_derivative_checks=chain_count,maximum_composite_derivative_error=chain_max)
  assert grad_max<2e-7
  assert geometry.REQUIRED==.24353421020226934
  # A full-period support bound must dominate all sampled instants, including signed vertices.
  snap=dict(omega=.32,amplitude=.25,vertices=[[[.3,.1,-.2],[-.4,-.2,.1]]for _ in range(8)])
  whole=geometry.support_at(snap,0.,True);minimum=1e99
  for k in range(1000):
   at=geometry.support_at(snap,k*2*math.pi/.32/999);minimum=min(minimum,min(a-b for a,b in zip(whole,at)))
  assert minimum>=-1e-12
  result.update(passed=True,independent_polygon_poses=poses,per_obstacle_derivative_checks=checks,maximum_lower_bound_minus_exact_m=lower_max,maximum_analytic_derivative_error=grad_max,whole_cycle_support_instants=1000,minimum_whole_minus_instant_m=minimum,required_raw_m=geometry.REQUIRED)
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc())
 result.update(closed=True,wall_s=time.monotonic()-start);put(S/'GEOMETRY_SOFTWARE_RESULT.json',result);print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
