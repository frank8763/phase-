"""Independent prerequisite lanes, no model/optimizer imports or formal claims."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import os,sys,json,hashlib,math,types,time,traceback,ast,resource
from pure_sources import R,sha,P6,P14,P7,P17,functions
C=Path(__file__).resolve().parent;S=R/'runs'/C.name
assert os.sched_getaffinity(0)=={4};resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(160,170))
import numpy as np
from shared_sensors import METHODS,capture_fixture,Consumer,digest
pins={};results={};start=time.monotonic()
def read(p):
 p=Path(p);p=p if p.is_absolute()else R/p;raw=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
def put(name,d):
 raw=json.dumps(d,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<1024**2;assert sum(p.stat().st_blocks*512 for p in S.rglob('*')if p.is_file())+len(raw)<2*1024**2;(S/name).write_bytes(raw)
def sensing():
 for p in[P6,P14,P7,P17]:pins[str(p.relative_to(R))]=sha(p)
 producer=digest(pins);rows=[];packets=[]
 for i,kind in enumerate(['open','rectangle','circle']):
  world=dict(bounds=[-5.,5.],rectangles=[[.9,0.,.12,.3]]if kind=='rectangle'else[],circles=[[.9,0.,.15]]if kind=='circle'else[])
  for heading in range(8):
   k=(8*i+heading)*5;packet=capture_fixture(np,world,[0.,0.,heading*math.pi/4],[2.,0.],k,.01*k,producer);packets.append(packet)
   consumed=[Consumer(m,producer).receive(packet,k)for m in METHODS];assert all(x==consumed[0]for x in consumed)
   rows.append(dict(scene=kind,heading=heading*math.pi/4,native=k,packet_sha256=packet['packet_sha256'],feature_count=sum(map(len,consumed[0].values()))))
 negatives=[]
 def reject(name,packet,k=0):
  try:Consumer('SCCR',producer).receive(packet,k)
  except(AssertionError,ValueError,KeyError):negatives.append(name)
  else:raise AssertionError('SENSOR_NEGATIVE_ACCEPTED:'+name)
 base=packets[0];bad=dict(base,producer_source_sha256='0'*64);reject('foreign_sensor_source',bad)
 bad=json.loads(json.dumps(base));bad['camera_depth_features']['phase7_depth_summary'][0]+=.1;reject('changed_feature_digest',bad)
 bad=dict(base,actor_world_xy=[1.,2.]);reject('hidden_actor_truth_field',bad)
 reject('future_or_stale_tick',base,5)
 consumer=Consumer('SCCR',producer);consumer.receive(base,0)
 try:consumer.receive(base,0)
 except AssertionError:negatives.append('repeated_packet')
 else:raise AssertionError('SENSOR_REPEATED_ACCEPTED')
 return dict(passed=True,scope='ORIGINAL_PURE_SENSOR_SOFTWARE_ONLY',scenarios=24,method_consumers=10,per_scenario_equal_information=True,camera_depth_features=50,rows=rows,negative_cases=negatives,actual_sensor_acquisitions=0,SCCR_full186_feature_builder_qualified=False,SCCR_actor_constructed=0,SCCR_inference=0,training=0,camera_is_goal_feature_not_RGB=True,depth_is_discrete_raycast_not_image=True,physical_noise_and_sampling_NOT_qualified=True,original_32ray_contract_unchanged=True)
def priest():
 O=R/'runs/v2122_priest_quiescent_handoff/vehicle/actual';request=read(O/'PRIEST_OPTIMIZER_REQUEST.json');source=R/'runs/v1484_baseline_disposition_priest/upstream/priest/src/mpc_non_dy.py';pins[str(source.relative_to(R))]=sha(source);tree=ast.parse(source.read_text())
 boundary=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='compute_boundary_vec');assert 'x_init_vec'in ast.unparse(boundary)and 'b_eq_x'in ast.unparse(boundary)
 assert 'np.linspace(0, t_fin, num)'in source.read_text()
 shadow=read(O/'cycle_000000_shadow.json');initial=read(O/'cycle_000000_origin.json')['receipt']['packet'];rear=request['initial_state'][:2];body=initial['body'][:2];a=request['constructor_kwargs']['a_obs_1'];points=request['static_points_world']
 values=[sum((x-y)**2 for x,y in zip(rear,p))/a**2 for p in points];assert len(values)==50 and max(values)<1.
 geometry=R/'experiments/v2131_filter_measured_current/geometry.py';pins[str(geometry.relative_to(R))]=sha(geometry);space={};exec(compile(geometry.read_text(),str(geometry),'exec'),space);reserve=space['REQUIRED'];radius=math.hypot(.44,.375)+reserve+.05/math.sqrt(2)
 body_values=[sum((x-y)**2 for x,y in zip(body,p))/radius**2 for p in points];assert min(body_values)>=1
 max_circle_violation=0.;max_roundtrip=0.
 for j in range(512):
  yaw=2*math.pi*j/512;c,s=math.cos(yaw),math.sin(yaw);rear_xy=[body[0]-.3*c,body[1]-.3*s];center=[rear_xy[0]+.3*c,rear_xy[1]+.3*s];max_roundtrip=max(max_roundtrip,math.dist(center,body))
  for dx in[-.44,.44]:
   for dy in[-.375,.375]:
    offset=[dx*c-dy*s,dx*s+dy*c];max_circle_violation=max(max_circle_violation,math.hypot(*offset)-math.hypot(.44,.375))
 assert max_circle_violation<=1e-15 and max_roundtrip<=1e-14
 return dict(passed=True,scope='SAVED_AUTHOR_INPUT_FEASIBILITY_DIAGNOSIS_NOT_NEW_PRIEST_RUN',initial_ellipse_obstacle_violations=50,static_points=50,old_reference='REAR_AXLE',old_inflated_radius=a,minimum_initial_normalized_distance_squared=min(values),initial_equality_includes_t0=True,all_old_obstacle_inequalities_cannot_hold_at_fixed_t0=True,old_vehicle_shadow_minimum=shadow['minimum_raw_m'],required_original_reserve=shadow['required_raw_m'],deficit_m=shadow['required_raw_m']-shadow['minimum_raw_m'],body_center_candidate_inflated_radius=radius,body_center_candidate_initial_violations=sum(v<1 for v in body_values),body_center_candidate_minimum_normalized_distance_squared=min(body_values),candidate_512_heading_circle_enclosure_max_error=max_circle_violation,candidate_reference_transform_max_error=max_roundtrip,new_optimizer_calls=0,original_author_parameters_changed=False,old_failure_preserved=True,future_need='body-center polynomial and current rear pose/velocity/curvature coupling, full physical stopping plus independent positive controls',new_body_center_adapter_qualified=False)
def pcbf():
 O=R/'runs/v2131_filter_measured_current/components/PCBF/actual';completion=read(O.parent/'COMPLETION.json');assert completion['closed']
 frame=read(O/'FILTER_QUERY_002_INPUT.json');raw=read(O/'FILTER_QUERY_002_RESULT.json');answer=raw['answer'];row=answer['returns'][0]
 assert len(answer['returns'])==1 and answer['numerical']['refused_stage']=='AUXILIARY'and row['status']==8 and not row['success']
 parent=R/'experiments/v2131_filter_measured_current';sys.path.insert(0,str(parent));from context import read as context_read,load
 source=context_read(R/'runs/v2131_filter_measured_current/SOURCE_FREEZE.json')['files'];deps=load('PCBF_saved_ideal_math',parent/'filter_scope.py')
 case=frame['request']['case'];known=frame['request']['public_known'];z=[.05,0.]*8
 with deps.scope(source)as modules:values,_,_=modules.filter.values_jac(z,case,known,'PCBF')
 assert max(values)<0.
 return dict(passed=True,scope='SAVED_AUXILIARY_FAILURE_AND_ZERO_SLACK_WITNESS_NO_SOLVER',original_failure_status=row['status'],original_failure_residual=row['maximum_constraint_residual'],original_failure_objective=row['objective'],original_failure_nit=row['nit'],original_returned_success=False,original_residual_gate=1e-7,strict_status_not_relaxed=True,zero_slack_witness_z=z,zero_slack_witness_maximum_constraint_residual=max(values),zero_slack_witness_objective=0.,all_nonnegative_slack_weights_prove_objective_lower_bound=0.,mathematically_feasible_initial_auxiliary_point_exists=True,not_new_optimized_solution=True,solver_calls=0,vehicle_calls=0,future_candidate='deterministic feasible-zero-slack initial point when validated by unchanged constraints; otherwise original feasible slack start; no retry',future_variant_unqualified=True)
for name,fn in [('SCCR',sensing),('PRIEST',priest),('PCBF',pcbf)]:
 try:results[name]=fn()
 except BaseException as e:results[name]=dict(passed=False,error=repr(e),traceback=traceback.format_exc())
 put(name+'_QUALIFICATION_READOUT.json',results[name])
assert all(sha(R/n)==h for n,h in pins.items())
put('PROVENANCE.json',dict(closed=True,models=0,optimizer_calls=0,physics=0,replay=0,new_physical_audits=0,new_formal_claims=0,scope='SOFTWARE_AND_SAVED_BOUNDARY_PREREQUISITES_NOT_VEHICLE_QUALIFICATION',local_time=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),input_SHA256=pins,source_SHA256={str(p.relative_to(R)):sha(p)for p in C.glob('*')if p.is_file()},wall_s=time.monotonic()-start,all_inputs_unchanged=True,all_lanes_passed=all(x['passed']for x in results.values())))
print(json.dumps({k:{x:v for x,v in d.items()if x not in ['rows','traceback','zero_slack_witness_z']}for k,d in results.items()}));raise SystemExit(0 if all(x['passed']for x in results.values())else 1)
