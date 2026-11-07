"""Warm existing decoder cache on five fixed saved queries; no new control."""
import json,os,signal,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo/'experiments/v800_spatial_nominal_global'))
from motion_tracker import install_time_gate
from renewal_state import _decode
read=lambda p:json.loads(p.read_text());pair=repo/'runs/v800_spatial_nominal_global/main_slot01/paired';cell=pair/'geometry_memory'
assert(repo/'REVIEW_PENDING').exists();out=repo/'runs/v800_saved_geometry_warm_profile';assert not out.exists();out.mkdir()
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('FIXED_WARM_QUERY_120S')));signal.alarm(120)
protocol=read(pair/'STATIC_PROTOCOL.json');bounds=np.asarray(protocol['footprint_bounds']);states={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').open())}
calls=[x for x in map(json.loads,(cell/'control_decisions.jsonl').open())if x['stage']=='NOMINAL'and x['candidate_role']=='ORDINARY']
result=[]
for i in [0,50,100,150,199]:
    call=calls[i];c=call['candidates'][0];z=np.load(cell/'nominal_forecasts'/c['nominal_saved_forecast'])
    f=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    install_time_gate(f,states[i],'predictive',protocol['known_circles'],protocol['known_rectangles']);times=[];before=_decode.cache_info()._asdict()
    for repeat in range(3):
        start=time.perf_counter();values=f.trajectory_values(z['poses'],.01);times.append(time.perf_counter()-start)
        assert abs(float(values.min())-c['minimum_clearance_m'])<=1e-8
    after=_decode.cache_info()._asdict();assert after['hits']-before['hits']>=2
    result.append(dict(step=i,seconds=times,existing_cache_hits=after['hits']-before['hits'],existing_cache_misses=after['misses']-before['misses']))
summary=dict(status='EXISTING_DECODER_CACHE_REUSE_VERIFIED',queries=result,new_models=0,new_integrations=0,new_actions=0,
    interpretation='The original LRU decoder already reuses each current-state domain. Cold five-state profile must not be extrapolated as a decode miss for every online candidate. Warm timings still include geometric body queries; these are fixed-query timings, not a whole-run attribution.')
(out/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n');signal.alarm(0);print(json.dumps(summary))
