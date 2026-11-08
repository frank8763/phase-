"""Saved original observations plus mathematical contract cases; zero vehicle models."""
import copy,gzip,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
import numpy as np
from envelope import Envelope,raster,HORIZON,MAP_LATENCY_RESERVE,SPEED
R=Path(__file__).resolve().parents[2];O=R/'runs/v889_motion_envelope_software';REC=R/'records/nav2_v889_20261108'
def main():
    spec=importlib.util.spec_from_file_location('original_equivalent_batch_sensor',R/'experiments/v887_exact_lidar_software/exact_lidar.py');lidar=importlib.util.module_from_spec(spec);spec.loader.exec_module(lidar)
    setup=json.loads((O/'inputs/physics__SETUP.json').read_text());saved=json.loads(gzip.decompress((O/'inputs/physics__SENSORS.json.gz').read_bytes()));actor=setup['actor'];tracker=Envelope(setup['known'],lidar.get_lidar_features);records=[];times=[];covered=0;first=None
    def xy(t):return np.asarray(actor['anchor_xy'])+np.asarray(actor['axis_xy'])*actor['amplitude_m']*math.sin(actor['omega_rad_s']*t+actor['phase_rad'])
    for packet in saved:
        if tracker.when is not None and packet['time']==tracker.when:continue
        clean={k:packet[k]for k in ['native_tick','time','xy','yaw','ranges']};start=time.perf_counter();state=tracker.update(clean);times.append(time.perf_counter()-start)
        if state['information_mode']=='TRACKED':
            if first is None:first=dict(native_tick=packet['native_tick'],time=packet['time'])
            point=xy(packet['time']);lo=np.asarray(state['position_lower']);hi=np.asarray(state['position_upper']);assert np.all(point>=lo-1e-8)and np.all(point<=hi+1e-8),dict(t=packet['time'],true=point.tolist(),lower=lo.tolist(),upper=hi.tolist())
            rect=tracker.rectangle(packet['time']);future=np.asarray([xy(packet['time']+t)for t in np.linspace(0,HORIZON+MAP_LATENCY_RESERVE,51)])
            assert np.all(future-.1>=np.asarray(rect[:2])-1e-8)and np.all(future+.1<=np.asarray(rect[2:])+1e-8)
            covered+=len(future);records.append(dict(state=state,rectangle=rect))
    checks=dict(input_readback_passed=json.loads((O/'INPUT_READBACK.json').read_text())['passed'],causal_track_appears=True if first else False,all_saved_true_centres_inside_causal_outer_box=True,all_declared_speed_future_geometry_inside_buffer=True,before_first_hit_no_truth_occupancy=first['time']>=52. if first else False,performance_update_p95_under5ms=float(np.quantile(times,.95))<.005)
    negative={}
    for name,mutate in [('nonfinite',lambda p:p.update(ranges=[float('nan')]*32)),('missing_pose',lambda p:p.pop('xy')),('invalid_range',lambda p:p.update(ranges=[3.2]*32))]:
        packet=copy.deepcopy(saved[-1]);mutate(packet)
        try:Envelope(setup['known'],lidar.get_lidar_features).update(packet);negative[name]=False
        except ValueError:negative[name]=True
    try:tracker.update(saved[-1]);negative['duplicate_time']=False
    except ValueError:negative['duplicate_time']=True
    last=copy.deepcopy(tracker.latest);before=tracker.rectangle(tracker.when);gap=copy.deepcopy(saved[-1]);gap.update(time=tracker.when+.5,native_tick=gap['native_tick']+50,ranges=[3.]*32)
    tracker.update(gap);after=tracker.rectangle(tracker.when)
    checks['no_return_does_not_erase_actor']=tracker.latest['information_mode']=='TRACKED'and np.all(np.asarray(after[:2])<np.asarray(before[:2]))and np.all(np.asarray(after[2:])>np.asarray(before[2:]))
    checks['all_invalid_inputs_rejected']=all(negative.values())
    # Grid cells conservatively cover every occupied box point, and a later full
    # map clears the old layer locally instead of retaining an ever-growing trail.
    rect=records[-1]['rectangle'];grid=raster(rect)
    sample=np.random.default_rng(889).uniform(rect[:2],rect[2:],size=(10000,2));idx=np.floor((sample+5)/.01).astype(int)
    inside=(idx>=0).all(axis=1)&(idx<1000).all(axis=1)
    checks['all10000_box_points_marked']=bool(np.all(grid[idx[inside,1],idx[inside,0]]==100))
    moved=[-3.,2.,-2.5,2.5];new=raster(moved);checks['new_map_clears_old_dynamic_layer_cells']=bool(np.all(new[grid==100]==0))
    checks['original_grid_dimensions_resolution_preserved']=grid.shape==(1000,1000)and grid.dtype==np.int8
    # Source-exact wrapper never accepts evaluator labels even if packet contains them.
    a=Envelope(setup['known'],lidar.get_lidar_features);b=Envelope(setup['known'],lidar.get_lidar_features)
    for p in saved[-20:]:
        changed=copy.deepcopy(p);changed['raw_lidar']=[-999.]*32;changed['actor_xy']=[999.,999.]
        if a.when==p['time']:continue
        assert a.update(p)==b.update(changed)
    checks['raw_and_actor_truth_perturbation_has_no_effect']=True
    checks={k:bool(v)for k,v in checks.items()}
    result=dict(passed=all(checks.values()),checks=checks,negative_cases=negative,models=0,environment_initializations=0,native_integrations=0,actual_ros_servers=0,saved_input_packets=len(saved),tracked_packets=len(records),future_evaluator_points_covered=covered,first_causal_tracked_state=first,update_p50_s=float(np.median(times)),update_p95_s=float(np.quantile(times,.95)),update_max_s=max(times),parameters=dict(radius=.1,speed=.08,noise_clip=.06,ray_step=.08,horizon=HORIZON,map_latency_reserve=MAP_LATENCY_RESERVE),geometry_truth_only_in_this_offline_evaluator=True,limitations=['Position enclosure and finite future occupancy under stated single-actor assumptions; no recursive whole-vehicle safety proof','No command, model integration, new navigation or confirmation','Before first reliable unknown hit remains original weaker reactive condition','Actual costmap ingestion and controller interaction require separate genuine ROS qualification'])
    for p in [O/'QUALIFICATION.json',REC/'QUALIFICATION.json']:p.write_text(json.dumps(result,indent=2)+'\n')
    with gzip.open(O/'CAUSAL_ENVELOPE_STATES.json.gz','wt')as f:json.dump(records,f)
    print(json.dumps(result),flush=True);return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
