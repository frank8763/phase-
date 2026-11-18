"""Saved-input original exact-footprint lattice alternative, zero physical models."""
import importlib.util,json,gzip,sys
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1342_dynamic_relay_preparation'
sys.path.insert(0,str(C));from causal_occupancy import CausalBall
sys.path.insert(0,str(R/'experiments/v855_renewal_worker'));from task_planner import search
spec=importlib.util.spec_from_file_location('exact_saved_geometry',R/'experiments/v855_renewal_worker/exact_footprint.py');geo=importlib.util.module_from_spec(spec);spec.loader.exec_module(geo)
P=R/'runs/v858_nav2_verified/v1341/rpp_default_dynamic_main';known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text());tracker=CausalBall(known)
with gzip.open(P/'physics/SENSORS.json.gz','rt') as stream:scans=json.load(stream)
scan=next(x for x in scans if x['native_tick']==4505);tracker.update(native_tick=4505,sim_time=scan['time'],center_body=[*scan['xy'],scan['yaw']],ranges=scan['ranges']);center,radius=tracker.occupied_ball(scan['time'])
field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.array(known['known_rectangles']),circles=np.array([*known['known_circles'],[*center,radius]]),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.,resolution=.05),clearance=np.ones((201,201)));field.pose_values=MethodType(geo.pose_values,field)
path,report=search(field,[*scan['xy'],scan['yaw']],[4,-2],.6,.42722137342572125,guard=.18,budget=15.,dense_requested_guard=True)
proof=dict(passed=path is not None and report['status']=='GLOBAL_GOAL_PATH',report=report,path=path.tolist() if path is not None else None,causal_ball=[*center,radius],models=0,physical_native=0);(O/'EXACT_LATTICE_PROBE.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='path'}))
