"""Fixed real packets and independent unpruned geometry comparison; zero integration."""
from pathlib import Path
from types import SimpleNamespace
import os,sys,json,gzip,time,hashlib,importlib.util
import numpy as np
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);src=Path(__file__).resolve().parent
from motion_tracker import Tracker,install_time_gate
from union_belief import future_cells,clearance
from motion_evaluator import check_forecast
from exact_footprint import pose_values
spec=importlib.util.spec_from_file_location('baseline_global_tracker',repo/'experiments/v670_dynamic_empty_samples/motion_tracker.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
root=repo/'runs/v673_dynamic_joint_forecast';root.mkdir(exist_ok=True);started=time.monotonic();states=[];summary=[];inputs={};maxerr=0.
for relative in ['v662_dynamic_sensor_diagnosis/sensor_replay_95000011/paired','v667_dynamic_first_hit/dev36_95000011_firsthit/paired','v669_dynamic_reserved_recovery/dev37_95000011_reserve/paired','v670_dynamic_empty_samples/dev38_95000011_empty/paired']:
 p=repo/'runs'/relative;model=json.loads((p/'STATIC_PROTOCOL.json').read_text());config=json.loads((p/'DYNAMIC_PROTOCOL.json').read_text());file=p/'geometry_memory/sensor_packets.jsonl.gz';inputs[str(file.relative_to(repo))]=hashlib.sha256(file.read_bytes()).hexdigest()
 with gzip.open(file,'rt')as f:packets=[json.loads(s)for s in f]
 tracker=Tracker();baseline=old.Tracker();worst=-1e9
 for packet in packets:
  _,s=tracker.update_rays(packet['rays'],model['known_rectangles'],model['known_circles'],packet['time']);_,b=baseline.update_rays(packet['rays'],model['known_rectangles'],model['known_circles'],packet['time'])
  for key in ['position_lower','position_upper','velocity_lower','velocity_upper']:maxerr=max(maxerr,float(np.max(abs(np.asarray(s[key])-b[key]))))
  coverage=check_forecast(config,s);assert coverage['passed'],(relative,packet['step'],coverage)
  worst=max(worst,coverage['maximum_future_center_union_excess_m']);states.append(s)
 summary.append({'dataset':relative,'frames':len(packets),'maximum_future_union_excess_m':worst})
assert maxerr<=1e-12
rng=np.random.default_rng(673);largest=-1e9;positive_errors=0
for i in range(5000):
 s=states[int(rng.integers(len(states)))];p=np.r_[np.asarray(s['center'])+rng.uniform(-2.,2.,2),rng.uniform(-np.pi,np.pi)][None,:];tt=float(rng.uniform(0,3.28))
 base=dict(half=np.asarray([.44,.375]),center_local=np.zeros(2),rectangles=np.empty((0,4)),circles=np.empty((0,3)),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));field=SimpleNamespace(**base);install_time_gate(field,s,'predictive',[],[])
 got=float(field.trajectory_values(p,tt)[0]);exact=float(min(pose_values(SimpleNamespace(**base),p)[0],clearance(field,p,s['outer_state_cells'],[tt])[0]));excess=got-exact;largest=max(largest,excess);positive_errors+=int(excess>1e-9);assert excess<=1e-9,('BROADPHASE_OVERSTATED_CLEARANCE',i,excess)
result={'status':'PASS','packets':len(states),'future_native_grid_per_packet':329,'maximum_global_tracker_difference':maxerr,'independent_unpruned_geometry_cases':5000,'maximum_broadphase_clearance_overstatement_m':largest,'false_high_clearances':positive_errors,'datasets':summary,'elapsed_s':time.monotonic()-started,'simulation_integrations':0,'navigation_tasks':0,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in src.glob('*.py')},'input_sha256':inputs}
(root/'PRE_NAV_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['source_sha256','input_sha256']},indent=2))
