"""Split the overloaded TIME_CLEARANCE label using saved full native poses, zero models."""
import importlib.abc,sys,json
from pathlib import Path
import numpy as np
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('SAVED_ONLY')
sys.meta_path.insert(0,NoModels());repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo/'experiments/v834_timed_escape_development'))
from exact_footprint import pose_values
from independent_norm import static_field
pair=repo/'runs/v830_ranked_return_development/main_slot01/paired';protocol=json.loads((pair/'STATIC_PROTOCOL.json').read_text());base=static_field(protocol);results=[]
for step in[495,527]:
 folder=repo/f'runs/v833_timed_escape_qualification/step{step:04d}';attempts=json.loads((folder/'ATTEMPTS.json').read_text());items=[dict(rank=a['source']['rank'],candidate=c)for a in attempts for c in a['detail']['candidates']if c['library']=='RETURN_TIMED_ESCAPE'];all_records=[]
 for start in range(0,len(items),8):
  group=items[start:start+8];poses=np.vstack([np.load(folder/x['candidate']['early_rejection_witness_file'])['poses']for x in group]);values=pose_values(base,poses).reshape(len(group),328)
  for x,v in zip(group,values):
   c=x['candidate'];assert c['reason']=='TIME_CLEARANCE' and len(v)==328 and np.isfinite(v).all()
   all_records.append(dict(rank=x['rank'],wheel=c['target_command'][2],steering=c['target_command'][:2],brake=c['brake_after_native_ticks'],minimum_static_m=float(v.min()),static_passed=bool(v.min()>=.155),time_clearance_rejected=c['reason']=='TIME_CLEARANCE',goal_progress_m=c['complete_goal_progress_m'],terminal_speed_m_s=c['terminal_speed_m_s'],self_margin_m=c['self_domain_margin_m'],witness_m=c['early_rejection_witness_value_m']))
 statically_safe=[x for x in all_records if x['static_passed']];dynamically_blocked=len(statically_safe);best=max(statically_safe,key=lambda x:x['witness_m'])if statically_safe else None
 results.append(dict(step=step,new_candidates=len(all_records),static_geometry_below0155=sum(not x['static_passed']for x in all_records),static_passed_but_time_gate_failed=dynamically_blocked,static_self_terminal_goal_passed_but_time_failed=sum(x['self_margin_m']>=.002 and x['terminal_speed_m_s']<=.025 and x['goal_progress_m']>=.02 for x in statically_safe),best_static_passed_rejection_witness=best,records=all_records))
out=repo/'runs/failure_analysis_20261106/TAIL_REJECTION_CLASSIFICATION.json';out.write_text(json.dumps(dict(status='SAVED_STATIC_VS_TEMPORAL_REJECTION_SPLIT',records=results,models=0,integrations=0),indent=2)+'\n');print(json.dumps([{k:v for k,v in x.items()if k!='records'}for x in results]))
