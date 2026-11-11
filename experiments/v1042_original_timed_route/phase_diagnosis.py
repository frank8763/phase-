"""200 instantaneous causal outer-set cuts; descriptive, not reachability proof."""
import importlib.abc,importlib.util,json,math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v1042_original_timed_route'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1023_dense_input_route'))
from geometry_model import ref,REQUIRED
s=importlib.util.spec_from_file_location('v1042_cut',R/'experiments/v1033_saved_task_diagnosis/contract_gate.py');gate=importlib.util.module_from_spec(s);s.loader.exec_module(gate)
s=importlib.util.spec_from_file_location('v1042_interval',R/'experiments/v1035_signed_timed_input_source/time_geometry.py');interval=importlib.util.module_from_spec(s);s.loader.exec_module(interval)
x=json.loads((R/'runs/v1040_approach_information_audit/REBUILT_SOURCE.json').read_text());period=2*math.pi/.32;t=np.arange(200)*period/200;bounds=interval.interval_support(x['source']['periodic']['vertices'],t-.05,t+.05);rows=[]
for i,b in enumerate(bounds):
 p=ref._old.polygon(b+1e-6);cut=gate.select_contract(x['setup']['known'],p,x['packet']['body'][:2],x['goal'],REQUIRED);rows.append(dict(phase_index=i,phase_s=float(t[i]),instantaneous_sufficient_cut=cut['obstruction_proved']))
summary=dict(models=0,integrations=0,rows=rows,sufficient_cut_phase_samples=sum(r['instantaneous_sufficient_cut']for r in rows),phase_samples=200,phase_dt_s=period/200,no_cut_is_unknown_not_free=True,finite_speed_infeasibility_proved=False)
(O/'PHASE_DIAGNOSIS.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items()if k!='rows'}))
