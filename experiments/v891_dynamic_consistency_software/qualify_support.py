"""Saved complete causal scan loop; finite coverage is an evaluator, never input."""
import gzip,json,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v891_dynamic_consistency_software'
sys.path[:0]=[str(R/'experiments/v887_exact_lidar_software'),str(R/'experiments/v881_timing_accounting_continuation')]
from exact_lidar import get_lidar_features
from support_envelope import SupportEnvelope,polygon,raster_support,NORMALS
from reproduce import pose,footprint,intersects
from planner_proxy import terminal_goal

def main():
    known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    journal=json.loads(gzip.decompress((O/'inputs/MOTION_ENVELOPE.json.gz').read_bytes()))
    tracker=SupportEnvelope(known,get_lidar_features);records=[];times=[]
    trace=np.load(O/'inputs/physics__NATIVE_TRACE.npz');tick_to_row={round(float(t)*100):i for i,t in enumerate(trace['time'])}
    covered=0;future_covered=0
    failure=json.loads((R/'records/nav2_v890_20261108/FAILURE_ANALYSIS.json').read_text())
    comparison_time=failure['last_published_envelope']['forecast_sim_time'];comparison_support=None
    for packet in journal['observations']:
        t=time.perf_counter();state=tracker.update(packet);times.append(time.perf_counter()-t)
        if tracker.support is None:continue
        center=trace['mocap_pos'][tick_to_row[packet['native_tick']],0,:2]
        assert np.max(NORMALS@center-tracker.support)<=1e-8,'POSITION_COVERAGE'
        covered+=1;forecast=tracker.forecast(packet['time'])
        for t2 in np.arange(packet['time'],min(packet['time']+1.5,trace['time'][-1])+1e-7,.05):
            j=int(np.argmin(abs(trace['time']-t2)))
            c=trace['mocap_pos'][j,0,:2]
            assert np.max(NORMALS@c+.1-forecast)<=1e-8,'FINITE_FUTURE_ACTOR_COVERAGE'
            future_covered+=1
        records.append(dict(state=state,forecast_support=forecast.tolist()))
        if packet['time']<=comparison_time:comparison_support=tracker.forecast(comparison_time).copy()
    final=comparison_support;assert final is not None
    cfg=json.loads((R/'experiments/v890_motion_envelope_dynamic/A_motion.yaml').read_text())
    vertices=json.loads(cfg['global_costmap']['global_costmap']['ros__parameters']['footprint'])
    goal,choice=terminal_goal(pose(4.,-2.),known)
    new_occupied=intersects(footprint(goal,vertices),polygon(final))
    oldrect=failure['last_published_envelope']['rectangle']
    poly=polygon(final);other=np.roll(poly,-1,axis=0);area=abs((poly[:,0]*other[:,1]-poly[:,1]*other[:,0]).sum())/2
    proof=dict(passed=True,models=0,integrations=0,saved_observations=len(journal['observations']),tracked_centres_covered=covered,finite_future_points_covered=future_covered,comparison_forecast_sim_time=comparison_time,old_rectangle_area=(oldrect[2]-oldrect[0])*(oldrect[3]-oldrect[1]),new_forecast_area=float(area),new_forecast_polygon=poly.tolist(),same_old_terminal_still_occupied=new_occupied,old_terminal=choice,update_p50_s=float(np.median(times)),update_p95_s=float(np.quantile(times,.95)),final_support=final.tolist(),scope='Saved-input position/finite horizon coverage only, no new sensing or physical navigation')
    with gzip.open(O/'SUPPORT_STATES.json.gz','wt')as f:json.dump(records,f)
    (O/'SUPPORT_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof),flush=True)
if __name__=='__main__':main()
