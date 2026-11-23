"""Sampled path geometry -> original Phase request interface. Never a controller."""
import copy,hashlib,json,math
WHEELBASE=.6
CAP=.42722137342572125

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def geometry(path):
 assert type(path)is list and len(path)>=3,'PATH_TOO_SHORT'
 assert all(type(p)is list and len(p)==2 and all(type(x)in{int,float}and math.isfinite(x)for x in p)for p in path),'PATH_NONFINITE_OR_SHAPE'
 rows=[]
 for i in range(1,len(path)-1):
  a=[path[i][j]-path[i-1][j]for j in range(2)];b=[path[i+1][j]-path[i][j]for j in range(2)]
  la=math.hypot(*a);lb=math.hypot(*b);chord=math.hypot(a[0]+b[0],a[1]+b[1]);assert la>1e-8 and lb>1e-8 and chord>1e-8,'PATH_DEGENERATE_OR_REVERSAL'
  k=2*(a[0]*b[1]-a[1]*b[0])/(la*lb*chord);delta=math.atan(WHEELBASE*k);assert math.isfinite(k)and math.isfinite(delta)
  rows.append(dict(vertex=i,curvature_per_m=k,raw_center_steering_rad=delta,within_original_center_cap=abs(delta)<=CAP))
 return rows

def qualify():
 assert all(r['curvature_per_m']==0. for r in geometry([[0.,0.],[1.,0.],[2.,0.]]))
 for fixture in [[[0.,0.],[0.,0.],[1.,0.]],[[0.,0.],[1.,0.],[0.,0.]],[[0.,0.],[float('nan'),0.],[1.,0.]],[[0.,0.],[1.,0.]],[[0.,0.],[1.,0.,0.],[2.,0.]]]:
  try:geometry(fixture)
  except AssertionError:pass
  else:raise AssertionError('INVALID_PATH_ACCEPTED')
 return 5

def run(fixture,bridge):
 assert bridge.CENTER_LIMIT==CAP and bridge.WHEELBASE==WHEELBASE,'ORIGINAL_VEHICLE_UNITS_CHANGED'
 assert fixture['synthetic_software_fixture']is True and fixture['real_measured_receipt']is False and fixture['no_plant_reuse']is True
 assert fixture['declared_speed_mps']==.1 and fixture['declared_gear']==1,'CHANGED_SPEED_OR_GEAR'
 original=copy.deepcopy(fixture);packet=fixture['origin_packet'];origin=bridge.decode(packet,expected_native=packet['native_tick'],expected_sim_time=packet['sim_time'],expected_packet_sha256=bridge.digest(packet))
 rows=geometry(fixture['selected_path']);requests=[];rejection=None
 for row in rows:
  try:
   x=bridge.request(row['raw_center_steering_rad'],longitudinal_speed=.1,declared_gear=1,origin=origin,expected_origin_sha256=bridge.digest(packet))
  except AssertionError as error:
   rejection=dict(vertex=row['vertex'],error=repr(error),raw_center_steering_rad=row['raw_center_steering_rad'],original_cap_rad=CAP);break
  v,w,_=x['body_request'];assert abs(w-v*row['curvature_per_m'])<=1e-14,'CURVATURE_BODY_REQUEST_ALGEBRA'
  requests.append(dict(vertex=row['vertex'],raw_delta=row['raw_center_steering_rad'],hypothetical_body_request=x['body_request'],origin_packet_sha256=x['origin_packet_sha256'],not_applied_to_vehicle=True))
 assert fixture==original,'INPUT_MUTATED'
 return dict(passed=rejection is None,scope='SAMPLED_SYNTHETIC_PATH_ORIGINAL_PHASE_REQUEST_GATE',geometry_samples=len(rows),mapped_samples_before_first_refusal=len(requests),sampled_max_abs_center_steering_rad=max(abs(r['raw_center_steering_rad'])for r in rows),original_center_cap_rad=CAP,first_refusal=rejection,geometry=rows,hypothetical_requests=requests,original_bridge_used=True,no_clipping_or_smoothing=True,continuous_path_feasibility_unknown=True,no_tracking_controller_defined=True,physical_admission=False,models=0,physical_native=0,replay_native=0,original_SCCR_queries=0,whole_navigation_passed=None)
