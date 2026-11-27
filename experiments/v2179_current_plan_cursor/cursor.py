"""Pure data protocol; NEVER grants numerical or physical execution authority."""
from pathlib import Path
import ast,copy,hashlib,json,math
R=Path(__file__).resolve().parents[2]
DT=.01;PREFIX=5;VMAX=.1;KMAX=1/1.32;AMAX=.1;OFFSET=.3
RESPONSE_CHECKS={'finite','full_states','full_raw_geometry','full_200_stop','speed_yaw','legal_ctrl','legal_slew','full2200','terminal_body_rest','terminal_steering_rest','memory_shape','terminal_full_cycle_hold'}
RECEIPT={'schema','packet_acquisitions','packet','packet_sha256','before_monotonic','after_monotonic','scan'}
PACKET={'body','body_lateral','native_tick','sim_time','body_measured_at','sent_at','dynamic_discovered','steering','controller_memory','coupled_episode','steering_motion_active'}
PHYSICAL={'body','body_lateral','native_tick','sim_time','dynamic_discovered','steering','controller_memory','coupled_episode','steering_motion_active'}
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def function(path,name,scope):
 t=ast.parse(path.read_text());n=next(n for n in t.body if isinstance(n,ast.FunctionDef)and n.name==name);exec(compile(ast.Module(body=[n],type_ignores=[]),str(path),'exec'),scope);return scope[name]
_clock_scope=dict(copy=copy,math=math,NATIVE_DT=DT,CLOCK_TOLERANCE=1e-8,SCAN_KEYS=('native_tick','time','xy','yaw','ranges'))
for n in ['native_clock','scan_only']:function(R/'experiments/v1694_shared_observation_closure/contract.py',n,_clock_scope)
_receipt_scope=dict(copy=copy,math=math,digest=digest,scan_only=_clock_scope['scan_only'])
verify_original=function(R/'experiments/v2176_sccr_common_plant_component/observation.py','verify',_receipt_scope)
def finite(x):return type(x)in(int,float)and math.isfinite(x)
def measured(receipt,native):
 assert type(receipt)is dict and set(receipt)==RECEIPT,'RECEIPT_FIELDS';p=verify_original(receipt,native,native*DT)
 assert set(p)==PACKET and type(p['native_tick'])is int and type(p['steering']['native_tick'])is int,'UNDECLARED_PACKET_FIELDS'
 assert type(p['body'])is list and len(p['body'])==5 and all(finite(v)for v in p['body']),'BODY_VALUES'
 assert finite(p['body_lateral'])and type(p['steering'])is dict and set(p['steering'])=={'position','velocity','native_tick','measured_at'},'STEERING_SCHEMA'
 assert all(type(p['steering'][n])is list and len(p['steering'][n])==2 and all(finite(v)for v in p['steering'][n])for n in ['position','velocity']),'STEERING_VALUES'
 assert set(p['controller_memory'])=={'last_ctrl','integral'}and len(p['controller_memory']['last_ctrl'])==4 and all(finite(v)for v in p['controller_memory']['last_ctrl'])and finite(p['controller_memory']['integral']),'MEMORY_VALUES'
 assert all(type(p[n])is bool for n in ['dynamic_discovered','coupled_episode','steering_motion_active']),'MEASURED_FLAGS'
 return p

def state_digest(p):
 d={k:copy.deepcopy(p[k])for k in PHYSICAL};d['steering'].pop('measured_at');return digest(d)
def rear(p):
 x,y,t=p['body'][:3];return[x-OFFSET*math.cos(t),y-OFFSET*math.sin(t),t]
def arc(p,v0,v1,k,t,h):
 d=v0*t+.5*(v1-v0)*t*t/h;a=k*d;s=math.sin(a)/a if a else 1.;b=2*math.sin(a/2)**2/a if a else 0.;c=math.cos(p[2]);sn=math.sin(p[2]);return[p[0]+d*(c*s-sn*b),p[1]+d*(sn*s+c*b),p[2]+a]
def angle(a):return math.atan2(math.sin(a),math.cos(a))

