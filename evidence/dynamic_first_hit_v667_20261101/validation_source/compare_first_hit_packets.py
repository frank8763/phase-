"""Paired perception ablation on the same recorded packets; not navigation ablation."""
import argparse,gzip,json,importlib.util,sys,hashlib
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('pair');a=p.parse_args();root=Path(a.pair)
src=repo/'experiments/v667_dynamic_first_hit';sys.path.insert(0,str(src))
from motion_tracker import Tracker,future_boxes
spec=importlib.util.spec_from_file_location('baseline_without_first_hit',repo/'experiments/v666_dynamic_dense_navigation/motion_tracker.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
model=json.loads((root/'STATIC_PROTOCOL.json').read_text());c=json.loads((root/'DYNAMIC_PROTOCOL.json').read_text())
with gzip.open(root/'geometry_memory/sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
saved=[json.loads(s)for s in(root/'geometry_memory/motion_estimate.jsonl').read_text().splitlines()]
new_tracker=Tracker();old_tracker=old.Tracker();records=[]
for packet,recorded in zip(packets,saved):
    _,new=new_tracker.update_rays(packet['rays'],model['known_rectangles'],model['known_circles'],packet['time'])
    _,previous=old_tracker.update_rays(packet['rays'],model['known_rectangles'],model['known_circles'],packet['time'])
    assert new['center']is not None and previous['center']is not None
    state_error=max(float(np.max(abs(np.asarray(new[k])-recorded[k])))for k in ['position_lower','position_upper','velocity_lower','velocity_upper'])
    assert state_error<=1e-10,'RECORDED_NEW_ESTIMATOR_MISMATCH'
    future=np.linspace(0,2.4,121);lo,hi=future_boxes(new,future);olo,ohi=old.future_boxes(previous,future)
    truth=np.asarray(c['anchor_xy'])+np.sin((new['time']+future)*c['omega_rad_s']+c['phase_rad'])[:,None]*c['amplitude_m']*np.asarray(c['axis_xy'])
    coverage=float(np.maximum(lo-truth,truth-hi).max());old_coverage=float(np.maximum(olo-truth,truth-ohi).max())
    subset_excess=float(np.maximum(olo-lo,hi-ohi).max())
    assert coverage<=1e-7 and old_coverage<=1e-7 and subset_excess<=1e-6
    records.append({'step':packet['step'],'new_box_area_m2':float(np.prod(hi[0]-lo[0])),'old_box_area_m2':float(np.prod(ohi[0]-olo[0])),
       'new_future_box_area_mean_m2':float(np.mean(np.prod(hi-lo,axis=1))),'old_future_box_area_mean_m2':float(np.mean(np.prod(ohi-olo,axis=1))),
       'new_maximum_future_center_excess_m':coverage,'old_maximum_future_center_excess_m':old_coverage,'subset_excess_m':subset_excess,'recorded_state_error':state_error})
assert len(records)==len(packets)==len(saved),'ALL_PACKETS_MUST_BE_ACCOUNTED'
new_area=float(np.mean([r['new_box_area_m2']for r in records]));old_area=float(np.mean([r['old_box_area_m2']for r in records]))
output={'status':'PASS','packets':len(records),'new_mean_position_box_area_m2':new_area,'old_mean_position_box_area_m2':old_area,'relative_area_reduction':1-new_area/old_area,
 'maximum_new_future_center_box_excess_m':max(r['new_maximum_future_center_excess_m']for r in records),'maximum_old_future_center_box_excess_m':max(r['old_maximum_future_center_excess_m']for r in records),
 'maximum_future_subset_excess_m':max(r['subset_excess_m']for r in records),'maximum_recorded_state_error':max(r['recorded_state_error']for r in records),
 'new_tracker_sha256':hashlib.sha256((src/'motion_tracker.py').read_bytes()).hexdigest(),'simulation_steps':0,'independent_navigation_tasks':0,
 'scope':'same physically recorded packets, estimator-only ablation; cannot infer old-controller navigation outcomes from this replay'}
(root/'FIRST_HIT_PAIRED_PACKET_AUDIT.json').write_text(json.dumps(output,indent=2)+'\n')
with gzip.GzipFile(str(root/'first_hit_packet_comparison.jsonl.gz'),'wb',mtime=0)as f:
    for r in records:f.write((json.dumps(r)+'\n').encode())
print(json.dumps(output,indent=2))
