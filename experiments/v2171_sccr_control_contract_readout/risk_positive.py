"""New finite risk-positive seam supplement, no rerun of the saved-frame study."""
import copy, json, math, os, hashlib
from pathlib import Path
import numpy as np
from study import ROOT, OUT, PRIOR, shell, clean, SOURCES
assert os.sched_getaffinity(0)=={0}
f=OUT/'RISK_POSITIVE_SUPPLEMENT.json'
assert not f.exists()
p=json.loads((PRIOR/'SCCR_UNION_000000.json').read_text())['sensor_packet']
results=[]
# Five fixed local scenes, two rigid frames per scene. No parameter search.
for label,index,want_side in [('front_center',0,'CENTER'),('left_conflict',1,'LEFT'),('right_conflict',31,'RIGHT'),('rear_excluded',16,'NONE'),('all_clear',None,'NONE')]:
 risks=[]
 for yaw,origin in [(0.,[0.,0.]),(.7,[2.,-1.])]:
  q=copy.deepcopy(p);q['body']=[*origin,yaw,0.,0.]
  c,s=math.cos(yaw),math.sin(yaw)
  q['path_world']=[[origin[0]+c*z,origin[1]+s*z] for z in np.linspace(0,2.4,61)]
  q['phase17_lidar32']=[1.]*32;q['phase17_depth15']=[1.]*15
  if index is not None:q['phase17_lidar32'][index]=1/3
  x=shell(q);x._phase21_compute_corridor_state()
  assert x.phase21_last_obstacle_side==want_side
  if want_side!='NONE':
   assert x.phase21_last_risk>0 and x.phase21_last_conflict_count==1
   # Independent local distance to straight centreline: abs(y), for a hit within the segment.
   y=math.sin(index*2*math.pi/32)
   assert abs(x.phase21_last_min_path_clearance-abs(y))<1e-6
  else:assert x.phase21_last_risk==0 and x.phase21_last_conflict_count==0
  risks.append(x.phase21_last_risk)
  results.append({'scene':label,'rigid_yaw':yaw,'origin':origin,'risk':x.phase21_last_risk,
                  'side':x.phase21_last_obstacle_side,'conflicts':x.phase21_last_conflict_count,
                  'min_path_clearance_m':x.phase21_last_min_path_clearance})
 assert abs(risks[0]-risks[1])<1e-6
r={'passed':True,'scope':'FIXED_SYNTHETIC_RISK_POSITIVES_REAR_NEGATIVE_AND_RIGID_FRAME_INVARIANCE',
   'cases':results,'local_source_default_only':True,'saved_frame_study_not_rerun':True,
   'input_template_SHA256':hashlib.sha256((PRIOR/'SCCR_UNION_000000.json').read_bytes()).hexdigest(),
   'source_SHA256':SOURCES,'new_NN_render_model_physics_replay_audit':0,
   'full_V3_detour_and_navigation_not_executed':True}
f.write_text(json.dumps(clean(r),indent=2,allow_nan=False)+'\n')
print(json.dumps({'passed':True,'fixed_cases':len(results),'new_NN_physics':0}))
