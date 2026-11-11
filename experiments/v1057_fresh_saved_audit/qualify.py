"""No-model parser positives and duplicate/tamper negatives."""
import sys,copy,importlib.abc,json,gzip
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(R/'experiments/v1056_fresh_route_regression'))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import load,dump,O
module=load('v1057_qualified_scan_entry',C/'audit_saved.py');path=R/'runs/v858_nav2_verified/v1056/main_west_east/physics/SENSORS.json.gz'
with gzip.open(path,'rt')as f:sensors=json.load(f)
owned=module.owner_scans(sensors);assert len(owned)==len(sensors)-2;rejected=[]
for name,fixture in [('missing_binding',sensors[1:]),('late_duplicate',owned[:3]+[owned[2]]+owned[3:]),('reversed_owner_time',sensors[:4]+[sensors[3]]+sensors[4:])]:
 try:module.owner_scans(fixture)
 except AssertionError:rejected.append(name)
 else:raise AssertionError('NEGATIVE_ACCEPTED '+name)
bad=copy.deepcopy(sensors[:4]);bad[1]['ranges'][0]+=.001
try:module.owner_scans(bad)
except AssertionError:rejected.append('t0_binding_mismatch')
else:raise AssertionError('TAMPER_ACCEPTED')
result=dict(passed=True,models=0,integrations=0,exact_original_recorded_scans=len(sensors),owner_consumed_scans=len(owned),discarded_only_two_identical_factory_binding_calls=True,negative_cases=rejected,frozen_physics_and_algorithm_unchanged=True);dump(O/'SUPPLEMENTAL_ENTRY_QUALIFICATION.json',result);print(json.dumps(result))
