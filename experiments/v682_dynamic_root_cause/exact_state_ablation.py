"""Evaluator-only exact current state under unchanged future bounds; zero integration."""
import os,sys,json,hashlib
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
repo=Path(os.environ['PHASE_REPO']);out=repo/'runs/v682_dynamic_root_cause';p=out/'EXACT_STATE_ABLATION.json';assert not p.exists();root=repo/'runs/v680_dynamic_later_stop_reserve/dev47_95000011_laterstop/paired';sys.path.insert(0,str(root.parent/'source_snapshot'))
from motion_tracker import install_time_gate
from exact_footprint import pose_values
read=lambda p:json.loads(p.read_text());analysis=read(out/'ANALYSIS.json');protocol=read(root/'STATIC_PROTOCOL.json');bounds=np.asarray(protocol['footprint_bounds']);records=[]
for r in analysis['records']:
 if'evaluator_only_counterfactual'not in r:continue
 e=r['evaluator_only_counterfactual'];pos=e['true_current_center'];vel=e['true_current_velocity'];state={'center':pos,'position_lower':pos,'position_upper':pos,'velocity_lower':vel,'velocity_upper':vel,'outer_state_cells':[[pos,pos,vel,vel]]};f=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));f.pose_values=MethodType(pose_values,f);install_time_gate(f,state,'predictive',protocol['known_circles'],protocol['known_rectangles']);poses=np.repeat(np.asarray(e['root_pose'])[None,:],329,axis=0);values=np.r_[f.pose_values(poses[:1]),f.trajectory_values(poses[1:],.01)];record={'step':r['step'],'causal_estimated_current_state_clearance_m':r['frozen_pose_causal_clearances_m'],'exact_current_state_same_future_bounds_clearance_m':values[[0,80,240,328]].tolist(),'actual_sinusoid_future_clearance_m':e['true_future_frozen_pose_clearances_m'],'scope':'same fixed root pose, geometry only; all truth evaluator-only'};records.append(record);print(record,flush=True)
result={'status':'COMPLETED_EVALUATOR_ONLY_DECOMPOSITION','times_s':[0,.8,2.4,3.28],'records':records,'robot_integrations':0,'navigation_tasks':0,'online_inputs_changed':False,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'analysis_input_sha256':hashlib.sha256((out/'ANALYSIS.json').read_bytes()).hexdigest()};p.write_text(json.dumps(result,indent=2)+'\n')
