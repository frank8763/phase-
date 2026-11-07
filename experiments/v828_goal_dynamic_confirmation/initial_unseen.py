"""Evaluation of t0 unseen prior and unchanged raw sensing; zero integrations."""
import numpy as np
from motion_tracker import Tracker
from motion_evaluator import check_forecast
from range_circle_memory import measured_rays
from instrumentation import dump

def certify(env,rect,circ,config,out):
 _,state=Tracker().update(env,rect,circ,0);coverage=check_forecast(config,state)
 distance=float(np.linalg.norm(np.asarray(config['anchor_xy'])-env.data.qpos[:2]));actual=np.asarray(config['anchor_xy'])+np.sin(config['phase_rad'])*config['amplitude_m']*np.asarray(config['axis_xy'])
 import json,os
 from pathlib import Path
 cases=json.loads((Path(__file__).parent/'SCENE_CASES.json').read_text());case=next(c for c in cases if c['id']==os.environ['PHASE_FIELD_CASE'])
 checks={'genuinely_outside_initial_range':np.linalg.norm(actual-env.data.qpos[:2])-config['radius_m']>3.,'no_causal_actor_detection':state['center']is None and state['certified_unknown_rays']==0,'public_initial_exclusion_holds':np.linalg.norm(actual-env.data.qpos[:2])>=3.,'original329_prior_coverage':coverage['passed'],'initial_time_zero':float(env.data.time)==0.,'registered_field_start_goal':np.array_equal(env.data.qpos[:2],case['start_xy'])and np.array_equal(np.asarray(env.goal_xy,dtype=np.float32),np.asarray(case['goal_xy'],dtype=np.float32)),'registered_encounter':distance>=3.6 and config['new_course_id']=='V706_ORIGINAL_FIELD_RANGE_ENTRY','known_static_field_present':len(rect)==10 and len(circ)==9,'public_origin_matches_robot_state':state['initial_clear_origin_xy']==env.data.qpos[:2].tolist()}
 packet={'time':float(env.data.time),'xy':np.asarray(env.robot_xy).tolist(),'yaw':float(env.robot_yaw),'lidar':np.asarray(env.phase17c_last_lidar).tolist(),'depth':np.asarray(env.phase17c_last_depth).tolist(),'lidar_max_range':float(env.phase17c_lidar_max_range),'depth_max_range':float(env.phase17c_depth_max_range),'rays':measured_rays(env).tolist()}
 report={'passed':bool(all(checks.values())),'checks':{k:bool(v)for k,v in checks.items()},'packet':packet,'causal_state':state,'coverage_evaluator_only':coverage,'robot_integrations':0,'training_updates':0,'scope':'initial exclusion disk is a public startup prior, not sensor-certified unknown free space'}
 dump(out/'INITIAL_UNSEEN.json',report);assert report['passed'],'INITIAL_UNSEEN_PREREQUISITE_FAILED'
 return report
