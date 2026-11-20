"""Saved positive/broken frames and exact rapid-brake metadata regression."""
import copy
import gzip
import json
from pathlib import Path
from reproduce import NoModel
from coherent_scan import needs_sample,validate_frame

R=Path(__file__).resolve().parents[2];O=R/'runs/v1371_overnight_retrospective';D=R/'runs/v858_nav2_verified/v1370/rpp_local_horizon_m1_s01_main'

def main():
    rows=json.loads((D/'APPLIED_JOURNAL.json').read_text())
    with gzip.open(D/'physics/SENSORS.json.gz','rt') as f:sensors=json.load(f)
    scan=next(s for s in sensors if s['native_tick']==41390);body=rows[41390]['body']
    assert validate_frame(scan,41390,413.9,body)
    bads=[]
    for name in ['old_sensor','forged_tick','forged_tick_and_time','future_sensor']:
        candidate=copy.deepcopy(scan)
        if name!='old_sensor':candidate['native_tick']=41410 if name!='future_sensor' else 41415
        if name=='forged_tick_and_time':candidate['time']=414.1
        try:validate_frame(candidate,41410,414.1,rows[41410]['body'])
        except AssertionError as e:bads.append(dict(case=name,rejected=True,reason=str(e)))
        else:raise AssertionError('BROKEN_FRAME_ACCEPTED '+name)
    original=json.loads((O/'REPRODUCTION.json').read_text());cached=None;at=0.;packets=[]
    for e in original['metadata_cache_pattern']:
        tick=e['packet_native'];now=e['wall_offset']
        if needs_sample(cached,tick,at,now):cached=tick;at=now
        assert cached==tick;packets.append(dict(body_native=tick,sensor_native=cached))
    assert not needs_sample(41410,41410,1.,1.001) and needs_sample(41410,41410,1.,1.041)
    proof=dict(passed=True,saved_frame_positive=True,broken_frame_negatives=bads,rapid_expiry_brake_metadata_frames=packets,
        same_tick_reuse_and_wall_refresh_passed=True,new_contract_prototype_only=True,installed_in_physical_runner=False,
        old_missing_scan_not_recreated_or_fabricated=True,models=0,physical_native=0,replay_native=0)
    (O/'FRAME_CONTRACT_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))

if __name__=='__main__':main()
