"""Locked old-input zero-integration validation, including synthetic stop/motion cases."""
import os,sys,json,hashlib,importlib.util
from pathlib import Path
import numpy as np
repo=Path(os.environ['PHASE_REPO']);src=Path(__file__).resolve().parent;sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
from route_commitment import route_check
from exact_footprint import build
from motion_tracker import install_time_gate
spec=importlib.util.spec_from_file_location('v689_policy_geometry',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);sys.modules[spec.name]=F;spec.loader.exec_module(F)
root=repo/'runs/v689_dynamic_route_commitment';diagnosis=json.loads((root/'REPLAN_DIAGNOSIS.json').read_text());records=[]
for old in diagnosis['records']:
 cell=repo/'runs/v688_dynamic_distance_curriculum'/old['run']/'paired/geometry_memory';step=old['step'];new=json.loads((cell/f'planning_{step:04d}.json').read_text());previous=json.loads((cell/f"planning_{old['previous_plan_step']:04d}.json").read_text());rows=json.loads((cell/'trace.json').read_text())[:step]
 states={s['step']:s for s in [json.loads(x)for x in(cell/'motion_estimate.jsonl').read_text().splitlines()]};field=build(F,new['causal_input']);install_time_gate(field,states[step],'predictive',[],[])
 value=route_check(field,np.asarray(previous['path']),old['index'],np.asarray(new['pose']),rows,step,old['previous_plan_step'])
 assert abs(value['current_route_minimum_m']-old['current_joint_route_minimum_m'])<=1e-10
 records.append({'run':old['run'],'step':step,'old_reasons':old['reconstructed_reasons'],'new_check':value,'old_trigger_suppressed':not(value['current_route_invalid']or value['stagnated_without_route_progress'])})
class FixedField:
 def __init__(self,value):self.value=value
 def pose_values(self,p):return np.full(len(p),self.value)
path=np.c_[np.linspace(0,1,51),np.zeros((51,2)),np.ones(51)];rows=[{'pose':[0,0,0],'path_index':0}for _ in range(30)]
stop=route_check(FixedField(.5),path,0,np.array([0,0,0]),rows,30,0);progress=route_check(FixedField(.5),path,10,np.array([0,0,0]),rows,30,0);blocked=route_check(FixedField(.14),path,10,np.array([0,0,0]),rows,30,0)
checks={'all15_original_trigger_inputs_reproduced':len(records)==15,'all_current_occupancies_still_safe':all(not x['new_check']['current_route_invalid']for x in records),'all_false_replans_suppressed':all(x['old_trigger_suppressed']for x in records),'true_stationary_stop_detected':stop['stagnated_without_route_progress'],'gear_loop_with_arc_progress_not_stagnation':not progress['stagnated_without_route_progress'],'current_breach_still_replans':blocked['current_route_invalid']}
out={'status':'PASS'if all(checks.values())else'FAIL','checks':{k:bool(v)for k,v in checks.items()},'records':records,'robot_integrations':0,'gradient_updates':0,'scope':'proposal bookkeeping validation only; actual dynamic rollout and complete audits still required'}
(root/'PRE_NAV_POLICY_VALIDATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'checks':out['checks']},indent=2));assert out['status']=='PASS'
