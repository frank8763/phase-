"""Saved-only paired diagnosis of the two closed reference-tail qualifications."""
import importlib.abc
import importlib.util
import json
import hashlib
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np

class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('ZERO_MODEL_CLOSED_CANDIDATE_ANALYSIS')
sys.meta_path.insert(0,NoModels())
repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/'experiments/v839_reference_differential_development'))
from exact_footprint import pose_values
from independent_norm import static_field,radial_lower
pair=repo/'runs/v830_ranked_return_development/main_slot01/paired'
cell=pair/'geometry_memory';protocol=json.loads((pair/'STATIC_PROTOCOL.json').read_text())
static=static_field(protocol)
spec=importlib.util.spec_from_file_location('original_broad_saved',repo/'experiments/v812_soft_global_reference/motion_tracker.py')
original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
states={x['step']:{k:v for k,v in x.items()if k!='step'}for x in map(json.loads,(cell/'motion_estimate.jsonl').open())}
def bound(poses,state,times):
 field=SimpleNamespace(**static.__dict__)
 original.install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
 return np.maximum(field.causal_values_at_times(poses,times),np.minimum(pose_values(static,poses),radial_lower(static,poses,state,times)))
records=[];inventories=[];pool={}
for label in ['v835_reference_recovery_qualification','v838_reference_differential_qualification']:
 root=repo/'runs'/label;folder=root/'step0495'
 final=json.loads((root/'FINALIZED.json').read_text());assert not final['component_passed']and final['source_and_decompressed_sha_verified']
 rows=[]
 for attempt in json.loads((folder/'ATTEMPTS.json').read_text()):
  for candidate in attempt['detail']['candidates']:
   if candidate['library']!='REFERENCE_FOLLOW':continue
   file=folder/candidate['full_forecast_file'];z=np.load(file);poses=z['poses'];values=bound(poses,states[495],np.arange(1,337)*.01);sv=pose_values(static,poses)
   assert len(poses)==336 and abs(float(sv[:328].min())-candidate['minimum_static_m'])<=1e-8
   assert values[:328].min()<.155
   row=dict(rank=attempt['source']['rank'],lookahead=candidate['lookahead_m'],wheel=candidate['wheel_speed'],drive=candidate['brake_after_native_ticks'],minimum_static328_m=float(sv[:328].min()),minimum_time328_m=float(values[:328].min()),minimum_time336_m=float(values.min()),yaw_change_deg=float(np.rad2deg(poses[-1,2]-poses[7,2])),goal_gain_m=candidate['complete_goal_progress_m'],file=str(file.relative_to(repo)))
   rows.append(row);inventories.append(dict(path=str(file.relative_to(repo)),sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
   if label.startswith('v838'):pool[(row['rank'],row['lookahead'],row['wheel'],row['drive'])]=(poses,values)
 summary=dict(version=label,new_reference_tails=len(rows),static_passed=sum(x['minimum_static328_m']>=.155 for x in rows),static_failed=sum(x['minimum_static328_m']<.155 for x in rows),all_time_rejected=True,best_time_minimum_m=max(x['minimum_time328_m']for x in rows),yaw_range_deg=[min(x['yaw_change_deg']for x in rows),max(x['yaw_change_deg']for x in rows)],records=rows)
 records.append(summary)
# Inspect historical valid bounds only for the six best current-bound candidates.
# These are existing past packets at 470..495. No later sensor packet or truth used.
selected=sorted(records[-1]['records'],key=lambda x:x['minimum_time328_m'],reverse=True)[:6]
history=[]
for row in selected:
 key=(row['rank'],row['lookahead'],row['wheel'],row['drive']);poses,values=pool[key];combined=values.copy()
 for step in range(470,495):
  state=states[step];times=np.arange(1,337)*.01+states[495]['time']-state['time']
  assert times.min()>=0 and state['time']<states[495]['time']
  combined=np.maximum(combined,bound(poses,state,times))
 history.append(dict(rank=row['rank'],lookahead=row['lookahead'],wheel=row['wheel'],drive=row['drive'],current_minimum336_m=float(values.min()),historical_maximum_minimum336_m=float(combined.min()),geometry_admission_flip=bool(values.min()<.155 and combined.min()>=.155)))
out=repo/'runs/reference_recovery_analysis_20261106';out.mkdir(exist_ok=False)
result=dict(status='CLOSED_REFERENCE_CANDIDATE_CAUSE_DECOMPOSITION',versions=records,historical_counterfactual=history,historical_scope='Only six best fixed saved new tails, past470..495; geometric counterfactual, no new model or executed control, no overall feasibility theorem.',models=0,integrations=0,source_files=inventories)
(out/'CAUSES.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k not in['source_files','versions']},ensure_ascii=False))
for x in records:print(json.dumps({k:v for k,v in x.items()if k!='records'}))
