"""Restoration constraints must expose the real retained whole-source failure."""
import sys,json,ast,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1110_constrained_joint_source'
sys.path.insert(0,str(C));import run as driver
import numpy as np
from solver import Solver
def main():
 for p in C.glob('*.py'):ast.parse(p.read_text())
 x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());pg=json.loads((R/'runs/v1107_reference_frame_alignment/PATH_GEARS.json').read_text());engine=Solver(x,np.array(pg['path']),pg['gear']);z=engine.seed();cpp_s,cpp_u,rows,events=engine.simulate(z)
 with np.load(R/'runs/v1109_joint_cusp_source/CONTROLLER_SOURCE.npz')as old:
  error=max(float(abs(cpp_s-old['states']).max()),float(abs(cpp_u-old['controls']).max()));ss=old['states'].copy()
 assert error<=1e-8,'CACHED_KERNEL_OR_PRIOR_SOURCE_CHANGED'
 t=time.monotonic();violation,report=engine.constraint_terms(ss,events);seconds=time.monotonic()-t
 original=json.loads((R/'runs/v1109_joint_cusp_source/COMPLETION.json').read_text())['complete_review']
 assert not report['restoration_targets_met'] and report['minimum_certified_raw_lower_m']<driver.kernel.REQUIRED and report['maximum_certified_cross_upper_m']>.04 and max(report['endpoint_errors_m'])>.02,'REAL_FAILED_GATES_MISSED'
 assert report['minimum_certified_raw_lower_m']<=original['minimum_full_cycle_raw_m']+1e-12,'GEOMETRY_ENVELOPE_UNSAFE_OVERSTATEMENT'
 assert report['maximum_certified_cross_upper_m']>=original['maximum_predicted_cross_track_m']-1e-12,'CROSS_TRACK_ENVELOPE_UNSAFE_UNDERSTATEMENT'
 # Every original native pose, not only representative poses, is enclosed.
 checks=0
 for section,((q,arc,d),(begin,moving,end))in enumerate(zip(engine.sections,events)):
  start=begin-300 if section else begin;s=ss[start:end+1,:3];n=len(s);bins=256;mapping=np.minimum(np.arange(n)*bins//n,bins-1);indices=np.minimum(((np.arange(bins)+.5)*n/bins).astype(int),n-1);samples=s[indices]
  dist=np.linalg.norm(s[:,:2]-samples[mapping,:2],axis=1);angle=np.abs(np.arctan2(np.sin(s[:,2]-samples[mapping,2]),np.cos(s[:,2]-samples[mapping,2])));envelope=np.zeros(bins);np.maximum.at(envelope,mapping,dist+np.hypot(.44,.375)*angle)
  a,b=engine.geometry.clearances(samples);actual_a,actual_b=engine.geometry.clearances(s);actual=np.minimum(actual_a,actual_b);assert np.all(np.minimum(a,b)[mapping]-envelope[mapping]<=actual+1e-10),'NATIVE_GEOMETRY_ENVELOPE_MISS';checks+=len(s)
 # Positive and negative analytic envelope patterns independent of fitting.
 point=np.tile(ss[0],(101,1));a,b=engine.geometry.clearances(point[:,:3]);assert np.minimum(a,b).min()>=driver.kernel.REQUIRED
 endpoints=report['endpoint_errors_m'];assert abs(endpoints[2]-.02023339423735885)<1e-10
 f=engine.residual(z);assert np.isfinite(f).all() and len(f)>1000,'RESTORATION_RESIDUAL_INVALID'
 refused=[]
 for name in ['mujoco','physical','vehicle','factory','torch','rclpy']:
  try:__import__(name)
  except AssertionError:refused.append(name)
 assert len(refused)==6
 qualification=dict(passed=True,real_failed_gates_reproduced=['clearance','cross_track','gear_endpoints'],full_source_cpp_to_saved_python_error=error,envelope_native_pose_checks=checks,lower_clearance_is_conservative=True,upper_cross_is_conservative=True,prior_source_constraints=report,constraint_seconds=seconds,source_kernel_and_mode_qualification_reused='runs/v1109_joint_cusp_source/ENTRY_QUALIFICATION.json',imports_refused=refused,analytical_work=dict(cpp_native=engine.native,python_native=0,readonly_geometry_queries=checks+3*1024+101),models=0,physical_integrations=0)
 (O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(qualification,indent=2)+'\n');print(json.dumps(qualification))
if __name__=='__main__':main()
