"""Hypothesis probes on frozen saved decisions; no new rollout or parameter tuning."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('NO_NEW_MODEL')
sys.meta_path.insert(0,NoModels())
import json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/dynamic_24_next_analysis_20261106';read=lambda p:json.loads(p.read_text());ls=lambda p:[json.loads(s)for s in p.open()]
cell=R/'runs/v841_early_joint/main_slot01/paired/geometry_memory';events=ls(cell/'early_joint_decisions.jsonl');ad=ls(cell/'model_admission.jsonl');result=read(cell/'result.json');counts=Counter();reasons=defaultdict(Counter);geometry=defaultdict(float);valid_reference=0;static_reference_fail=0;temporal_reference_fail=0;reference_details=[];above=[];native_probes=0
for e in events:
 step=e['step']
 if ad[step-1].get('recovery_reserve',{}).get('reserve_minimum_clearance_m',-1)>=.4174:above.append(dict(step=step,selected_rank=e['selected_rank'],previous_margin=ad[step-1]['recovery_reserve']['reserve_minimum_clearance_m']))
 for p in e['probes']:
  native_probes+=8
  for c in p['detail']['candidates']:
   counts[c['library']]+=1;native_probes+=328;reasons[c['library']][str(c['reason'])]+=1;geometry[c['library']]+=c['geometry_wall_s']
   if c['library']=='REFERENCE_FOLLOW':
    valid_reference+=c['reason']is None
    static_reference_fail+=c['reason']=='TIME_CLEARANCE'and c['minimum_static_m']<.155
    temporal_reference_fail+=c['reason']=='TIME_CLEARANCE'and c['minimum_static_m']>=.155
    if c['reason']is None:reference_details.append(dict(step=step,rank=p['rank'],score=c['selection_score'],gain=c['joint_goal_gain_m'],minimum=c['minimum_clearance_m'],chosen_event_score=next(x['joint_score']for x in e['probes']if x['rank']==e['selected_rank'])))
post=result['prediction_steps']-ad[294]['prediction_steps_total'];nominal=94*25*240;assert post==native_probes+nominal
actual=read(R/'runs/v828_goal_dynamic_confirmation/FINAL_INDEPENDENT_AUDIT.json');mains=actual['records'];failures=[dict(slot=x['task']['slot'],seed=x['task']['seed'],outcome=x['result']['outcome'],distance_m=x['result']['goal_distance_m'],public=x['result']['public_steps'],wall_s=x['result']['elapsed_s'])for x in mains if not x['functional_passed']]
success=[x['result']['elapsed_s']for x in mains if x['functional_passed']];old_tasks=read(R/'experiments/v828_goal_dynamic_confirmation/TASK_LIST.json');fresh_path=R/'experiments/v840_reference_differential_confirmation/TASK_LIST.json';fresh=fresh_path.read_bytes();fresh_tasks=json.loads(fresh);assert len(fresh_tasks)==24 and fresh== (R/'experiments/v837_reference_recovery_confirmation/TASK_LIST.json').read_bytes()
assert not(R/'runs/v840_reference_differential_confirmation/ROUND_WINDOW.json').exists()and not(R/'runs/v837_reference_recovery_confirmation/ROUND_WINDOW.json').exists()
out=dict(models=0,integrations=0,old24=dict(planned=24,attempted=8,successes=6,functional_failures=failures,unexecuted_seeds=[t['seed']for t in old_tasks[8:]],upper_successes_if_remaining_all_pass=22,original_gate_can_no_longer_pass=True),unused_locked24=dict(seeds=[t['seed']for t in fresh_tasks],sha256=hashlib.sha256(fresh).hexdigest(),source=str(fresh_path.relative_to(R)),round_never_started=True,do_not_tune_on_this_pool=True),v841=dict(early_cycles=len(events),probes=sum(len(e['probes'])for e in events),tails=dict(counts),reasons={k:dict(v)for k,v in reasons.items()},logged_tail_geometry_wall_s=dict(geometry),reference_python_native_calls=counts['REFERENCE_FOLLOW']*328,post_trigger_all_private_native=post,reference_prediction_native_share=counts['REFERENCE_FOLLOW']*328/post,individual_prediction_and_io_wall_shares_unknown=True,valid_reference_candidates=valid_reference,reference_static_time_rejections=static_reference_fail,reference_dynamic_time_rejections=temporal_reference_fail,global_selected_reference=0,above_guard_cycles=len(above),above_guard_nonzero_nominal_rank=sum(x['selected_rank']!=0 for x in above),first_above_guard=None if not above else above[0],turning_off_search_would_change_decisions_not_an_exact_optimization=any(x['selected_rank']!=0 for x in above),safe_reference_score_records=reference_details),time_budget=dict(old_six_successful_navigation_wall_s=success,old_success_median_s=float(np.median(success)),old_success_max_s=max(success),old_27_navigation_at_observed_median_hours=27*float(np.median(success))/3600,old_27_navigation_at_observed_max_hours=27*max(success)/3600,excludes24_t0_audits_archive_and_new_version_cost=True,confirmation_27_navigation_at_60min_cap_hours=27,confirmation_old1505_outer27_navigation_plus24t0_125_seconds_hours=(27*1505+24*125)/3600,finite_goal_success_with_more_budget_unknown=True))
(O/'SAVED_ANALYSIS.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='v841'},ensure_ascii=False));print('V841',json.dumps({k:v for k,v in out['v841'].items()if k!='safe_reference_score_records'},ensure_ascii=False))
