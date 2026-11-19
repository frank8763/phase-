"""Saved real packet conditioning, then fixed failed-state planner checks."""
import gzip
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sys.path.insert(0,str(C));sys.path.insert(1,str(R/'experiments/v1354_fast_stamped_pipeline'))
from causal_occupancy import CausalBall
from observed_route import revalidate,nominal_clearance
spec=importlib.util.spec_from_file_location('phase_fast',R/'experiments/v1350_bounded_complete_search/planner.py')
fast=importlib.util.module_from_spec(spec);spec.loader.exec_module(fast)


def main():
    O.mkdir(exist_ok=True);os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    raw=R/'runs/v858_nav2_verified/v1354/rpp_fast_stamped_dynamic_main'
    known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    sensors=json.load(gzip.open(raw/'physics/SENSORS.json.gz','rt'))
    requests=[json.loads((raw/'planner_jobs'/('request%02d.json'%i)).read_text()) for i in [1,4,11]]
    trackers={name:CausalBall(known,model=name) for name in ['EXCURSION','PERIODIC']}
    requests_by_tick={x['native_tick']:x for x in requests};rows=[];future_rows=[];processed_requests=set();start=time.monotonic()
    # Entire sequence is causal: policy receives only recorded sensor whitelist.
    for packet in sensors:
        tick=packet['native_tick'];body=[*packet['xy'],packet['yaw'],0.,0.]
        for name,tracker in trackers.items():
            tracker.update(native_tick=tick,sim_time=packet['time'],center_body=body,ranges=packet['ranges'])
            ball=tracker.occupied_ball(packet['time'])
            if ball is not None and (tick%50==0 or tick in requests_by_tick):
                future_rows.append(dict(model=name,native_tick=tick,sim_time=packet['time'],center=ball[0].tolist(),radius_m=ball[1],horizon_s=1.5))
        if tick not in requests_by_tick or tick in processed_requests:continue
        processed_requests.add(tick)
        req=requests_by_tick[tick]
        for name,tracker in trackers.items():
            ball=tracker.occupied_ball(req['sim_time']);ball_data=[*ball[0].tolist(),ball[1]]
            for mode in ([0] if name=='EXCURSION' else [0,1]):
                path,report=fast.propose(req['known'],req['body'],req['goal'],ball,guard=.22,mode=mode)
                valid,proof=revalidate(req['known'],path,req['body'],ball,guard=.22)
                row=dict(saved_request=req['request_id'],model=name,planner_mode=mode,ball=ball_data,
                    current_footprint_clearance_m=nominal_clearance(req['body'],*ball),
                    path_admitted=valid,report=report,snapshot_dense_validation=proof,
                    path=None if path is None else path.tolist())
                rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='path'}),flush=True)
    result=dict(executed=True,rows=rows,models=0,physical_native=0,wall_s=time.monotonic()-start,
          source='original saved real corrupted sensor packets only; actor truth absent from predictor',
          stronger_prior_than_v1354=True)
    (O/'SAVED_PREDICTOR_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    (O/'FORECAST_FIXTURES.json').write_text(json.dumps(future_rows,separators=(',',':'))+'\n')
    for name,tracker in trackers.items():
        (O/('FINAL_'+name+'_SNAPSHOT.json')).write_text(json.dumps(tracker.snapshot(),indent=2)+'\n')


if __name__=='__main__':main()
