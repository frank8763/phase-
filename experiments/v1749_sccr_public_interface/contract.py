"""Public geometry and causal measurement only; no access to a simulator."""
import copy,hashlib,json,math
SCAN_KEYS=('native_tick','time','xy','yaw','ranges')
PACKET_FIELDS=('native_tick','sim_time','body')
KNOWN_FIELDS={'known_rectangles','known_circles'}
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def finite(values):return all(type(v)in{int,float}and math.isfinite(v)for v in values)
def public_known(value):
 assert type(value)is dict and set(value)==KNOWN_FIELDS,'SCCR_PUBLIC_MAP_SCOPE'
 for row in value['known_rectangles']:assert len(row)==4 and finite(row)and row[2]>0 and row[3]>0,'SCCR_PUBLIC_RECTANGLE'
 for row in value['known_circles']:assert len(row)==3 and finite(row)and row[2]>0,'SCCR_PUBLIC_CIRCLE'
 return copy.deepcopy(value)
def causal_input(receipt,known,route,config):
 assert receipt['schema']=='PHASE_CURRENT_MEASUREMENT_V1'and receipt['packet_acquisitions']==1,'SCCR_RECEIPT_IDENTITY'
 p=receipt['packet'];assert digest(p)==receipt['packet_sha256'],'SCCR_PACKET_SHA'
 n=p['native_tick'];t=p['sim_time'];assert type(n)is int and n>=0 and finite([t])and abs(t-.01*n)<=1e-8,'SCCR_NATIVE_CLOCK'
 assert finite(p['body'])and len(p['body'])==5,'SCCR_BODY_SHAPE'
 assert n==p['steering']['native_tick'],'SCCR_STEERING_NATIVE'
 assert finite([receipt['before_monotonic'],receipt['after_monotonic'],p['body_measured_at'],p['sent_at'],p['steering']['measured_at']])and receipt['before_monotonic']<=p['body_measured_at']==p['sent_at']==p['steering']['measured_at']<=receipt['after_monotonic'],'SCCR_REAL_RECEIPT_CLOCK'
 scan=receipt['scan'];assert set(scan)==set(SCAN_KEYS),'SCCR_NO_TRUTH_SCAN'
 k=scan['native_tick'];assert type(k)is int and 0<=n-k<=5 and abs(scan['time']-.01*k)<=1e-8 and -1e-8<=t-scan['time']<=.05+1e-8,'SCCR_SCAN_CAUSAL_AGE'
 assert len(scan['xy'])==2 and len(scan['ranges'])==32 and finite([*scan['xy'],scan['yaw'],*scan['ranges']])and all(0<=v<=3.00000001 for v in scan['ranges']),'SCCR_SCAN_SHAPE_RANGE'
 assert type(route)is list and len(route)>=6 and all(type(v)is list and len(v)==2 and finite(v)for v in route),'SCCR_PUBLIC_ROUTE'
 expected={'robot_radius':.28,'phase21_corridor_radius':.36000000000000004,'phase21_v4_min_known_margin':.06,'phase21_v4_min_sensor_margin':.025,'phase21_v4_max_p95_curvature':1.8,'phase21_v4_max_heading_delta':.24,'phase21_path_lookahead':2.2,'phase21_v3_conflict_margin':.06}
 assert config==expected,'SCCR_PLANNER_PARAMETERS_CHANGED'
 points=[]
 for i,r in enumerate(scan['ranges']):
  if .05<r<2.999:
   angle=scan['yaw']+math.tau*i/32;points.append([scan['xy'][0]+r*math.cos(angle),scan['xy'][1]+r*math.sin(angle)])
 return dict(observation={k:copy.deepcopy(p[k])for k in PACKET_FIELDS},scan=copy.deepcopy(scan),sensor_world_points=points,known=public_known(known),original=copy.deepcopy(route),config=copy.deepcopy(config),source_packet_sha256=digest(p),causal_point_map_adaptation=True,physical_admission=False,whole_navigation=False)
