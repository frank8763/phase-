"""Original saved stream, exact gate recomputation and independent selection checks."""
import copy,gzip,hashlib,importlib.abc,json,sys,time
from collections import Counter
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v933_rpccr_certified_recovery';started=time.monotonic()
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in{'mujoco','torch','factory','physical','vehicle','rclpy'}:raise AssertionError('MODEL_OR_ROS_IMPORT '+name)
sys.meta_path.insert(0,Block());sys.path[:0]=[str(C),str(R/'experiments/v924_consistent_polygon_reference'),str(R/'experiments/v887_exact_lidar_software')]
from command_tube import admit
from snapshot_geometry import field
from exact_footprint import pose_values
from certified_recovery import select,PRIMITIVES
S=O/'saved';known=json.loads((S/'SETUP.json').read_text())['known'];task=json.loads((S/'TASK.json').read_text());rows=json.loads(gzip.decompress((S/'COMMAND_TUBES.json.gz').read_bytes()));static=lambda known,poses:pose_values(field(known),poses);checks={};cases=[];counts=Counter();admitted=0;fallbacks=0;outputs=[];old_reasons=Counter()
for index,row in enumerate(rows):
 now=row['proof']['issued_at'];original=admit(row['packet'],row['source'],*row['wanted'],known,now)
 if original['passed']:admitted+=1;continue
 # Only historical nominal-to-zero/retained fallbacks; wait renewals separate.
 if row.get('wait_renewal')or list(row['wanted'])==[0.,0.]:continue
 fallbacks+=1
 for name in ['static_lower_m','dynamic_lower_m','terminal_cycle_lower_m']:
  if original[name]is not None and original[name]<.155:old_reasons[name]+=1
 result=select(row['packet'],row['source'],row['wanted'],known,now,task['goal_xy'],admit,static)
 if result.selected is not None:
  independent=admit(copy.deepcopy(row['packet']),copy.deepcopy(row['source']),*result.selected,copy.deepcopy(known),now)
  assert independent['passed']and independent==result.proof
 counts[result.mode]+=1
 outputs.append(dict(index=index,tick=row['packet']['native_tick'],mode=result.mode,selected=result.selected,source_tick=row['source']['source_native_tick'],original_wanted=row['wanted'],selected_proof=result.proof))
 assert time.monotonic()-started<240,'ZERO_MODEL_GEOMETRY_240S_BUDGET'
checks['every_selected_output_original_gate_passed']=True;checks['fixed13_primitives']=len(PRIMITIVES)==13 and len(set(PRIMITIVES))==13
for target in [9000,11000,13000,14800]:
 row=[x for x in rows if not x.get('wait_renewal')and x['packet']['native_tick']<=target][-1];now=row['proof']['issued_at'];decision=select(row['packet'],row['source'],row['wanted'],known,now,task['goal_xy'],admit,static)
 cases.append(dict(target=target,tick=row['packet']['native_tick'],body=row['packet']['body'],nominal=row['wanted'],mode=decision.mode,selected=decision.selected,nominal_proof=decision.nominal_proof,alternatives=decision.alternatives))
checks['saved_10998_recovery_exists']=cases[1]['mode']=='CERTIFIED_CLEARANCE_RECOVERY'and cases[1]['selected'][0]<0
checks['late_12999_not_falsely_rescued']=cases[2]['mode']=='NO_NEW_CERTIFIED_CONTROL'
checks['late_14798_stop_never_overridden']=cases[3]['mode']=='STOP_REQUEST_NO_OVERRIDE'and cases[3]['selected']is None
row=next(x for x in rows if admit(x['packet'],x['source'],*x['wanted'],known,x['proof']['issued_at'])['passed'])
unchanged=select(row['packet'],row['source'],row['wanted'],known,row['proof']['issued_at'],task['goal_xy'],admit,static)
checks['passed_nominal_bitwise_unchanged']=unchanged.mode=='NOMINAL_UNCHANGED'and unchanged.selected==tuple(row['wanted'])and not unchanged.alternatives
for name,mutate in [('future',lambda p,s:s.update(source_native_tick=p['native_tick']+1)),('stale',lambda p,s:p.update(body_measured_at=p['body_measured_at']-1)),('nan',lambda p,s:p['body'].__setitem__(0,float('nan')))]:
 p=copy.deepcopy(row['packet']);s=copy.deepcopy(row['source']);mutate(p,s)
 try:select(p,s,row['wanted'],known,row['proof']['issued_at'],task['goal_xy'],admit,static)
 except AssertionError:checks[name+'_rejected']=True
 else:checks[name+'_rejected']=False
# Same controller and params as the already passed V884/V885 anchor; no plugin mutation.
anchor=json.loads((R/'records/nav2_v885_20261108/RESULT_SUMMARY.json').read_text());assert anchor['combined_three_route_static_development_passed']
config=json.loads((R/'experiments/v884_feasible_rpp/A_feasible.yaml').read_text());controller=config['controller_server']['ros__parameters']['FollowPath'];assert controller['plugin']=='phase_feasible_rpp/FeasibleRPP'
fingerprints={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [R/'experiments/v884_feasible_rpp/feasible_rpp.cpp',R/'experiments/v884_feasible_rpp/feasible_twist.hpp',R/'experiments/v884_feasible_rpp/A_feasible.yaml',R/'experiments/v924_consistent_polygon_reference/command_tube.py']}
checks['passed_rpp_static_anchor_preserved']=True
result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,saved_decisions=len(rows),passed_original_nominal=admitted,original_fallbacks_examined=fallbacks,original_refusal_categories=dict(old_reasons),selection_counts=dict(counts),fixed_cases=cases,source_fingerprints=fingerprints,elapsed_s=time.monotonic()-started,physical_candidate_ready=False,scope='RP-CCR certified recovery component only. Each selected first command passes unchanged V924 predicate; one-second ranking is not a dynamics or successor certificate. Saved counterfactual selection does not rescue old actual trajectory or prove arrival.')
(O/'SAVED_SELECTIONS.json').write_text(json.dumps(outputs,indent=2)+'\n');(O/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='fixed_cases'},indent=2));assert result['passed']