class Cursor:
 episodes=set()
 def __init__(self,episode_id):
  assert type(episode_id)is str and episode_id and episode_id not in self.episodes,'EPISODE_MISSING_OR_RESTARTED';self.episodes.add(episode_id)
  self.episode=episode_id;self.expected=0;self.pending=None;self.plan=None;self.poisoned=False;self.closed=False;self.commits=0;self.previous=None
 def alive(self):assert not self.closed and not self.poisoned,'CLOSED_OR_POISONED_CURSOR'
 def install(self,plan,query_receipt,current_receipt):
  try:
   self.alive();assert self.plan is None and self.expected==0 and self.pending is None,'PROFILE_CANNOT_BE_RESTARTED'
   assert set(plan)=={'query','success','status','native_author_PRIEST','interval_s','speeds','curvatures','rear_poses'},'PROFILE_UNDECLARED_FIELDS'
   a=measured(query_receipt,0);b=measured(current_receipt,0);assert current_receipt['before_monotonic']>=query_receipt['after_monotonic'],'POST_SOLVE_ACQUISITION_NOT_LATER';assert state_digest(a)==state_digest(b),'POST_SOLVE_PHYSICAL_STATE_CHANGED'
   q=plan['query'];assert set(q)=={'episode_id','origin_native','origin_sim_time','receipt_sha256','state_sha256','query_sequence','source_freeze_sha256','numerical_admission_sha256','query_nonce'},'QUERY_BINDING_SCHEMA'
   assert q['episode_id']==self.episode and type(q['origin_native'])is int and q['origin_native']==0 and abs(q['origin_sim_time']-a['sim_time'])<=1e-8 and q['receipt_sha256']==digest(query_receipt)and q['state_sha256']==state_digest(a),'FOREIGN_OR_STALE_QUERY'
   assert type(q['query_sequence'])is int and q['query_sequence']==0 and type(q['query_nonce'])is str and len(q['query_nonce'])>=16 and all(type(q[k])is str and len(q[k])==64 for k in ['source_freeze_sha256','numerical_admission_sha256']),'QUERY_AUTHORITY_BINDING_SHAPE'
   assert plan['success']is True and type(plan['status'])is int and plan['status']==0 and plan['native_author_PRIEST']is False,'SOLVER_STATUS_OR_IDENTITY'
   h=plan['interval_s'];v=plan['speeds'];k=plan['curvatures'];p=plan['rear_poses'];assert h==.5 and len(v)==21 and len(k)==20 and len(p)==21,'PROFILE_SHAPE'
   assert all(finite(x)for x in v+k)and all(type(row)is list and len(row)==3 and all(finite(x)for x in row)for row in p),'PROFILE_FINITE'
   assert min(v)>=0 and max(v)<=VMAX+1e-12 and max(abs(x)for x in k)<=KMAX+1e-12 and max(abs(b-a)/h for a,b in zip(v,v[1:]))<=AMAX+1e-12,'PROFILE_BOUNDS'
   assert max(abs(x-y)for x,y in zip(p[0],rear(a)))<=1e-12 and abs(v[0]-a['body'][3])<=1e-12,'MEASURED_INITIAL_BOUNDARY'
   assert abs(v[-1])+abs(v[-2])<=1e-12,'ENDPOINT_REST'
   for i in range(20):assert max(abs(x-y)for x,y in zip(arc(p[i],v[i],v[i+1],k[i],h,h),p[i+1]))<=1e-8,'IDEAL_KINEMATIC_RESIDUAL'
   self.plan=copy.deepcopy(plan);self.plan_sha=digest(plan);self.origin_native=0;self.origin_time=a['sim_time'];self.current_state=state_digest(b);self.last_receipt=digest(current_receipt);self.last_after=current_receipt['after_monotonic'];self.installed_steering=copy.deepcopy(b['steering']);self.installed_memory=copy.deepcopy(b['controller_memory']);return dict(profile_sha256=self.plan_sha,original_origin_native=0,physical_authority=False)
  except BaseException:self.poisoned=True;raise
 def at(self,native):
  assert type(native)is int and 0<=native<1000,'PROFILE_HORIZON_EXPIRED';p=self.plan;i=min(19,native//50);local=(native-i*50)*DT;v=p['speeds'][i]+(p['speeds'][i+1]-p['speeds'][i])*local/p['interval_s'];k=p['curvatures'][i]
  pose=arc(p['rear_poses'][i],p['speeds'][i],p['speeds'][i+1],k,local,p['interval_s']);return pose,v,k
 def requests(self,origin,count):
  out=[]
  for n in range(origin,origin+count):
   _,v,k=self.at(n);assert 0<=v<=VMAX+1e-12 and abs(k)<=KMAX+1e-12,'COMMAND_DOMAIN'
   out.append([0.,0.,False]if v<.005 else[v,v*k,False])
  return out
 def propose(self,receipt):
  try:
   self.alive();assert self.plan is not None and self.pending is None,'UNINSTALLED_OR_PENDING';p=measured(receipt,self.expected)
   assert state_digest(p)==self.current_state,'UNCOMMITTED_CURRENT_STATE';assert digest(receipt)==self.last_receipt or receipt['before_monotonic']>=self.last_after,'ACQUISITION_CLOCK_REVERSED';self.last_receipt=digest(receipt);self.last_after=receipt['after_monotonic'];pose,v,k=self.at(self.expected);measured_rear=rear(p)
   assert math.hypot(measured_rear[0]-pose[0],measured_rear[1]-pose[1])<=.04 and abs(angle(measured_rear[2]-pose[2]))<=.035,'IDEAL_REFERENCE_TRACKING_ONLY'
   prefix=self.requests(self.expected,5);shadow=self.requests(self.expected,10);token=digest(dict(episode=self.episode,native=self.expected,receipt=digest(receipt),profile=self.plan_sha,prefix=prefix))
   self.pending=dict(token=token,native=self.expected,origin_packet_sha256=digest(p),prefix=prefix,shadow=shadow,proof_verified=False,origin_steering=copy.deepcopy(p['steering']),origin_controller_memory=copy.deepcopy(p['controller_memory']))
   return dict(token=token,origin_native=self.expected,original_plan_origin_native=self.origin_native,elapsed_s=self.expected*DT,requests=copy.deepcopy(prefix),shadow_requests=copy.deepcopy(shadow),required_stop_native=2200,origin_packet_sha256=digest(p),profile_sha256=self.plan_sha,physical_authority=False)
  except BaseException:self.poisoned=True;raise
 def verify_response(self,token,proofs):
  try:
   self.alive();p=self.pending;assert p is not None and token==p['token']and not p['proof_verified'],'MISSING_OR_REUSED_RESPONSE_BINDING';assert type(proofs)is list and len(proofs)==2,'RESPONSE_PROOF_COUNT'
   for row,label,head in zip(proofs,['shadow','admission'],[p['shadow'],p['prefix']]):
    assert set(row)=={'label','origin_packet_sha256','requests_sha256','native','passed','checks','arrays_sha256'},'PROOF_SCHEMA'
    assert row['label']==label and row['origin_packet_sha256']==p['origin_packet_sha256']and row['requests_sha256']==digest(head+[[0.,0.,False]for _ in range(2200)])and row['native']==len(head)+2200,'PROOF_WRONG_ORIGIN_OR_REQUESTS'
    assert row['passed']is True and type(row['checks'])is dict and all(x is True for x in row['checks'].values())and set(row['checks'])==RESPONSE_CHECKS,'ORIGINAL_RESPONSE_NOT_PASSED'
    assert type(row['arrays_sha256'])is str and len(row['arrays_sha256'])==64,'MISSING_PREDICTION_ARRAY_BINDING'
   p['proof_verified']=True;return dict(token=token,response_binding_verified=True,physical_authority=False)
  except BaseException:self.poisoned=True;raise
 def commit(self,token,receipt,applied_rows):
  try:
   self.alive();p=self.pending;assert p is not None and token==p['token']and p['proof_verified'],'UNPROVED_OR_FOREIGN_COMMIT';b=measured(receipt,p['native']+5);assert receipt['before_monotonic']>=self.last_after,'COMMIT_ACQUISITION_CLOCK_REVERSED'
   assert type(applied_rows)is list and len(applied_rows)==5,'PARTIAL_PREFIX'
   for i,row in enumerate(applied_rows):assert set(row)=={'episode_id','before_native','request','applied'}and row['episode_id']==self.episode and row['before_native']==p['native']+i and row['request']==p['prefix'][i]and row['applied']is True,'APPLIED_PREFIX_MISMATCH'
   self.expected+=5;self.commits+=1;self.current_state=state_digest(b);self.last_receipt=digest(receipt);self.last_after=receipt['after_monotonic'];self.previous=dict(token=token,applied_prefix_sha256=digest(applied_rows),end_native=self.expected,original_plan_origin_native=self.origin_native);self.pending=None;return copy.deepcopy(self.previous)
  except BaseException:self.poisoned=True;raise
 def close(self):self.closed=True
