"""Profile fixed saved geometric queries only; no new controls or simulation."""
import cProfile,json,signal,sys,time,pstats,os
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=repo/'experiments/v800_spatial_nominal_global';sys.path.insert(0,str(own))
from motion_tracker import install_time_gate
from exact_footprint import pose_values
read=lambda p:json.loads(p.read_text());root=repo/'runs/v800_spatial_nominal_global'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
assert(repo/'REVIEW_PENDING').exists()and read(root/'ROUND_WINDOW.json')['round_closed']
out=repo/'runs/v800_saved_geometry_profile';assert not out.exists();out.mkdir()
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('FIXED_SAVED_GEOMETRY_120S')));signal.alarm(120)
pair=root/'main_slot01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');bounds=np.asarray(protocol['footprint_bounds'])
base=dict(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
states={s['step']:s for s in map(json.loads,(cell/'motion_estimate.jsonl').open())}
calls=[s for s in map(json.loads,(cell/'control_decisions.jsonl').open())if s['stage']=='NOMINAL'and s['candidate_role']=='ORDINARY']
chosen=sorted(set([0,len(calls)//4,len(calls)//2,3*len(calls)//4,len(calls)-1]));results=[]
prof=cProfile.Profile();prof.enable()
for index in chosen:
    call=calls[index];c=call['candidates'][0];z=np.load(cell/'nominal_forecasts'/c['nominal_saved_forecast'])
    begin=time.perf_counter();field=SimpleNamespace(**base);install_time_gate(field,states[call['step']],'predictive',protocol['known_circles'],protocol['known_rectangles']);construct_s=time.perf_counter()-begin
    begin=time.perf_counter();values=field.trajectory_values(z['poses'],.01);risk_s=time.perf_counter()-begin
    begin=time.perf_counter();static=pose_values(SimpleNamespace(**base),z['poses']);static_s=time.perf_counter()-begin
    assert abs(float(values.min())-c['minimum_clearance_m'])<=1e-8
    results.append(dict(step=call['step'],saved_file=c['nominal_saved_forecast'],poses=len(z['poses']),field_setup_s=construct_s,causal_geometry_s=risk_s,static_geometry_s=static_s,minimum_causal_m=float(values.min()),minimum_static_m=float(static.min())))
prof.disable();prof.dump_stats(str(out/'fixed_saved_geometry.prof'))
with(out/'PROFILE.txt').open('w')as stream:pstats.Stats(prof,stream=stream).sort_stats('cumulative').print_stats(30)
summary=dict(status='FIVE_FIXED_SAVED_GEOMETRY_QUERIES_PROFILED',queries=results,model_initializations=0,integrations=0,new_predictions=0,new_actions=0,
    limits='cProfile adds overhead and does not time native rollout/whole online run; these fixed saved geometry timings are not a whole-runtime causal decomposition or a real-time claim.')
(out/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n');signal.alarm(0);print(json.dumps(summary))
