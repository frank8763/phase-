"""Independent sample-ray geometry and causal packet validation; zero integration."""
from pathlib import Path
import os,sys,json,gzip,hashlib,importlib.util,time
import numpy as np
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);src=repo/'experiments/v667_dynamic_first_hit'
sys.path.insert(0,str(src))
from motion_tracker import capsule_constraints,Tracker,future_boxes
spec=importlib.util.spec_from_file_location('old_interval_tracker',repo/'experiments/v666_dynamic_dense_navigation/motion_tracker.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
rng=np.random.default_rng(667);worst=-float('inf');usable=0;started=time.monotonic()
for i in range(5000):
    origin=rng.uniform(-1,1,2).astype(np.float32)
    angle=rng.uniform(-np.pi,np.pi);direction=np.asarray([np.cos(angle),np.sin(angle)],np.float32)
    center=origin+rng.uniform(.20,2.70)*direction+rng.uniform(-.095,.095)*np.array([-direction[1],direction[0]])
    ds=np.arange(0,3.000001,.08)
    points=(origin[None,:]+ds.astype(np.float32)[:,None]*direction).astype(float)
    ids=np.flatnonzero(np.linalg.norm(points-center,axis=1)<=.10)
    if not len(ids):continue
    hit=ds[ids[0]];bound=[.06,.09][i%2];z=float(hit+rng.uniform(-bound,bound))
    ray=np.r_[origin,direction,z,bound,0.]
    A,b,count=capsule_constraints(np.asarray([ray]),[],[])
    assert count==1,'INDEPENDENT_GENERATOR_SHOULD_CERTIFY_UNKNOWN'
    excess=float(np.max(A@center-b));worst=max(worst,excess);usable+=1
    assert excess<=1e-7,('FIRST_HIT_PLANE_EXCLUDES_TRUE_CENTER',i,excess)
root=repo/'runs/v662_dynamic_sensor_diagnosis/sensor_replay_95000011/paired'
model=json.loads((root/'STATIC_PROTOCOL.json').read_text());config=json.loads((root/'DYNAMIC_PROTOCOL.json').read_text())
with gzip.open(root/'geometry_memory/sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
tracker=Tracker();baseline=old.Tracker();records=[]
for packet in packets:
    _,state=tracker.update_rays(packet['rays'],model['known_rectangles'],model['known_circles'],packet['time'])
    _,previous=baseline.update_rays(packet['rays'],model['known_rectangles'],model['known_circles'],packet['time'])
    assert state['center']is not None
    times=np.linspace(0,2.4,121);lo,hi=future_boxes(state,times)
    truth=np.asarray(config['anchor_xy'])+np.sin((state['time']+times)*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy'])
    velocity=np.cos(state['time']*config['omega_rad_s']+config['phase_rad'])*config['maximum_speed_m_s']*np.asarray(config['axis_xy'])
    excess=float(np.maximum(lo-truth,truth-hi).max());vexcess=float(np.maximum(np.asarray(state['velocity_lower'])-velocity,velocity-np.asarray(state['velocity_upper'])).max())
    assert excess<=1e-7 and vexcess<=1e-7,('PACKET_COVERAGE_FAILURE',packet['step'],excess,vexcess)
    widths=np.asarray(state['position_upper'])-state['position_lower'];old_widths=np.asarray(previous['position_upper'])-previous['position_lower']
    records.append({'step':packet['step'],'state':state,'old_state':previous,'new_position_box_area_m2':float(np.prod(widths)),'old_position_box_area_m2':float(np.prod(old_widths)),'future_max_excess_m':excess,'velocity_max_excess_m_s':vexcess})
result={'status':'PASS','independent_geometry_cases_generated':5000,'geometry_usable_first_hits':usable,'maximum_geometry_constraint_excess_m':worst,'packets':len(records),'future_times_per_packet':121,
 'maximum_future_center_box_excess_m':max(r['future_max_excess_m']for r in records),'maximum_velocity_box_excess_m_s':max(r['velocity_max_excess_m_s']for r in records),
 'old_mean_position_box_area_m2':float(np.mean([r['old_position_box_area_m2']for r in records])),'new_mean_position_box_area_m2':float(np.mean([r['new_position_box_area_m2']for r in records])),
 'tracker_sha256':hashlib.sha256((src/'motion_tracker.py').read_bytes()).hexdigest(),'elapsed_s':time.monotonic()-started,'simulation_steps':0,'navigation_tasks':0,'scope':'single-actor, bounded noise, exact localization; independent necessary-constraint check and old development packets, not population or continuous safety'}
out=repo/'runs/v667_dynamic_first_hit';out.mkdir(exist_ok=True)
(out/'OFFLINE_FIRST_HIT_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
with gzip.GzipFile(str(out/'offline_packet_comparison.jsonl.gz'),'wb',mtime=0)as f:
    for r in records:f.write((json.dumps(r)+'\n').encode())
print(json.dumps(result,indent=2))
