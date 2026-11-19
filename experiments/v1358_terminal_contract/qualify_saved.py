"""Reconstruct fixed tail inputs causally, verify new body-goal and guards."""
import gzip
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sys.path.insert(0,str(C));sys.path.insert(1,str(R/'experiments/v1357_expiry_evidence_relay'))
from causal_occupancy import CausalBall
from recovery_guard import check
from observed_route import revalidate
spec=importlib.util.spec_from_file_location('new_body_goal_search',C/'planner.py')
compiled=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiled);propose=compiled.propose


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text());records=[];forecasts=[]
    for branch,indices in [('periodic_mode0',[10]),('periodic_mode1',[10,11])]:
        raw=R/'runs/v858_nav2_verified/v1357'/(branch+'_dynamic_main')
        requests=[json.loads((raw/'planner_jobs'/('request%02d.json'%i)).read_text()) for i in indices]
        by_tick={p['native_tick']:p for p in requests};done=set()
        sensors=json.load(gzip.open(raw/'physics/SENSORS.json.gz','rt'))
        trackers={kind:CausalBall(known,forecast_kind=kind) for kind in ['HORIZON','NESTED_SWEEP']}
        for packet in sensors:
            tick=packet['native_tick']
            for kind,tracker in trackers.items():
                tracker.update(native_tick=tick,sim_time=packet['time'],center_body=[*packet['xy'],packet['yaw'],0.,0.],ranges=packet['ranges'])
                ball=tracker.occupied_ball(packet['time'])
                if ball is not None and tick%100==0 and (not forecasts or (forecasts[-1]['branch'],forecasts[-1]['kind'],forecasts[-1]['native_tick'])!=(branch,kind,tick)):
                    forecasts.append(dict(branch=branch,kind=kind,native_tick=tick,sim_time=packet['time'],center=ball[0].tolist(),radius_m=ball[1],horizon_s=1.5))
            if tick not in by_tick or tick in done:continue
            done.add(tick);req=by_tick[tick]
            for kind,tracker in trackers.items():
                ball=tracker.occupied_ball(req['sim_time'])
                path,report=propose(known,req['body'],req['goal'],ball,mode=1)
                valid,proof=revalidate(known,path,req['body'],ball,guard=.22)
                if path is not None and report['status']=='GLOBAL_GOAL_PATH':assert report['body_goal_distance_m']<=.32+1e-8
                row=dict(branch=branch,request_id=req['request_id'],kind=kind,request=dict(req,ball=[*ball[0].tolist(),ball[1]],planner_mode=1),
                    report=report,geometry=proof,geometry_passed=valid,path=None if path is None else path.tolist())
                records.append(row);print(json.dumps({k:v for k,v in row.items() if k not in ['path','request']}),flush=True)
        # Nested disks cannot introduce new occupied space into any installed
        # exact-footprint route. This is a geometric property, not dynamics proof.
        events=trackers['NESTED_SWEEP'].sweep_events
        assert events
        for event in events[1:]:
            assert np.linalg.norm(np.asarray(event['center'])-event['previous_center'])+event['radius_m']<=event['previous_radius_m']+1e-10
    old=json.loads((R/'runs/v1358_terminal_contract/ORIGINAL_REPRODUCTION.json').read_text())
    event=old['recoverable_escape_refused'];allowed,proof=check(known,event['body'],*event['requested'])
    assert allowed and proof['command_geometry_minimum_m']>=proof['current_known_clearance_m']-1e-8
    negative,neg=check(known,event['body'],-.08,0.)
    assert not negative,'TOWARD_WALL_COMMAND_NOT_REFUSED'
    (O/'SAVED_TAIL_QUALIFICATION.json').write_text(json.dumps(dict(executed=True,rows=records,old_escape_now_nondecreasing=True,
         toward_wall_negative_refused=True,all_returned_paths_dense_checked=True,models=0,physical_native=0),indent=2)+'\n')
    (O/'SAVED_FORECASTS.json').write_text(json.dumps(forecasts,separators=(',',':'))+'\n')


if __name__=='__main__':main()
