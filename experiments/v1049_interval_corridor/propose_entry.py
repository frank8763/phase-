"""Reeds-Shepp staging guidance only; all admission uses original input model."""
import importlib.abc,importlib.util,json,math,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1049_interval_corridor'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1047_day_relay'));from kernel import PARAMETERS,ref,REQUIRED
s=importlib.util.spec_from_file_location('v1049_mit_rs',C/'third_party/reeds_shepp.py');rs=importlib.util.module_from_spec(s);s.loader.exec_module(rs)
x=json.loads((R/'runs/v1047_day_relay_20261111/INPUT_SOURCE.json').read_text());gate=json.loads((O/'LANE_INTERVAL_RESULT.json').read_text());passing=[z for z in gate['lanes']if z.get('independent_all_native_stops')];assert passing,'NO_VERIFIED_GATE_LANE';lane=max(passing,key=lambda z:z['best']['minimum_all_native_brake_raw_m']);goal=np.asarray(lane['entry_pose']);start=np.asarray(x['packet']['body'][:3]);offset=PARAMETERS['lateral_discrete'][0]/PARAMETERS['gain_a'];rear=lambda q:q[:2]-offset*np.array([math.cos(q[2]),math.sin(q[2])]);srear=rear(start);grear=rear(goal);geo=ref._old.Geometry(x['setup']['known'],x['source']['periodic']);rows=[]
for radius in [1.65,1.8,2.0]:
 paths=rs.calc_paths(*srear,start[2],*grear,goal[2],1/radius,.02)
 for path in paths:
  yaw=np.asarray(path.yaw);poses=np.c_[np.asarray(path.x)+offset*np.cos(yaw),np.asarray(path.y)+offset*np.sin(yaw),yaw];a,b=geo.clearances(poses);minimum=float(np.minimum(a,b).min());lengths=[float(a)for a in path.lengths];rows.append(dict(radius_m=radius,types=path.ctypes,lengths_m=lengths,total_length_m=float(path.L),sampled_guidance_minimum_raw_m=minimum,guidance_geometry_passed=minimum>=REQUIRED,estimated_duration_s=sum(abs(a)/(.08 if a>0 else.03)for a in lengths),reference_rear_offset_m=offset))
rows.sort(key=lambda z:(not z['guidance_geometry_passed'],z['total_length_m']));(O/'ENTRY_GUIDANCE.json').write_text(json.dumps(dict(lane=lane,start_actual_pose=start.tolist(),target_proposal_pose=goal.tolist(),proposals=rows,models=0,integrations=0,physical_ready=False),indent=2)+'\n');print(json.dumps(dict(start=start.tolist(),target=goal.tolist(),candidates=len(rows),geometry_passed=sum(z['guidance_geometry_passed']for z in rows),first=rows[:6],models=0)))
