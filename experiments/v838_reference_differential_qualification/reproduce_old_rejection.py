"""Fast independent actual saved original-forward-tail rejection seam; no models."""
import argparse,importlib.abc,importlib.util
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('ZERO_MODEL_REPRODUCTION')
import sys
sys.meta_path.insert(0,NoModels())
from helpers import *
from independent_norm import static_field,radial_lower
from exact_footprint import pose_values
ap=argparse.ArgumentParser();ap.add_argument('--require-certified',action='store_true');args=ap.parse_args()
protocol=read(pair/'STATIC_PROTOCOL.json');base=static_field(protocol);spec=importlib.util.spec_from_file_location('old_broad',repo/'experiments/v812_soft_global_reference/motion_tracker.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);rows=[]
for entry in read(own/'FIXED_INPUTS.json'):
 field=SimpleNamespace(**base.__dict__);old.install_time_gate(field,entry['state'],'predictive',protocol['known_circles'],protocol['known_rectangles']);minimums=[]
 for a in entry['old_attempts']:
  for c in a['detail']['candidates']:
   if c['kind']!='FORWARD_BRAKE':continue
   z=np.load(cell/c['early_rejection_witness_file']);p=z['poses'];clock=np.arange(1,329)*.01;v=np.maximum(field.causal_values_at_times(p,clock),np.minimum(pose_values(base,p),radial_lower(base,p,entry['state'],clock)));tick=c['early_rejection_witness_native_tick'];assert abs(v[tick-1]-c['early_rejection_witness_value_m'])<=1e-8
   minimums.append(float(v.min()))
 assert minimums and max(minimums)<.155;rows.append(dict(step=entry['step'],original_forward_tails=len(minimums),best_complete328_minimum_m=max(minimums),required_m=.155))
print(json.dumps(dict(status='SAVED_ORIGINAL_FORWARD_LIBRARY_STILL_REJECTED',records=rows,models=0,integrations=0)),flush=True)
if args.require_certified:assert all(x['best_complete328_minimum_m']>=.155 for x in rows),'NO_ORIGINAL_FORWARD_TAIL_HAS_COMPLETE328_CERTIFICATE'
