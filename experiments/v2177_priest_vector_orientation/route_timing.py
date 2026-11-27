"""Finite route/target applicability arithmetic, no author import or optimizer."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,importlib.util,json,math,os
import numpy as np
R=Path(__file__).resolve().parents[2];S=R/'runs/v2177_priest_vector_orientation'
assert os.sched_getaffinity(0)=={4}and not(S/'ROUTE_TIMING_GATE.json').exists()
routefile=R/'runs/v2170_sccr_live_source_scope/components/SCCR/actual/SCCR_UNION_PUBLIC_ROUTE.json';r=json.loads(routefile.read_text());path=r['original_virtual_rear_path']
knownfile=R/'experiments/v855_renewal_worker/KNOWN_FIELD.json';known=json.loads(knownfile.read_text())
gfile=R/'experiments/v2176_sccr_common_plant_component/geometry.py';spec=importlib.util.spec_from_file_location('C2177_route_geometry',gfile);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
# Independent oracle functions only, not the already-closed initial gate main.
original=R/'experiments/v2177_priest_vector_orientation/initial_vector.py';tree=ast.parse(original.read_text());nodes=[copy.deepcopy(n)for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in ['vertices','point_segment','polygon_distance','oracle']];scope={'math':math};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<independent_polygon_oracle_functions>','exec'),scope)
length=0.;curvature=[];dense=[];minstep=float('inf')
for i,(a,b)in enumerate(zip(path,path[1:])):
 distance=math.dist(a[:2],b[:2]);length+=distance;minstep=min(minstep,distance);theta=math.atan2(math.sin(b[2]-a[2]),math.cos(b[2]-a[2]))
 assert a[3] in[-1.,1.]and b[3]in[-1.,1.]
 if distance>1e-12 and a[3]==b[3]:curvature.append(abs(theta/distance))
 for j in range(5):
  f=j/5;heading=a[2]+f*theta;x=a[0]+f*(b[0]-a[0]);y=a[1]+f*(b[1]-a[1]);dense.append([x+.3*math.cos(heading),y+.3*math.sin(heading),heading])
a=path[-1];dense.append([a[0]+.3*math.cos(a[2]),a[1]+.3*math.sin(a[2]),a[2]])
conservative=[];exact=[];excess=0.
for pose in dense:
 v=g.feature(pose,known)[0];e=scope['oracle'](pose,known);conservative.append(min(v));exact.append(min(e));excess=max(excess,max(a-b for a,b in zip(v,e)));assert all(a<=b+1e-10 for a,b in zip(v,e))
# Prove the existing captured scaled request's necessary target bound using
# only the exact author AST prefix through y_fin_path, without a constructor.
requestfile=R/'runs/v2122_priest_quiescent_handoff/vehicle/actual/PRIEST_OPTIMIZER_REQUEST.json';request=json.loads(requestfile.read_text());author=R/'runs/v1484_baseline_disposition_priest/upstream/priest/src/mpc_non_dy.py';author_sha=hashlib.sha256(author.read_bytes()).hexdigest();assert author_sha==request['port_identity']['author_sha256']
fn=next(n for n in ast.walk(ast.parse(author.read_text()))if isinstance(n,ast.FunctionDef)and n.name=='compute_traj_guess');prefix=[]
for n in fn.body:
 prefix.append(copy.deepcopy(n))
 if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='y_fin_path'for t in n.targets):break
assert isinstance(prefix[-1],ast.Assign)and prefix[-1].targets[0].id=='y_fin_path'
kw=request['constructor_kwargs'];data=request['path'];space={'jnp':np,'self':SimpleNamespace(t_fin=kw['t_fin']),'v_des':kw['v_des'],'initial_state':np.array(request['initial_state'],float)}
for name in ['x_waypoint','y_waypoint','arc_vec']:space[name]=np.asarray(data[name],float)
exec(compile(ast.Module(body=prefix,type_ignores=[]),'<exact_author_target_prefix_only>','exec'),space)
start=request['initial_state'][:2];end=[float(space['x_fin_path']),float(space['y_fin_path'])];displacement=math.dist(start,end);H=kw['t_fin'];vmax=kw['v_max'];amax=kw['a_max'];speed0=math.hypot(*request['initial_state'][2:4]);tacc=min(H,max(0.,(vmax-speed0)/amax));acceleration_upper=speed0*tacc+.5*amax*tacc*tacc+vmax*(H-tacc)
# Feasible initializer defined in protocol, not an optimization/outcome search.
straight_prefix_length=.6;straight_prefix=[]
for a in path:
 if a[0]-path[0][0]<=straight_prefix_length+1e-10:straight_prefix.append(a)
assert len(straight_prefix)>2 and all(abs(a[1]+2.)<1e-12 and abs(a[2])<1e-12 and a[3]==1. for a in straight_prefix)
result=dict(passed=True,scope='PUBLIC_ROUTE_AND_CAPTURED_REQUEST_NECESSARY_TIMING_CONDITIONS_ONLY',
 route_pose_count=len(path),dense_samples=len(dense),rear_arc_length_m=length,maximum_discrete_rear_curvature_m_inv=max(curvature),common_curvature_limit=1/1.32,
 conservative_vector_min_clearance_m=min(conservative),independent_exact_min_clearance_m=min(exact),conservative_route_geometry_passed=min(conservative)>=g.REQUIRED,exact_route_geometry_passed=min(exact)>=g.REQUIRED,original_required_m=g.REQUIRED,
 conservative_oracle_max_excess_m=excess,gears=sorted(set(a[3]for a in path)),end_bodycentre=dense[-1],body_goal_distance_m=math.dist(dense[-1][:2],[4.,-2.]),
 full_route_speed_only_time_lower_s=length/vmax,local_author_horizon_s=H,full_route_arrival_not_implied=True,
 captured_author_target=dict(initial_xy=start,selected_xy=end,selected_index=int(space['index_final_path']),requested_arc_lookahead_m=kw['v_des']*H,selected_displacement_m=displacement,continuous_speed_upper_m=vmax*H,continuous_acceleration_speed_upper_m=acceleration_upper,exceeds_speed_necessary_bound=displacement>vmax*H,exceeds_acceleration_necessary_bound=displacement>acceleration_upper,author_optimizer_not_reexecuted=True,original_first_refusal_not_replaced_or_attributed_to_timing=True,source_prefix_line_range=[prefix[0].lineno,prefix[-1].end_lineno]),
 analytic_0p6m_initializer_prefix_is_in_saved_straight_route=True,
 new_source_solver_Predictor_Allocator_models_NN_physics_replay_physical_audit_formal_calls=0,
 source_SHA256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),routefile,knownfile,gfile,original,requestfile,author]})
raw=json.dumps(result,indent=2,allow_nan=False)+'\n';assert len(raw.encode())<65536;(S/'ROUTE_TIMING_GATE.json').write_text(raw);print(json.dumps(result))
