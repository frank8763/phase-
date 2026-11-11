"""Four-way saved-causal comparison; no physical models or new observations."""
import importlib.abc,importlib.util,json,math,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1040_approach_information_audit';P=R/'runs/v858_nav2_verified/v1039/approach'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
norm=load('v1040_public_norm_prior',R/'experiments/v1037_periodic_norm_source/periodic_norm.py');gm=load('v1040_existing_geometry',R/'experiments/v1023_dense_input_route/geometry_model.py');ref=gm.ref

def areas(prior):
 bounds=norm.old.original.bounds_from_vertices(prior['vertices'],np.arange(200)*2*math.pi/.32/200);values=[]
 for b in bounds:
  poly=ref._old.polygon(b);values.append(float(abs(poly[:,0]@np.roll(poly[:,1],1)-poly[:,1]@np.roll(poly[:,0],1))/2))
 p=ref._old.polygon(ref._old.cycle_upper(prior)+1e-6);cycle=float(abs(p[:,0]@np.roll(p[:,1],1)-p[:,1]@np.roll(p[:,0],1))/2)
 return dict(mean_phase_center_area_m2=float(np.mean(values)),minimum_phase_center_area_m2=float(np.min(values)),maximum_phase_center_area_m2=float(np.max(values)),full_cycle_center_area_m2=cycle)

def main():
 done=json.loads((R/'runs/v1039_causal_approach/COMPLETION.json').read_text());assert done['closed']and done['passed']and done['audit']['passed'],'NO_VERIFIED_ACTUAL_NEW_OBSERVATIONS'
 row=json.loads((P/'FINAL_CAUSAL_SOURCE.json').read_text());e=json.loads((P/'CAUSAL_EVIDENCE.json').read_text());old=json.loads((P/'APPROACH_INITIAL.json').read_text());baseline=norm.old.PeriodicSupport();tightened=norm.PeriodicSupport()
 for c in e['periodic_constraints']:
  assert c['native_tick']<=row['packet']['native_tick'];baseline.update(c['time'],c['native_tick'],c['support']);tightened.update(c['time'],c['native_tick'],c['support'])
 assert baseline.snapshot()['vertices']==row['source']['periodic']['vertices'],'NEW_OBSERVATION_BASELINE_REBUILD_CHANGED'
 priors=dict(before_box=old['source']['periodic'],after_box=baseline.snapshot(),before_norm=json.loads((R/'runs/v1037_periodic_norm_source/SOURCE.json').read_text())['source']['periodic'],after_norm=tightened.snapshot());metrics={k:areas(v)for k,v in priors.items()}
 phases=np.arange(1000)*2*math.pi/.32/1000;bb=norm.old.original.bounds_from_vertices(priors['before_box']['vertices'],phases);ab=norm.old.original.bounds_from_vertices(priors['after_box']['vertices'],phases);an=norm.old.original.bounds_from_vertices(priors['after_norm']['vertices'],phases);assert (ab-bb).max()<=1e-8 and(an-ab).max()<=1e-8
 actor=json.loads((P/'physics/SETUP.json').read_text())['actor'];angles=np.arange(8)*math.pi/8;directions=np.c_[np.cos(angles),np.sin(angles)];axis=np.asarray(actor['axis_xy']);theta=actor['phase_rad'];true=np.c_[directions@np.asarray(actor['anchor_xy']),.25*(directions@axis)*math.cos(theta),.25*(directions@axis)*math.sin(theta)];violation=max(float((true[i]@p.a.T-p.b).max())for i,p in enumerate(tightened.polytopes));assert violation<=1e-8
 rebuilt=dict(row,source=dict(row['source'],periodic=tightened.snapshot()),models=0,integrations=0,physical_ready=False);(O/'REBUILT_SOURCE.json').write_text(json.dumps(rebuilt,indent=2)+'\n')
 result=dict(passed=True,metrics=metrics,causal_observation_updates_before=89,causal_observation_updates_after=len(e['periodic_constraints']),maximum_added_data_support_expansion=float((ab-bb).max()),maximum_norm_support_expansion=float((an-ab).max()),maximum_offline_true_coefficient_violation=violation,actual_new_component_native=done['result']['new_component_native'],new_information_only_reduction_percent=100*(1-metrics['after_box']['mean_phase_center_area_m2']/metrics['before_box']['mean_phase_center_area_m2']),combined_reduction_percent=100*(1-metrics['after_norm']['mean_phase_center_area_m2']/metrics['before_box']['mean_phase_center_area_m2']),models=0,integrations=0,full_dynamic_arrival=False)
 (O/'INFORMATION_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
