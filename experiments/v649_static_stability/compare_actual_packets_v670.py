"""Same recorded actual packets, two estimators, zero control/navigation/integration."""
from pathlib import Path
import os,sys,json,gzip,importlib.util
import numpy as np
repo=Path(__file__).resolve().parents[2];src=repo/'experiments/v670_dynamic_empty_samples';sys.path.insert(0,str(src))
from motion_tracker import Tracker,future_boxes
spec=importlib.util.spec_from_file_location('old_tracker',repo/'experiments/v669_dynamic_reserved_recovery/motion_tracker.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
root=repo/'runs/v670_dynamic_empty_samples';pair=root/'dev38_95000011_empty/paired';cell=pair/'geometry_memory';model=json.loads((pair/'STATIC_PROTOCOL.json').read_text());config=json.loads((pair/'DYNAMIC_PROTOCOL.json').read_text())
with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
actual=[json.loads(s)for s in(cell/'motion_estimate.jsonl').read_text().splitlines()];assert len(actual)==len(packets)
new=Tracker();baseline=old.Tracker();records=[];maxerr=0.
for packet,saved in zip(packets,actual):
 _,s=new.update_rays(packet['rays'],model['known_rectangles'],model['known_circles'],packet['time']);_,b=baseline.update_rays(packet['rays'],model['known_rectangles'],model['known_circles'],packet['time'])
 for key in ['position_lower','position_upper','velocity_lower','velocity_upper']:
  maxerr=max(maxerr,float(np.max(abs(np.asarray(s[key])-saved[key]))))
 assert maxerr<=1e-10,'ESTIMATOR_PACKET_REPLAY_MISMATCH'
 excess=[]
 for state in [s,b]:
  tt=np.linspace(0,3.28,165);lo,hi=future_boxes(state,tt);truth=np.asarray(config['anchor_xy'])+np.sin((state['time']+tt)*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy']);v=np.cos(state['time']*config['omega_rad_s']+config['phase_rad'])*config['maximum_speed_m_s']*np.asarray(config['axis_xy'])
  e=float(np.maximum(lo-truth,truth-hi).max());ve=float(np.maximum(np.asarray(state['velocity_lower'])-v,v-np.asarray(state['velocity_upper'])).max());assert max(e,ve)<=1e-7;excess.append(e)
 area=lambda x:float(np.prod(np.asarray(x['position_upper'])-x['position_lower']))
 records.append({'step':packet['step'],'new_area_m2':area(s),'baseline_area_m2':area(b),'future_excess_new_baseline_m':excess})
a=float(np.mean([r['new_area_m2']for r in records]));b=float(np.mean([r['baseline_area_m2']for r in records]));result={'status':'PASS','same_packet_frames':len(records),'new_mean_area_m2':a,'baseline_mean_area_m2':b,'mean_area_reduction_fraction':1-a/b,'terminal_area_new_m2':records[-1]['new_area_m2'],'terminal_area_baseline_m2':records[-1]['baseline_area_m2'],'maximum_reconstructed_online_state_error':maxerr,'future_times_per_frame_per_estimator':165,'all_finite_center_velocity_coverage_pass':True,'simulation_integrations':0,'navigation_tasks':0,'scope':'actual new recorded packets estimator-only same-input ablation; not a controller counterfactual or independent sample'}
(root/'ACTUAL_PACKET_ESTIMATOR_ABLATION.json').write_text(json.dumps(result,indent=2)+'\n')
with gzip.GzipFile(str(root/'actual_packet_ablation.jsonl.gz'),'wb',mtime=0)as f:
 for r in records:f.write((json.dumps(r)+'\n').encode())
print(json.dumps(result,indent=2))
