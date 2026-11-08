"""Closed actual map/sensor diagnostics; no navigation or model initialization."""
import gzip,json,math
from collections import Counter
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v894_wait_map_validation';REC=R/'records/nav2_v894_20261108'
def main():
    assert json.loads((O/'COMPLETION.json').read_text())['closed']
    p=R/'runs/v858_nav2_verified/v894/main_we';journal=json.loads(gzip.decompress((p/'MOTION_ENVELOPE.json.gz').read_bytes()));n=json.loads((p/'RESULT.json').read_text());ros=json.loads((p/'ROS_RESULT.json').read_text());routes=json.loads((p/'ROUTER_REQUESTS.json').read_text());states=journal['states'];tracked=[s for s in states if s['last_hit_time']is not None]
    gaps=[(s['time']-s['last_hit_time'],s['time'])for s in tracked]
    result=dict(status='NOT_PASSED',successful_periodic_routes_after_detection=8,max_certified_return_gap_s=max(gaps)[0],gap_ends_at_sim_s=max(gaps)[1],last_return_gap_s=tracked[-1]['time']-tracked[-1]['last_hit_time'],last_causal_state=states[-1],last_router_request=routes[-1],smac_failure_counts=dict(Counter(str(x.get('smac_error_code'))for x in routes if not x['passed'])),virtual205_waits=sum(x.get('returned_error_code')==208 for x in routes),terminal_region_waits=sum(x.get('wait_reason')=='DYNAMIC_TERMINAL_BLOCKED'for x in routes),action_status=ros.get('action_status'),action_error_code=ros.get('action_error_code'),actual_postdetection_path_m=n['actual_travel_after_detection_m'],models=0,integrations=0,scope='Observed sparse-return gaps and actual saved master maps; no uniqueness claim about internal Smac cause')
    import sys
    sys.path.insert(0,str(R/'experiments/v891_dynamic_consistency_software'))
    from support_envelope import polygon,NORMALS
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Polygon
    cfg=json.loads((R/'experiments/v894_wait_map_validation/A_motion.yaml').read_text());foot=np.asarray(json.loads(cfg['global_costmap']['global_costmap']['ros__parameters']['footprint']))
    snapshots=json.loads((p/'COSTMAP_SNAPSHOT_INDEX.json').read_text());global_rows=[x for x in snapshots if x['kind']=='global_costmap']
    colors=plt.cm.Greys(np.linspace(0,1,256));colors[255]=[.65,.4,.85,1.];palette=ListedColormap(colors)
    fig,axes=plt.subplots(1,4,figsize=(15,4),constrained_layout=True)
    evidence=[]
    for ax,target in zip(axes,[52.,60.,68.,75.]):
        row=min(global_rows,key=lambda x:abs(x['at']-n['armed_at']-target));sim=row['at']-n['armed_at']
        with np.load(p/row['path'])as z:data=z['data'].reshape(row['height'],row['width'])
        ax.imshow(data,origin='lower',extent=[-5.,5.,-5.,5.],cmap=palette,vmin=0,vmax=255)
        publication=min(journal['publications'],key=lambda x:abs(x['at']-row['at']))
        if publication['forecast_support']is not None:ax.add_patch(Polygon(polygon(publication['forecast_support']),fill=False,edgecolor='tab:red',linewidth=1.5))
        rr=min([x for x in routes if 'original_start'in x],key=lambda x:abs(x['started_monotonic']-row['at']));x,y,a=rr['original_start'];c,s=math.cos(a),math.sin(a);body=foot@np.asarray([[c,s],[-s,c]])+[x,y]
        ax.add_patch(Polygon(body,fill=False,edgecolor='tab:blue'));ax.scatter(4.,-2.,marker='*',color='tab:green',s=60)
        state=min(states,key=lambda x:abs(x['time']-sim));age=None if state['last_hit_time']is None else state['time']-state['last_hit_time']
        ax.set(xlim=(0.,4.8),ylim=(-3.5,.1),aspect='equal',title=f't≈{sim:.1f}s; return age≈{age:.2f}s\nUnknown255: {np.mean(data==255):.0%} (purple)',xlabel='x(m)')
        evidence.append(dict(snapshot=row,approximate_sim_time_from_wall_pacing_s=sim,nearest_causal_return_age_s=age,nearest_router_pose=rr['original_start'],forecast_polygon_is_nearest_published_not_claimed_exact_ingested_layer=True))
    fig.savefig(REC/'ACTUAL_GLOBAL_MAP_DIAGNOSIS.png',dpi=150);plt.close(fig)
    result['global_map_diagnostic_frames']=evidence
    counts=[]
    for row in global_rows:
        with np.load(p/row['path'])as z:data=z['data']
        counts.append(dict(at=row['at'],unknown_cells=int(np.sum(data==255)),all_cells=len(data)))
    result['global_full_snapshots']=len(counts);result['all_unknown_global_snapshots']=sum(x['unknown_cells']==x['all_cells']for x in counts);result['global_snapshot_unknown_counts']=counts
    (REC/'FAILURE_ANALYSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ['max_certified_return_gap_s','last_return_gap_s','successful_periodic_routes_after_detection','virtual205_waits','terminal_region_waits','action_error_code']}))
if __name__=='__main__':main()
