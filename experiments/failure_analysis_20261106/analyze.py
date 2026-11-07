"""Independent saved-only bound decomposition and chronological failure seam."""
import importlib.abc,importlib.util,json,gzip,sys,math
from pathlib import Path
from types import SimpleNamespace
import numpy as np
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('ZERO_MODEL_FAILURE_ANALYSIS')
sys.meta_path.insert(0,NoModels());repo=Path(__file__).resolve().parents[2];science=repo/'experiments/v834_timed_escape_development'
for d in[repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1',science]:sys.path.insert(0,str(d))
from exact_footprint import pose_values
from independent_norm import static_field,radial_lower
spec=importlib.util.spec_from_file_location('independent_broad_original',repo/'experiments/v812_soft_global_reference/motion_tracker.py');original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
read=lambda p:json.loads(p.read_text());pair=repo/'runs/v830_ranked_return_development/main_slot01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');base=static_field(protocol)
needed=set([470,478,485,488,489,490,491,495,527,531]);states={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').open())if x['step']in needed}
execution={x['step']:x for x in map(json.loads,(cell/'v648_execution.jsonl').open())};admissions={x['step']:x for x in map(json.loads,(cell/'model_admission.jsonl').open())};routes={x['step']:x for x in map(json.loads,(cell/'route_revalidation.jsonl').open())}
def decompose(p,state,clock):
 p=np.asarray(p);clock=np.asarray(clock);f=SimpleNamespace(**base.__dict__);original.install_time_gate(f,state,'predictive',protocol['known_circles'],protocol['known_rectangles']);static=pose_values(base,p);broad=f.causal_values_at_times(p,clock);radial=radial_lower(base,p,state,clock);refined=np.maximum(broad,np.minimum(static,radial));current=np.maximum(f.causal_values_at_times(p,np.zeros(len(p))),np.minimum(static,radial_lower(base,p,state,np.zeros(len(p)))))
 minimum=int(np.argmin(refined));return dict(native_samples=len(p),minimum_static_m=float(static.min()),minimum_current_occupancy_m=float(current.min()),minimum_broad_m=float(broad.min()),minimum_norm_m=float(np.minimum(static,radial).min()),minimum_refined_m=float(refined.min()),minimum_tick=minimum+1,time_at_minimum_s=float(clock[minimum]),static_at_minimum_m=float(static[minimum]),current_at_minimum_m=float(current[minimum]),broad_at_minimum_m=float(broad[minimum]),norm_at_minimum_m=float(np.minimum(static,radial)[minimum]),required_m=.155),refined
timeline=[]
for step in sorted(needed):
 state=states[step];a=admissions.get(step,{});route=routes.get(step,{});timeline.append(dict(step=step,time_s=state['time'],observed_this_frame=state['observed_this_frame'],observation_age_s=state['age_s'],cells=len(state['outer_state_cells']),admission=a.get('status'),reserve_minimum_m=a.get('recovery_reserve',{}).get('reserve_minimum_clearance_m',a.get('predicted_minimum_clearance_m')),recovery_kind=a.get('recovery_kind',a.get('recovery_reserve',{}).get('recovery_kind')),reserve_terminal_xy=a.get('predicted_end_pose',[])[:2],route_invalid=route.get('current_route_invalid'),route_minimum_m=route.get('current_route_minimum_m'),last_plan=route.get('last_plan'),new_plan_finite=route.get('route_exists')))
with gzip.open(next((cell/'recovery_contracts').glob('*.gz')),'rt')as f:cache=json.load(f)
assert cache['created_step']==490
q=np.asarray(cache['qpos']);p=np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))];complete=np.vstack([cache['prefix_poses'],p]);original_certificate,values=decompose(complete,cache['forecast_state'],np.arange(1,329)*.01)
assert abs(values.min()-cache['minimum_causal_predicted_clearance_m'])<=1e-8 and values.min()>=.155
handover_seams=[]
for step in[495,527]:
 cursor=(step-491)*8;remaining=p[cursor:];newstate=states[step]
 existing,_=decompose(remaining,cache['forecast_state'],(np.arange(cursor+1,321)+8)*.01)
 fresh_remaining,_=decompose(remaining,newstate,np.arange(1,len(remaining)+1)*.01)
 current=np.asarray(execution[step-1]['qpos_full']);yaw=math.atan2(2*(current[3]*current[6]+current[4]*current[5]),1-2*(current[5]**2+current[6]**2));stationary=np.repeat([[current[0],current[1],yaw]],328,axis=0);stationary_bound,_=decompose(stationary,newstate,np.arange(1,329)*.01)
 attempts=read(repo/f'runs/v833_timed_escape_qualification/step{step:04d}/ATTEMPTS.json');candidates=[(a['source']['rank'],c)for a in attempts for c in a['detail']['candidates']if c['library']=='RETURN_TIMED_ESCAPE'];rank,c=max(candidates,key=lambda x:x[1]['early_rejection_witness_value_m']);z=np.load(repo/f'runs/v833_timed_escape_qualification/step{step:04d}'/c['early_rejection_witness_file']);saved,newvalues=decompose(z['poses'],newstate,np.arange(1,329)*.01);tick=c['early_rejection_witness_native_tick'];assert abs(newvalues[tick-1]-c['early_rejection_witness_value_m'])<=1e-8
 handover_seams.append(dict(step=step,remaining_original_contract_native=len(remaining),remaining_old_certificate=existing,remaining_with_fresh_belief=fresh_remaining,stationary_at_current_pose=stationary_bound,best_recorded_rejection_witness_candidate=dict(nominal_rank=rank,target=c['target_command'],brake=c['brake_after_native_ticks'],signed_displacement_m=c['signed_displacement_m'],complete_goal_gain_m=c['complete_goal_progress_m'],terminal_speed_m_s=c['terminal_speed_m_s'],bounds=saved)))
plans=[dict(step=x['step'],status=x['stats']['status'],nodes=len(x['path']) if x['path'] else 0,pose=x['pose'])for x in [read(p)for p in sorted(cell.glob('planning_*.json'))]]
result=dict(status='SAVED_FAILURE_DECOMPOSITION_VERIFIED',timeline=timeline,original490_certificate=original_certificate,handover_seams=handover_seams,global_plans=plans,models=0,integrations=0,scope='Saved geometric bound and decision provenance only; counterfactual new control success and recursive feasibility are unproven.')
out=repo/'runs/failure_analysis_20261106/CAUSE_DECOMPOSITION.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
