"""Separate polygon geometry witness, no online collision routine calls."""
import importlib.util,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v1022_independent_polygons',R/'experiments/v938_rpccr_recovery_segments/independent_geometry.py');geo=importlib.util.module_from_spec(s);s.loader.exec_module(geo)

def geometry_witness(states,known,prior,required):
    states=np.asarray(states,float);assert states.ndim==2 and states.shape[1]==8 and np.isfinite(states).all()
    assert abs(states[:,3]).max()<=.13 and abs(states[:,5]).max()<=.16
    # The original body envelope is .13 forward, .16 yaw; also bound the
    # predictor's explicit lateral velocity rather than silently omitting it.
    lateral=float(abs(states[:,4]).max());assert lateral<=.03
    stride=5;indices=np.unique(np.r_[np.arange(0,len(states),stride),len(states)-1])
    rectangles=[np.array([x,y])+geo.SIGNS*np.array([hx,hy])for x,y,hx,hy in known['known_rectangles']]
    obstacle=None if prior is None else geo.enclosure(prior)
    minimum=math.inf
    for index in indices:
        x,y,yaw=states[index,:3];c,s=math.cos(yaw),math.sin(yaw);rotation=np.array([[c,-s],[s,c]])
        body=geo.SIGNS*geo.HALF@rotation.T+[x,y];value=float(np.min(5-abs(body)))
        for rectangle in rectangles:value=min(value,geo.polygon_distance(body,rectangle))
        for cx,cy,radius in known['known_circles']:
            local=np.array([cx-x,cy-y])@rotation;value=min(value,float(np.linalg.norm(np.maximum(abs(local)-geo.HALF,0)))-radius)
        if obstacle is not None:value=min(value,geo.polygon_distance(body,obstacle)-.1-2e-6)
        minimum=min(minimum,value)
    gap=.5*stride*.01*(math.hypot(.13,lateral)+math.hypot(.44,.375)*.16)
    lower=minimum-gap
    return dict(passed=lower>=required,samples=len(indices),minimum_sample_raw_m=minimum,whole_path_lower_m=lower,
        interpolation_reserve_m=gap,required_raw_m=required,maximum_predicted_lateral_m_s=lateral,
        models=0,integrations=0,independent_geometry_only=True,physical_ready=False)

if __name__=='__main__':
    import json,time
    out=R/'runs/v1022_full_route_planner';plan=json.loads((out/'ns_initial.input_route.json').read_text());setup=json.loads((R/'runs/v858_nav2_verified/v1020/PREFLIGHTS/ns/SETUP.json').read_text());start=time.monotonic()
    result=geometry_witness(plan['state_path'],setup['known'],None,plan['required_raw_clearance_m']);result['wall_s']=time.monotonic()-start
    (out/'INDEPENDENT_STATIC_GEOMETRY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
