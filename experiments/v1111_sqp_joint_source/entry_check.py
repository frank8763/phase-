"""Explicit constraint API and the real retained violating source, zero physics."""
import sys,json,ast,hashlib
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1111_sqp_joint_source'
sys.path.insert(0,str(C));import run as driver
import numpy as np
sys.path.insert(0,str(R/'runs/v1111_solver_dependencies/site'))
import scipy
from scipy.optimize import minimize
from solver import Solver
def main():
 for p in C.glob('*.py'):ast.parse(p.read_text())
 assert scipy.__version__=='1.15.3'
 test=minimize(lambda z:(z[0]+1)**2,[0.],jac=lambda z:np.array([2*(z[0]+1)]),method='SLSQP',bounds=[(-2.,2.)],constraints=[dict(type='ineq',fun=lambda z:np.array([z[0]-1]),jac=lambda z:np.ones((1,1)))],options=dict(ftol=1e-10,maxiter=30))
 assert test.success and abs(test.x[0]-1)<1e-7,'EXPLICIT_INEQUALITY_NOT_ENFORCED'
 opposite=minimize(lambda z:(z[0]-1)**2,[0.],jac=lambda z:np.array([2*(z[0]-1)]),method='SLSQP',bounds=[(-2.,2.)],constraints=[dict(type='ineq',fun=lambda z:np.array([-1-z[0]]),jac=lambda z:-np.ones((1,1)))],options=dict(ftol=1e-10,maxiter=30))
 assert opposite.success and abs(opposite.x[0]+1)<1e-7,'INEQUALITY_SIGN_WRONG'
 x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());pg=json.loads((R/'runs/v1107_reference_frame_alignment/PATH_GEARS.json').read_text());engine=Solver(x,np.array(pg['path']),pg['gear']);z=engine.seed();value,signed,report=engine.evaluate(z)
 with np.load(R/'runs/v1110_constrained_joint_source/CONTROLLER_SOURCE.npz')as previous:old_s=previous['states'].copy();old_u=previous['controls'].copy()
 accelerated,controls,rows,events=engine.simulate(z);error=max(float(abs(accelerated-old_s).max()),float(abs(controls-old_u).max()));assert error<=1e-8
 assert len(signed)==2052 and np.isfinite(signed).all()and signed.min()<0 and not report['restoration_targets_met'],'REAL_UNSAFE_SOURCE_ACCEPTED'
 assert (signed[:1024]<0).any()and(signed[1024:2048]<0).any()and(signed[2048:]<0).any(),'REAL_FAILED_CLASS_NOT_EXPLICIT'
 calls=engine.calls;again=engine.evaluate(z);assert engine.calls==calls and np.array_equal(signed,again[1]),'CACHED_CONSTRAINT_BINDING_BROKEN'
 # Verify a real finite-difference objective/constraint column uses bounded
 # steering and the same continuous origin/model, not an optimizer stub.
 z1=z.copy();z1[0]+=min(.001,engine.upper[0]-z1[0]);f1,g1,_=engine.evaluate(z1);assert g1.shape==signed.shape and np.isfinite((g1-signed)/max(z1[0]-z[0],1e-12)).all()
 refused=[]
 for name in ['mujoco','physical','vehicle','factory','torch','rclpy']:
  try:__import__(name)
  except AssertionError:refused.append(name)
 assert len(refused)==6
 deps=R/'runs/v1111_solver_dependencies/site';files={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(deps.rglob('*'))if p.is_file()and not p.is_symlink()and '__pycache__'not in p.parts}
 (R/'runs/v1111_solver_dependencies/FILES_SHA256.json').write_text(json.dumps(files,indent=2)+'\n')
 q=dict(passed=True,solver='SciPy SLSQP',version=scipy.__version__,explicit_inequality_positive_negative_cases=2,real_inequality_count=len(signed),real_source_violations_recognized=True,cpp_saved_python_error=error,evaluation_cache_binding_passed=True,dependency_files=len(files),dependency_bytes=sum((R/n).stat().st_size for n in files),source_constraints=report,imports_refused=refused,unchanged_geometry_envelope_audit_reused='runs/v1110_constrained_joint_source/ENTRY_QUALIFICATION.json',analytical_work=dict(cpp_native=engine.native,python_native=0),models=0,physical_integrations=0)
 (O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q))
if __name__=='__main__':main()
