"""Zero-integration independent reconstruction of initial packet and motion set."""
import os,json,sys,argparse
from pathlib import Path
import numpy as np
from motion_tracker import Tracker
from motion_evaluator import check_forecast
p=argparse.ArgumentParser();p.add_argument('paired');a=p.parse_args();root=Path(a.paired)
read=lambda p:json.loads(p.read_text())
report=read(root/'INITIAL_VISIBILITY.json');packet=report['packet'];protocol=read(root/'STATIC_PROTOCOL.json');config=read(root/'DYNAMIC_PROTOCOL.json');rays=[]
for name,b,sigma in [('lidar',.06,.02),('depth',.09,.03)]:
 ranges=np.clip(np.asarray(packet[name]),0,1)*packet[name+'_max_range'];R=packet[name+'_max_range'];angles=(np.arange(len(ranges))*2*np.pi/len(ranges)if name=='lidar'else np.linspace(-np.deg2rad(35),np.deg2rad(35),len(ranges)))+packet['yaw'];keep=(ranges>.05)&(ranges<R-b-1e-5)
 for angle,z in zip(angles[keep],ranges[keep]):rays.append([*packet['xy'],np.cos(angle),np.sin(angle),z,b,sigma])
circles,state=Tracker().update_rays(rays,protocol['known_rectangles'],protocol['known_circles'],0.);coverage=check_forecast(config,state)
checks={'registered8mgeometry':protocol['goal_xy']==[4.,-2.]and protocol['start_qpos'][:2]==[-4.,-2.]and config['anchor_xy']==[-2.,-2.]and config['initial_encounter_distance_m']==2.,'raw_ray_filter_reconstructed':np.array_equal(np.asarray(rays),np.asarray(packet['rays'])),'original_causal_state_reconstructed':state==report['causal_state'],'positive_actor_detection':state['center']is not None and state['certified_unknown_rays']>0,'original_future_coverage':coverage==report['coverage_evaluator_only']and coverage['passed'],'no_truth_in_state':state['hidden_world_geometry_used']is False,'report_passed':report['passed']is True,'zero_initial_physics':packet['time']==0.}
out={'status':'PASS'if all(checks.values())else'FAIL','checks':checks,'certified_unknown_rays':state['certified_unknown_rays'],'verification_integrations':0,'scope':'declared initially visible course, not original failed3mencounter'}
(root/'INITIAL_VISIBILITY_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert out['status']=='PASS'
