"""One exposed nominal geometry search and independent sampled polygon check."""
import copy,datetime,fcntl,hashlib,json,math,os,signal,struct,time,traceback
from pathlib import Path
import numpy as np
from nominal_frontend import NominalFrontend,local_window,rear_goal,SEARCH,GEOMETRY
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
assert os.sched_getaffinity(0)=={4}and not(S/'NOMINAL_FRONTEND_GEOMETRY_ONCE.json').exists()
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('NOMINAL_GEOMETRY120S')));signal.alarm(120)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
locks=[]
for name in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
    h=(R/name).open();fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(h)
assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
assert not Path('/proc/113868').exists()
allocated=lambda p:sum(f.stat().st_blocks*512 for f in p.rglob('*')if f.is_file())
assert allocated(S)+allocated(R/'runs/v2183_lossless_capture_stream')+96*1024<1024**2
inputs=[R/SEARCH,R/GEOMETRY,R/'experiments/v855_renewal_worker/KNOWN_FIELD.json',R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json',R/'runs/v1978_rpp_first_common_round/actual/cycle_0000_origin.json']
source={str(p.relative_to(R)):sha(p)for p in inputs};static=json.loads(inputs[2].read_bytes());known={k:static[k]for k in ['known_rectangles','known_circles']}
task=json.loads(inputs[3].read_bytes())['tasks'][0]['task'];packet=json.loads(inputs[4].read_bytes())['receipt']['packet'];assert task['task_id']=='common_01'and packet['native_tick']==0 and packet['body'][:3]==[*task['start_xy'],task['start_yaw']]
claim=dict(created_at=datetime.datetime.now().astimezone().isoformat(),cpu=4,positive_geometry_search_limit=1,expansion_limit=22000,outer_seconds=120,source_SHA256=source,models_FFI_controllers_physics=0)
with(S/'NOMINAL_FRONTEND_GEOMETRY_ONCE.json').open('x')as f:f.write(json.dumps(claim,indent=2)+'\n')

def corners(center,hx,hy,yaw=0.):
    c,s=math.cos(yaw),math.sin(yaw)
    return [(center[0]+c*x-s*y,center[1]+s*x+c*y)for x,y in [(-hx,-hy),(hx,-hy),(hx,hy),(-hx,hy)]]
def cross(a,b,c):return(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def inside(p,poly):
    values=[cross(a,b,p)for a,b in zip(poly,poly[1:]+poly[:1])]
    return all(v>=0 for v in values)or all(v<=0 for v in values)
def point_segment(p,a,b):
    den=(b[0]-a[0])**2+(b[1]-a[1])**2
    if den==0:return math.dist(p,a)
    t=max(0.,min(1.,((p[0]-a[0])*(b[0]-a[0])+(p[1]-a[1])*(b[1]-a[1]))/den))
    return math.hypot(p[0]-a[0]-t*(b[0]-a[0]),p[1]-a[1]-t*(b[1]-a[1]))
def point_polygon(p,poly):
    return 0. if inside(p,poly)else min(point_segment(p,a,b)for a,b in zip(poly,poly[1:]+poly[:1]))
def polygons(a,b):
    if any(inside(p,b)for p in a)or any(inside(p,a)for p in b):return 0.
    minimum=float('inf')
    for x,y in zip(a,a[1:]+a[:1]):
        for z,w in zip(b,b[1:]+b[:1]):
            # Proper edge crossings, including containment handled above.
            if cross(x,y,z)*cross(x,y,w)<0 and cross(z,w,x)*cross(z,w,y)<0:return 0.
            minimum=min(minimum,point_segment(x,z,w),point_segment(y,z,w),point_segment(z,x,y),point_segment(w,x,y))
    return minimum
def independent(pose):
    x,y,yaw=pose;center=[x+.3*math.cos(yaw),y+.3*math.sin(yaw)];robot=corners(center,.44,.375,yaw)
    values=[min(x+5,5-x,y+5,5-y)for x,y in robot]
    values += [polygons(robot,corners([x,y],hx,hy))for x,y,hx,hy in known['known_rectangles']]
    values += [point_polygon([x,y],robot)-r for x,y,r in known['known_circles']]
    return min(values)

start=time.monotonic();result=dict(passed=False,scope='ONE_PUBLIC_STATIC_NOMINAL_FRONTEND_GEOMETRY_NOT_PHYSICAL_CAPABILITY',geometry_search_attempts=0,geometry_search_returns=0,new_models_FFI_NLP_controller_queries_physics_replay_audit_Source=0,physical_launch_authorized=False,independent_check_is_sampled_nominal_geometry_only=True)
try:
    # Independent checker sanity cases before the positive search.
    assert polygons(corners([0,0],1,1),corners([3,0],1,1))==1.
    assert polygons(corners([0,0],1,1),corners([.5,.5],.1,.1))==0.
    assert math.isclose(point_polygon([2,2],corners([0,0],1,1)),math.sqrt(2))
    negative=[]
    def refuse(name,fn):
        try:fn()
        except(AssertionError,ValueError,KeyError):negative.append(name)
        else:raise AssertionError('UNEXPECTED_NOMINAL_FRONTEND_ACCEPT:'+name)
    refuse('private_actor_information',lambda:NominalFrontend(np,source,dict(known,actor_truth=[1,2])))
    bad=dict(source);bad[SEARCH]='12'*32;refuse('changed_geometry_source',lambda:NominalFrontend(np,bad,known))
    blocked=NominalFrontend(np,source,known);rect=known['known_rectangles'][0]
    refuse('occupied_start_before_expansion',lambda:blocked.propose_once([rect[0],rect[1],0.,0.,0.],task['goal_xy'],task['goal_yaw']));assert blocked.queries==0
    refuse('occupied_start_poison_no_retry',lambda:blocked.propose_once(packet['body'],task['goal_xy'],task['goal_yaw']))
    refuse('NaN_goal',lambda:rear_goal([float('nan'),0.],0.))
    # Rotated goal transforms: no additional path searches.
    assert rear_goal([1.,2.],0.)==[.7,2.]
    assert np.allclose(rear_goal([1.,2.],math.pi),[1.3,2.],rtol=0,atol=1e-15)
    f=NominalFrontend(np,source,known);result['geometry_search_attempts']=1
    path,report=f.propose_once(packet['body'],task['goal_xy'],task['goal_yaw']);result['geometry_search_returns']=1
    assert path is not None,'NO_NOMINAL_PATH_WITHIN_FIXED_WORK_LIMIT'
    dense=[]
    for a,b in zip(path[:-1],path[1:]):
        angle=math.atan2(math.sin(b[2]-a[2]),math.cos(b[2]-a[2]))
        for i in range(5):
            t=i/5;dense.append([a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),a[2]+t*angle])
    dense.append(path[-1,:3].tolist());original=f.field.pose_values(dense);other=np.asarray([independent(p)for p in dense]);error=float(np.max(abs(original-other)))
    assert error<=1e-10,'INDEPENDENT_SAMPLED_GEOMETRY_MISMATCH'
    assert float(other.min())>=report['guard_m']-1e-8,'NOMINAL_REPORTED_GUARD_NOT_MET'
    window,window_report=local_window(path.tolist());assert math.isclose(window_report['arc_length_m'],.6,abs_tol=1e-12)
    assert math.dist(window[-1][:2],window[0][:2])<=.6+1e-12 and len(window)<len(path)
    refuse('second_geometry_search_not_allowed',lambda:f.propose_once(packet['body'],task['goal_xy'],task['goal_yaw']))
    refuse('invalid_progress_index',lambda:local_window(path.tolist(),start_index=len(path)))
    corner=[[0.,0.,0.,1.],[.2,0.,0.,1.],[0.,0.,0.,-1.]];single,r=local_window(corner);assert len(single)==2 and r['arc_length_m']==.2 and r['gear']==1
    result.update(passed=True,public_static_only=True,hidden_actor_truth_used=False,exposed_common01_not_confirmation=True,report=report,global_nominal_path=path.tolist(),global_path_f64_sha256=hashlib.sha256(path.astype('<f8').tobytes()).hexdigest(),dense_sampled_pose_count=len(dense),independent_max_sampled_error_m=error,independent_sampled_minimum_m=float(other.min()),sampled_clearance_f64_SHA256=hashlib.sha256(other.astype('<f8').tobytes()).hexdigest(),common_first_local_window=window,local_window_report=window_report,negative_cases=negative,shared_common_local_route_data_prepared=True,live_progress_and_gear_cusp_runtime_qualified=False,continuous_dynamic_or_full_response_certificate=False,actual_controller_or_vehicle_capability=False,shared_group_ready=False,source_SHA256=source,numpy_version=np.__version__)
except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
finally:
    result.update(created_at=datetime.datetime.now().astimezone().isoformat(),wall_s=time.monotonic()-start,new_source_SHA256={str(p.relative_to(R)):sha(p)for p in [C/'nominal_frontend.py',Path(__file__).resolve(),C/'NOMINAL_FRONTEND_SCOPE.md']})
    raw=json.dumps(result,indent=2).encode()+b'\n';assert len(raw)<=96*1024
    with(S/'NOMINAL_FRONTEND_GEOMETRY.json').open('xb')as f:f.write(raw)
print(json.dumps({k:result.get(k)for k in ['passed','first_error','geometry_search_attempts','geometry_search_returns','dense_sampled_pose_count','independent_max_sampled_error_m','physical_launch_authorized','wall_s']}))
raise SystemExit(0 if result['passed']else 1)
