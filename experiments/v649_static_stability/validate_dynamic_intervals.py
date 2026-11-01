"""Offline causal packet replay; scene truth is confined to this evaluator."""
from pathlib import Path
import argparse,gzip,json,sys,time,hashlib,os
import numpy as np
repo=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--source',default='experiments/v663_dynamic_interval_tracking');a=p.parse_args();sys.path.insert(0,str(repo/a.source))
from motion_tracker import Tracker,future_boxes
started=time.monotonic();root=repo/'runs/v662_dynamic_sensor_diagnosis/sensor_replay_95000011/paired'
with gzip.open(root/'geometry_memory/sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
model=json.loads((root/'STATIC_PROTOCOL.json').read_text());c=json.loads((root/'DYNAMIC_PROTOCOL.json').read_text());tracker=Tracker();records=[];failure=None
try:
 for packet in packets:
  _,state=tracker.update_rays(packet['rays'],model['known_rectangles'],model['known_circles'],packet['time'])
  assert state['center']is not None,'MISSING_INITIAL_DETECTION'
  t=packet['time'];future=np.linspace(0,2.4,121);lo,hi=future_boxes(state,future)
  truth=np.array(c['anchor_xy'])+np.sin((t+future)*c['omega_rad_s'])[:,None]*c['amplitude_m']*np.array(c['axis_xy'])
  velocity=np.cos(t*c['omega_rad_s'])*c['maximum_speed_m_s']*np.array(c['axis_xy'])
  excess=float(np.maximum(lo-truth,truth-hi).max());current_error=float(np.linalg.norm(np.array(state['center'])-truth[0]))
  velocity_excess=float(np.maximum(np.array(state['velocity_lower'])-velocity,velocity-np.array(state['velocity_upper'])).max())
  records.append({'step':packet['step'],'state':state,'future_center_box_max_excess_m':excess,'velocity_box_excess_m_s':velocity_excess,'current_center_error_m':current_error})
  assert excess<=1e-7 and velocity_excess<=1e-7,'TRUE_ACTOR_OUTSIDE_CAUSAL_POSITION_OR_VELOCITY_SET'
except BaseException as e:failure={'type':type(e).__name__,'message':str(e),'step':len(records)}
result={'status':'PASS'if failure is None and len(records)==264 else'FAIL','error':failure,'packets':len(packets),'processed':len(records),'forecast_times_per_packet':121,'horizon_s':2.4,'maximum_future_center_box_excess_m':max((r['future_center_box_max_excess_m']for r in records),default=None),'maximum_current_center_error_m':max((r['current_center_error_m']for r in records),default=None),'maximum_velocity_box_excess_m_s':max((r['velocity_box_excess_m_s']for r in records),default=None),'elapsed_s':time.monotonic()-started,'simulation_steps':0,'navigation_tasks':0,'source':a.source,'tracker_sha256':hashlib.sha256((repo/a.source/'motion_tracker.py').read_bytes()).hexdigest(),'scope':'development causal packet replay only; finite pose/future grid, not independent confirmation or calibrated probability'}
out=repo/'runs/v663_dynamic_interval_tracking';out.mkdir(exist_ok=True)
(out/'OFFLINE_PACKET_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
with gzip.open(out/'offline_packet_states.jsonl.gz','wt')as f:
 for row in records:f.write(json.dumps(row)+'\n')
print(json.dumps(result,indent=2))
