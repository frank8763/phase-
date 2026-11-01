"""Independent synthetic and fixed-packet evaluator; zero robot integration."""
import os,sys,time,json,gzip,hashlib,importlib.util
from pathlib import Path
import numpy as np
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);src=Path(__file__).resolve().parent;sys.path.insert(0,str(src))
from empty_sample_contract import contract_box,empty_points
from motion_tracker import Tracker,future_boxes
spec=importlib.util.spec_from_file_location('baseline_tracker',repo/'experiments/v669_dynamic_reserved_recovery/motion_tracker.py');baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
root=repo/'runs/v670_dynamic_empty_samples';started=time.monotonic();rng=np.random.default_rng(67001);geometry=[]
for i in range(5000):
    o=rng.uniform(-2,2,2).astype(np.float32);a=rng.uniform(-np.pi,np.pi);d=np.asarray([np.cos(a),np.sin(a)],np.float32)
    center=o+rng.uniform(.3,2.5)*d+rng.uniform(-.075,.075)*np.array([-d[1],d[0]])
    ds=np.arange(0,3.000001,.08);points=(o[None,:]+ds.astype(np.float32)[:,None]*d).astype(float)
    hits=np.flatnonzero(np.linalg.norm(points-center,axis=1)<=.10);assert len(hits)
    b=[.06,.09][i%2];z=float(ds[hits[0]]+rng.uniform(-b,b));rays=np.asarray([np.r_[o,d,z,b,.02]])
    bounds=np.stack([center-rng.uniform(.005,.25,2),center+rng.uniform(.005,.25,2)],axis=1)
    reduced,stats=contract_box(bounds,rays);excess=float(np.maximum(reduced[:,0]-center,center-reduced[:,1]).max())
    assert excess<=1e-9,('GEOMETRY_EXCLUDED_TRUTH',i,excess)
    geometry.append(excess)
datasets=[('v662_dynamic_sensor_diagnosis/sensor_replay_95000011/paired',264),('v666_dynamic_dense_navigation/dev35_95000011_dense/paired',765),('v667_dynamic_first_hit/dev36_95000011_firsthit/paired',210),('v669_dynamic_reserved_recovery/dev37_95000011_reserve/paired',227)]
summary=[];details=[];inputs={}
for relative,expected in datasets:
    path=repo/'runs'/relative;model=json.loads((path/'STATIC_PROTOCOL.json').read_text());config=json.loads((path/'DYNAMIC_PROTOCOL.json').read_text())
    packetfile=path/'geometry_memory/sensor_packets.jsonl.gz';inputs[str(packetfile.relative_to(repo))]=hashlib.sha256(packetfile.read_bytes()).hexdigest()
    with gzip.open(packetfile,'rt')as f:packets=[json.loads(s)for s in f]
    assert len(packets)==expected
    new=Tracker();old=baseline.Tracker();records=[]
    for packet in packets:
        _,s=new.update_rays(packet['rays'],model['known_rectangles'],model['known_circles'],packet['time'])
        _,previous=old.update_rays(packet['rays'],model['known_rectangles'],model['known_circles'],packet['time'])
        tt=np.linspace(0,3.28,165);lo,hi=future_boxes(s,tt)
        truth=np.asarray(config['anchor_xy'])+np.sin((s['time']+tt)*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy'])
        velocity=np.cos(s['time']*config['omega_rad_s']+config['phase_rad'])*config['maximum_speed_m_s']*np.asarray(config['axis_xy'])
        excess=float(np.maximum(lo-truth,truth-hi).max());vexcess=float(np.maximum(np.asarray(s['velocity_lower'])-velocity,velocity-np.asarray(s['velocity_upper'])).max())
        assert excess<=1e-7 and vexcess<=1e-7,('OFFLINE_PACKET_COVERAGE_FAILURE',relative,packet['step'],excess,vexcess)
        area=lambda x:float(np.prod(np.asarray(x['position_upper'])-x['position_lower']))
        record={'dataset':relative,'step':packet['step'],'new_state':s,'old_state':previous,'new_area_m2':area(s),'old_area_m2':area(previous),'maximum_future_excess_m':excess,'maximum_velocity_excess_m_s':vexcess};records.append(record);details.append(record)
    n=float(np.mean([r['new_area_m2']for r in records]));o=float(np.mean([r['old_area_m2']for r in records]));summary.append({'dataset':relative,'frames':len(records),'old_mean_area_m2':o,'new_mean_area_m2':n,'mean_area_reduction_fraction':1-n/o,'terminal_old_area_m2':records[-1]['old_area_m2'],'terminal_new_area_m2':records[-1]['new_area_m2'],'maximum_future_excess_m':max(r['maximum_future_excess_m']for r in records),'maximum_velocity_excess_m_s':max(r['maximum_velocity_excess_m_s']for r in records),'frames_with_deleted_continuous_cells':sum(r['new_state']['empty_sample_contract']['removed_cells']>0 for r in records)})
with gzip.GzipFile(str(root/'offline_packet_comparison.jsonl.gz'),'wb',mtime=0)as f:
    for r in details:f.write((json.dumps(r)+'\n').encode())
result={'status':'PASS','geometry_cases_with_first_hit':len(geometry),'maximum_geometry_truth_excess_m':max(geometry),'datasets':summary,'frames':len(details),'future_times_per_frame':165,'simulation_integrations':0,'navigation_tasks':0,'elapsed_s':time.monotonic()-started,'input_sha256':inputs,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in src.glob('*.py')},'scope':'samplewise geometry and recorded same-packet ablation; continuous-cell exclusion rule, not full floating-point certification or navigation acceptance'}
(root/'OFFLINE_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['source_sha256','input_sha256']},indent=2))
