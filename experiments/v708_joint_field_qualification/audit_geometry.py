"""Independent scalar polygon/segment distances; no simulator or planning calls."""
import hashlib
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / 'runs/v708_joint_field_qualification'
PARENT = REPO / 'experiments/v706_global_field_qualification'
read = lambda p: json.loads(p.read_text())

def point_segment(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    den = dx*dx+dy*dy
    t = max(0., min(1., ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)) if den else 0.
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)

def polygon_distance(a, b):
    for poly in (a,b):
        for p,q in zip(poly, poly[1:]+poly[:1]):
            axis=(q[1]-p[1],p[0]-q[0])
            aa=[x*axis[0]+y*axis[1] for x,y in a]
            bb=[x*axis[0]+y*axis[1] for x,y in b]
            if max(aa)<min(bb) or max(bb)<min(aa):
                return min(point_segment(p,q,r) for src,dst in ((a,b),(b,a)) for p in src for q,r in zip(dst,dst[1:]+dst[:1]))
    return -1.

def scalar_clearance(pose, known, anchor):
    x,y,yaw=pose;c,s=math.cos(yaw),math.sin(yaw)
    vertices=[(x+c*dx-s*dy,y+s*dx+c*dy) for dx,dy in [(-.44,-.375),(.44,-.375),(.44,.375),(-.44,.375)]]
    result=min(5.-abs(t) for v in vertices for t in v)
    for ox,oy,hx,hy in known['known_rectangles']:
        rect=[(ox-hx,oy-hy),(ox+hx,oy-hy),(ox+hx,oy+hy),(ox-hx,oy+hy)]
        result=min(result,polygon_distance(vertices,rect))
    for ox,oy,r in [*known['known_circles'],[*anchor,.35]]:
        dx,dy=ox-x,oy-y
        lx,ly=c*dx+s*dy,-s*dx+c*dy
        signed=max(abs(lx)-.44,abs(ly)-.375)
        distance=min(point_segment((ox,oy),p,q) for p,q in zip(vertices,vertices[1:]+vertices[:1]))
        result=min(result,(-distance if signed<=0 else distance)-r)
    return result

def wrap(x):return (x+math.pi)%(2*math.pi)-math.pi

def continuous(path,known,anchor):
    lower=float('inf');rho=math.hypot(.44,.375)
    for a,b in zip(path,path[1:]):
        ds=math.hypot(b[0]-a[0],b[1]-a[1]);dy=wrap(b[2]-a[2]);n=max(1,math.ceil(ds/.01),math.ceil(abs(dy)/.01))
        for k in range(n):
            t=(k+.5)/n
            pose=[a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),a[2]+t*dy]
            lower=min(lower,scalar_clearance(pose,known,anchor)-(ds+rho*abs(dy))/n/2)
    return lower

def placement(anchor,case,known,sweep_radius=.35):
    clearance=min(5.-abs(v) for v in anchor)
    for x,y,hx,hy in known['known_rectangles']:
        clearance=min(clearance,math.hypot(max(abs(anchor[0]-x)-hx,0.),max(abs(anchor[1]-y)-hy,0.)))
    for x,y,r in known['known_circles']:clearance=min(clearance,math.dist(anchor,[x,y])-r)
    return dict(fixed_motion_envelope=abs(sweep_radius-.35)<=1e-14,known_point_clearance=clearance>=.90,
                swept_known_clearance=clearance-sweep_radius>=.55-1e-12,
                start_distance=math.dist(anchor,case['start_xy'])>=3.60,
                initial_full_sweep_outside_range=math.dist(anchor,case['start_xy'])-.35>3.,
                away_from_goal=math.dist(anchor,case['goal_xy'])>=1.4,
                protected_junction=math.hypot(max(abs(anchor[0])-.8,0.),max(abs(anchor[1])-.8,0.))-sweep_radius>=.05-1e-12)

def main():
    known=read(PARENT/'KNOWN_FIELD.json');cases=read(PARENT/'SCENE_CASES.json');details=[]
    for case in cases:
        directory=ROOT/case['id'];result=read(directory/'RESULT.json')
        if not result['eligible']:
            details.append(dict(case_id=case['id'],passed=False,checks=dict(constructor_eligible=False)));continue
        selection=result['selection'];anchor=selection['anchor_xy'];cert=selection['certificate'];path=cert['reference_path']
        grid=read(directory/'CANDIDATE_GRID.json');known_reference=read(directory/'KNOWN_REFERENCE.json')['path']
        projection=[];arc=0.
        for a,b in zip(known_reference,known_reference[1:]):
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            t=max(0.,min(1.,((anchor[0]-a[0])*dx+(anchor[1]-a[1])*dy)/(length*length))) if length else 0.
            projection.append((point_segment(anchor,a,b),arc+t*length));arc+=length
        distance,at=min(projection,key=lambda x:x[0])
        lower=continuous(path,known,anchor)
        checks=placement(anchor,case,known,selection['swept_radius_m'])
        checks.update(near_reference=distance<=.50+1e-12,reference_arc=at>=1.8 and at<=arc-1.4,
            registered_first_eligible=selection['grid_index']==grid['checked_ids'][selection['rank']] and all(not x['eligible'] for x in result['attempts'][:-1]),
            selected_grid_point=anchor==grid['points'][selection['grid_index']],
            continuous_full_body_reference=lower>=.15-1e-12,
            recorded_bound_matches=abs(lower-cert['continuous_polygonal_pose_clearance_lower_bound_m'])<=1e-10,
            goal_distance=math.dist(path[-1][:2],case['goal_xy'])<=.28,
            exact_start=path[0][:3]==[*case['start_xy'],case['yaw']],
            no_simulator=not read(ROOT/'COMPLETION.json')['simulator_imported'])
        negative=dict(anchor_at_start_rejected=not all(placement(case['start_xy'],case,known).values()),
                      shrunken_envelope_rejected=not all(placement(anchor,case,known,.20).values()))
        details.append(dict(case_id=case['id'],checks=checks,negative_controls=negative,continuous_lower_bound_m=lower,
                            passed=all(checks.values()) and all(negative.values())))
    freeze=read(Path(__file__).parent/'SOURCE_FREEZE.json')
    checks=dict(all_three=len(details)==3 and all(d['passed'] for d in details),
                frozen_inputs=all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items()),
                offline_closed=read(ROOT/'ROUND_WINDOW.json')['round_closed'],zero_integration=all(read(ROOT/'COMPLETION.json')[k]==0 for k in ['initializations','navigation_integrations','private_integrations','replay_integrations','training_updates']))
    out=dict(status='ALL_THREE_JOINT_GEOMETRY_INDEPENDENTLY_VERIFIED' if all(checks.values()) else 'JOINT_GEOMETRY_AUDIT_NOT_PASSED',checks=checks,details=details,verification_integrations=0,
             scope='Geometric full-sweep references only; actual sensing, Ackermann dynamics and arrival remain untested in the field.')
    (ROOT/'INDEPENDENT_GEOMETRY_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out));return 0 if all(checks.values()) else 1

if __name__=='__main__':raise SystemExit(main())
