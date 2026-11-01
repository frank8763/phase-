"""Fixed recorded-input union coverage check, evaluator truth isolated from estimator."""
from pathlib import Path
import os,sys,json,gzip,time,hashlib
import numpy as np
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);sys.path.insert(0,str(repo/'experiments/v670_dynamic_empty_samples'))
from motion_tracker import Tracker,future_boxes
from union_belief import build_cells,future_cells
started=time.monotonic();records=[];summaries=[];inputs={}
for relative in ['v662_dynamic_sensor_diagnosis/sensor_replay_95000011/paired','v667_dynamic_first_hit/dev36_95000011_firsthit/paired','v669_dynamic_reserved_recovery/dev37_95000011_reserve/paired','v670_dynamic_empty_samples/dev38_95000011_empty/paired']:
    p=repo/'runs'/relative;model=json.loads((p/'STATIC_PROTOCOL.json').read_text());config=json.loads((p/'DYNAMIC_PROTOCOL.json').read_text());file=p/'geometry_memory/sensor_packets.jsonl.gz';inputs[str(file.relative_to(repo))]=hashlib.sha256(file.read_bytes()).hexdigest()
    with gzip.open(file,'rt')as f:packets=[json.loads(s)for s in f]
    tracker=Tracker();stats=[]
    for packet in packets:
        _,state=tracker.update_rays(packet['rays'],model['known_rectangles'],model['known_circles'],packet['time']);cells,metadata=build_cells(tracker.bounds,packet['rays'],model['known_rectangles'],model['known_circles'],packet['time'],tracker.frames)
        times=np.linspace(0,3.28,165);low,high=future_cells(cells,times);true=np.asarray(config['anchor_xy'])+np.sin((packet['time']+times)*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy'])
        # A joint cell containing current p,v is needed, not unrelated marginals.
        actual_v=np.cos(packet['time']*config['omega_rad_s']+config['phase_rad'])*config['maximum_speed_m_s']*np.asarray(config['axis_xy']);arr=np.asarray(cells);pv=np.maximum.reduce([arr[:,0]-true[0],true[0]-arr[:,1],arr[:,2]-actual_v,actual_v-arr[:,3]]).max(axis=1).min()
        excess=np.maximum(low-true[:,None,:],true[:,None,:]-high).max(axis=2).min(axis=1).max();assert max(pv,excess)<=1e-7,(relative,packet['step'],pv,excess)
        stats.append(metadata['cover_rectangles']);records.append({'dataset':relative,'step':packet['step'],'state':state,'cells':cells,'metadata':metadata,'joint_current_state_excess':float(pv),'maximum_future_union_excess_m':float(excess)})
    summaries.append({'dataset':relative,'frames':len(packets),'mean_cover_rectangles':float(np.mean(stats)),'maximum_cover_rectangles':max(stats)})
root=repo/'runs/v671_dynamic_consistency_diagnosis'
with gzip.GzipFile(str(root/'validated_union_states.jsonl.gz'),'wb',mtime=0)as f:
    for r in records:f.write((json.dumps(r)+'\n').encode())
result={'status':'PASS','frames':len(records),'future_grid_per_frame':165,'maximum_joint_current_state_excess':max(r['joint_current_state_excess']for r in records),'maximum_future_union_excess_m':max(r['maximum_future_union_excess_m']for r in records),'datasets':summaries,'elapsed_s':time.monotonic()-started,'navigation_tasks':0,'simulation_integrations':0,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in Path(__file__).parent.glob('*.py')},'input_sha256':inputs}
(root/'UNION_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['source_sha256','input_sha256']},indent=2))
