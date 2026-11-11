"""Rebuild from original causal observations; truth used only offline audit."""
import importlib.abc,json,math,sys,time,hashlib
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1037_periodic_norm_source'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from periodic_norm import PeriodicSupport,NORMALS,FACETS,old
p=R/'runs/v858_nav2_verified/v1024/dynamic_we';row=json.loads((p/'DYNAMIC_COMPLETE_PLAN.json').read_text());evidence=json.loads((p/'CAUSAL_EVIDENCE.json').read_text());constraints=evidence['periodic_constraints'];prior=row['source']['periodic'];setup=json.loads((p/'physics/SETUP.json').read_text());baseline=old.PeriodicSupport();new=PeriodicSupport();started=time.time()
assert all(r['native_tick']<=row['packet']['native_tick']for r in constraints)
for c in constraints:
 baseline.update(c['time'],c['native_tick'],c['support']);new.update(c['time'],c['native_tick'],c['support'])
assert baseline.snapshot()['vertices']==prior['vertices'],'ORIGINAL_SOURCE_REPLAY_DIFFERS'
maximum_old_plane_violation=-math.inf;maximum_new_norm_violation=-math.inf
for original,tightened in zip(baseline.polytopes,new.polytopes):
 maximum_old_plane_violation=max(maximum_old_plane_violation,float((tightened.v@original.a.T-original.b).max()));maximum_new_norm_violation=max(maximum_new_norm_violation,float((tightened.v@NORMALS.T-(.25+2e-7)).max()))
assert maximum_old_plane_violation<=1e-9 and maximum_new_norm_violation<=1e-9
# Cauchy-Schwarz gives the analytic containment statement for all legal
# coefficients. Dense disk-boundary points are an additional numerical check.
phase=np.linspace(-math.pi,math.pi,10001);boundary=np.c_[np.zeros(len(phase)),.25*np.cos(phase),.25*np.sin(phase)];max_disk=float((boundary@NORMALS.T-.25).max());assert max_disk<=1e-12
assert (np.array([0.,.25,.25])@NORMALS.T).max()>.25+.1,'OLD_SQUARE_CORNER_NOT_EXCLUDED'
# The factory's declared truth is evaluator-only; it is never loaded by the
# online PeriodicSupport implementation or used to construct any plane.
actor=setup['actor'];print('ACTOR_METADATA_KEYS',list(actor),flush=True)
anchor=np.asarray(actor['anchor_xy']);axis=np.asarray(actor['axis_xy']);theta=actor['phase_rad'];angles=np.arange(8)*math.pi/8;directions=np.c_[np.cos(angles),np.sin(angles)];amp=float(actor['amplitude_m']);truth=np.c_[directions@anchor,amp*(directions@axis)*math.cos(theta),amp*(directions@axis)*math.sin(theta)]
maximum_true_plane_violation=max(float((truth[i]@p.a.T-p.b).max())for i,p in enumerate(new.polytopes));assert maximum_true_plane_violation<=1e-9
old_max=max(float(np.hypot(p.v[:,1],p.v[:,2]).max())for p in baseline.polytopes);new_max=max(float(np.hypot(p.v[:,1],p.v[:,2]).max())for p in new.polytopes)
source=dict(row['source'],periodic=new.snapshot());record=dict(packet=row['packet'],source=source,setup={k:setup[k]for k in ['known','limits','slew_per_second']},goal=row['plan']['original_goal'],models=0,integrations=0,physical_ready=False)
(O/'SOURCE.json').write_text(json.dumps(record,indent=2)+'\n')
result=dict(passed=True,models=0,integrations=0,causal_observation_updates=len(constraints),old_source_vertices_reproduced_exactly=True,unchanged_declared_amplitude_m=.25,unchanged_declared_maximum_speed_m_s=.08,facets=FACETS,maximum_old_coefficient_radius_m=old_max,maximum_new_outer_coefficient_radius_m=new_max,maximum_new_vertex_old_plane_violation=maximum_old_plane_violation,maximum_new_vertex_norm_plane_violation=maximum_new_norm_violation,maximum_entire_disk_boundary_plane_violation=max_disk,maximum_offline_true_coefficient_plane_violation=maximum_true_plane_violation,valid_disk_containment_proof='For every unit tangent n, n dot (a,b) <= norm(a,b) <= .25. Therefore all64 halfspaces contain every originally declared sinusoidal coefficient; only originally infeasible square corners are removed.',class_was_not_narrowed=True,physical_ready=False,wall_s=time.time()-started)
(O/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
