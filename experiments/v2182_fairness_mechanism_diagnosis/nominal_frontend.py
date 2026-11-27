"""Shared public-static nominal geometry, no controller or physical authority."""
import ast,copy,hashlib,heapq,math,time
from pathlib import Path
from types import SimpleNamespace,MethodType
R=Path(__file__).resolve().parents[2]
SEARCH='experiments/v855_renewal_worker/task_planner.py'
GEOMETRY='experiments/v855_renewal_worker/exact_footprint.py'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def _functions(path,names,env):
    tree=ast.parse(path.read_text());nodes=[copy.deepcopy(n)for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names]
    assert {n.name for n in nodes}==set(names)
    scope=dict(env);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),scope)
    return scope
def rear_pose(body):
    assert len(body)==5 and all(type(v)in(int,float)and math.isfinite(v)for v in body)
    return [body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]]
def rear_goal(goal,yaw):
    assert len(goal)==2 and all(type(v)in(int,float)and math.isfinite(v)for v in [*goal,yaw])
    return [goal[0]-.3*math.cos(yaw),goal[1]-.3*math.sin(yaw)]

class NominalFrontend:
    def __init__(self,np,source,known):
        for n in [SEARCH,GEOMETRY]:assert source[n]==sha(R/n),'NOMINAL_GEOMETRY_SOURCE_CHANGED'
        assert set(known)=={'known_rectangles','known_circles'},'FRONTEND_PRIVATE_OR_UNDECLARED_INFORMATION'
        rect=np.asarray(known['known_rectangles'],float).reshape(-1,4);circle=np.asarray(known['known_circles'],float).reshape(-1,3)
        assert len(rect)<=64 and len(circle)<=64 and np.isfinite(rect).all()and np.isfinite(circle).all()
        assert (rect[:,2:]>0).all()and(circle[:,2]>=0).all()
        base=_functions(R/SEARCH,['wrap','search'],dict(np=np,heapq=heapq,math=math,time=time))
        geometry=_functions(R/GEOMETRY,['pose_values'],dict(np=np))['pose_values']
        self.field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=rect.copy(),circles=circle.copy(),sensor_points=np.empty((0,2)),sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.,resolution=.05),clearance=np.ones((201,201)))
        self.field.pose_values=MethodType(geometry,self.field);self.search=base['search'];self.np=np;self.queries=0;self.poisoned=False
    def propose_once(self,body,goal,goal_yaw):
        assert not self.poisoned and self.queries==0,'ONE_GEOMETRY_SEARCH_ONLY'
        self.poisoned=True;start=rear_pose(body);target=rear_goal(goal,goal_yaw)
        # Cheap necessary negative, before any node expansion or query count.
        initial=float(self.field.pose_values([start])[0]);assert initial>=.15-1e-6,'NOMINAL_OCCUPIED_START'
        self.queries=1
        path,report=self.search(self.field,start,target,.6,math.atan(.6*.50),guard=.27,budget=15.,dense_requested_guard=True,work_limit=22000)
        if path is not None:
            assert path.ndim==2 and path.shape[1]==4 and len(path)>=2 and self.np.isfinite(path).all()
            end=path[-1];center=end[:2]+.3*self.np.array([math.cos(end[2]),math.sin(end[2])])
            report=dict(report,nominal_body_goal_distance_m=float(self.np.linalg.norm(center-self.np.asarray(goal))),nominal_goal_yaw_error_rad=abs(math.atan2(math.sin(end[2]-goal_yaw),math.cos(end[2]-goal_yaw))))
        self.poisoned=False
        return path,dict(report,actual_whole_goal_xy=list(goal),registered_goal_yaw=goal_yaw,registered_rear_goal_xy=target,public_static_only=True,controller_capability=False,continuous_or_dynamic_safety_certificate=False,physical_launch_authorized=False)

def local_window(path,*,start_index=0):
    """Fixed .6m same-gear window; live progress/index authority is external."""
    rows=[list(p)for p in path]
    assert len(rows)>=2 and type(start_index)is int and 0<=start_index<len(rows)-1
    assert all(len(p)==4 and all(type(v)in(int,float)and math.isfinite(v)for v in p)and p[3]in(-1,1)for p in rows)
    gear=int(rows[start_index+1][3]);out=[rows[start_index][:]];distance=0.
    for a,b in zip(rows[start_index:-1],rows[start_index+1:]):
        if int(b[3])!=gear:break
        edge=math.dist(a[:2],b[:2]);remaining=.6-distance
        if edge>=remaining and edge>0:
            fraction=remaining/edge;angle=math.atan2(math.sin(b[2]-a[2]),math.cos(b[2]-a[2]))
            out.append([a[0]+fraction*(b[0]-a[0]),a[1]+fraction*(b[1]-a[1]),a[2]+fraction*angle,float(gear)]);distance=.6;break
        out.append(b[:]);distance+=edge
    assert len(out)>=2,'NO_LOCAL_SINGLE_GEAR_EDGE'
    return out,dict(gear=gear,arc_length_m=distance,requested_lookahead_m=.6,source_start_index=start_index,live_progress_tracking_qualified=False,not_arrival_or_safety_certificate=True)
