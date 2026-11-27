"""One pure ideal-trajectory readout, no optimization or physical replay."""
from pathlib import Path
import os,json,hashlib,math,ast,datetime,time,signal,fcntl
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name;P=R/'runs/v2177_priest_vector_orientation';O=P/'components/MATH';M=1024**2
assert os.sched_getaffinity(0)=={4}and not(S/'RESULT.json').exists()
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(O/'COMPLETION.json')['closed']and read(O/'POST_MATH_STORAGE_BARRIER.json')['passed']and read(P/'OWNER_CLOSED.json')['closed']
for p in [P/'LAUNCH_IDENTITY.json',O/'OWNED_CHILD.json']:
 i=read(p);q=Path('/proc',str(i['pid']),'stat');assert not q.exists()or q.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
handles=[]
for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
 f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);handles.append(f)
for f in handles:f.close()
with(S/'ONCE.json').open('x')as f:json.dump(dict(unix=time.time(),new_NLP_physics=0),f)
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('IDEAL_READOUT_60S')));signal.alarm(60)
source=R/'experiments/v2177_priest_vector_orientation/initial_vector.py';tree=ast.parse(source.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in {'vertices','point_segment','polygon_distance','oracle'}];assert len(nodes)==4
ns={'math':math};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns);oracle=ns['oracle'];known=read(P/'PUBLIC_VECTOR_INPUT.json');required=.24353421020226934;VMAX=.1;KMAX=1/1.32;AMAX=.1;H=.5;radius=math.hypot(.3+.44,.375)

def rear_at(p,v0,v1,k,t):
 d=v0*t+(v1-v0)*t*t/(2*H);a=k*d;s=math.sin(a)/a if a else 1.;b=2*math.sin(a/2)**2/a if a else 0.;c=math.cos(p[2]);sn=math.sin(p[2]);return[p[0]+d*(c*s-sn*b),p[1]+d*(sn*s+c*b),p[2]+a]
def body(p):return[p[0]+.3*math.cos(p[2]),p[1]+.3*math.sin(p[2]),p[2]]
def schedule_bounds(v,k):return min(v)>=0 and max(v)<=VMAX+1e-12 and max(abs(x)for x in k)<=KMAX+1e-12 and max(abs(b-a)/H for a,b in zip(v,v[1:]))<=AMAX+1e-12
rows=[];pins={str(source.relative_to(R)):sha(source),str((P/'PUBLIC_VECTOR_INPUT.json').relative_to(R)):sha(P/'PUBLIC_VECTOR_INPUT.json'),str((O/'RESULT.json').relative_to(R)):sha(O/'RESULT.json'),str((O/'POST_MATH_STORAGE_BARRIER.json').relative_to(R)):sha(O/'POST_MATH_STORAGE_BARRIER.json'),str(Path(__file__).relative_to(R)):sha(Path(__file__))}
for case in ['straight','left_bump']:
 p=O/(case+'_CHECKED_RETURN.json');raw=O/(case+'_RAW_RETURN.json');x=read(p);ret=read(raw);pins[str(p.relative_to(R))]=sha(p);pins[str(raw.relative_to(R))]=sha(raw)
 assert ret['success']and ret['status']==0 and x['passed'];v=x['speeds'];k=x['curvatures'];poses=x['poses'];assert len(v)==21 and len(k)==20 and len(poses)==21
 state=[-4.3,-2.,0.];maximum_node_error=0.;minimum=float('inf');evaluations=0;max_yawrate=0.
 for i in range(20):
  max_yawrate=max(max_yawrate,max(abs(v[i]*k[i]),abs(v[i+1]*k[i])))
  for j in range(51):minimum=min(minimum,min(oracle(body(rear_at(state,v[i],v[i+1],k[i],H*j/50)),known)));evaluations+=1
  state=rear_at(state,v[i],v[i+1],k[i],H);maximum_node_error=max(maximum_node_error,max(abs(a-b)for a,b in zip(state,poses[i+1])))
 bound=minimum-(max(v)+radius*max_yawrate)*.01/2-1e-10
 gates=dict(original_solver_success=True,ideal_bounds=schedule_bounds(v,k),independent_endpoint_closure=maximum_node_error<=1e-8,original_hard_geometry_bound=bound>=required,terminal_rest=abs(v[0])+abs(v[1])+abs(v[-2])+abs(v[-1])<=1e-12,original_endpoint=max(abs(a-b)for a,b in zip(state,[-3.7,-2.,0.]))<=1e-8)
 rows.append(dict(case=case,passed=all(gates.values()),gates=gates,independent_maximum_node_error=maximum_node_error,sampled_exact_clearance_m=minimum,ideal_continuous_distance_lower_bound_m=bound,unchanged_required_m=required,distance_lower_bound_margin_m=bound-required,evaluated_poses=evaluations,maximum_grid_dt_s=.01,maximum_surface_speed_bound=max(v)+radius*max_yawrate,final_rear_pose=state))
blocked=dict(known,known_circles=known['known_circles']+[[-4.,-2.,.1]]);occupied=min(oracle([-4.,-2.,0.],blocked));assert occupied<required
bad=[0.,0.]+[.101]*17+[0.,0.];assert not schedule_bounds(bad,[0.]*20)
r=dict(passed=all(x['passed']for x in rows),closed=True,identity='INDEPENDENT_IDEAL_KINEMATIC_POLYGON_DISTANCE_READOUT',cases=rows,occupied_negative_m=occupied,overspeed_negative_refused=True,new_optimizer_NN_models_physics_replay_physical_audit=0,native_author_PRIEST=False,vehicle_or_whole_navigation_qualified=False,formal_samples=0,source_SHA256=pins,created_at=datetime.datetime.now().astimezone().isoformat());text=json.dumps(r,indent=2,allow_nan=False)+'\n';assert len(text.encode())<96*1024;(S/'RESULT.json').write_text(text);print(json.dumps(r))
