"""Current-rest query to original ideal equations. No optimizer or physical import."""
from pathlib import Path
import json,hashlib,importlib.util,sys,math,copy
R=Path(__file__).resolve().parents[2]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
cursor=load('C2180_current_origin_cursor_contract',R/'experiments/v2179_current_plan_cursor/cursor.py')
base=load('C2180_unchanged_projection_equations',R/'experiments/v2177_priest_vector_orientation/collocation.py')
np=base.np
PUBLIC=R/'experiments/v855_renewal_worker/KNOWN_FIELD.json'
# Actual expected public content is pinned by future SOURCE; explicit exact file
# equality prevents private dynamic geometry being added to a request.
def known():return json.loads(PUBLIC.read_text())
def validate(frame):
 assert set(frame)=={'schema','episode_id','query_sequence','query_nonce','source_freeze_sha256','numerical_admission_sha256','receipt','public_known','public_known_sha256','whole_goal_xy'},'CURRENT_QUERY_FIELDS'
 assert frame['schema']=='FRESH_REST_ORIENTATION_PROJECTION_V1'and type(frame['episode_id'])is str and frame['episode_id']and type(frame['query_sequence'])is int and frame['query_sequence']==0,'CURRENT_QUERY_ID'
 assert type(frame['query_nonce'])is str and len(frame['query_nonce'])>=16,'MISSING_FRESH_QUERY_NONCE'
 assert all(type(frame[n])is str and len(frame[n])==64 for n in ['source_freeze_sha256','numerical_admission_sha256']),'ADMISSION_BINDING_SHAPE'
 assert frame['public_known']==known()and frame['public_known_sha256']==hashlib.sha256(PUBLIC.read_bytes()).hexdigest(),'PUBLIC_GEOMETRY_ONLY'
 assert frame['whole_goal_xy']==[4.,-2.],'ORIGINAL_WHOLE_GOAL_MUST_NOT_BE_REPLACED'
 packet=cursor.measured(frame['receipt'],0);assert abs(packet['body'][3])+abs(packet['body'][4])+abs(packet['body_lateral'])<=1e-12,'REST_ONLY_APPLICABILITY_NO_SPEED_RESET'
 return copy.deepcopy(packet)

class FreshProjection(base.Projection):
 def __init__(self,frame):
  self.input_packet=validate(frame);super().__init__(copy.deepcopy(frame['public_known']));start=cursor.rear(self.input_packet);theta=start[2];c=math.cos(theta);s=math.sin(theta)
  for a in [self.initial_full,self.reference]:
   for i in range(self.N+1):
    u=float(a[3*i]+4.3);v=float(a[3*i+1]+2.);t=float(a[3*i+2]);a[3*i:3*i+3]=[start[0]+c*u-s*v,start[1]+s*u+c*v,theta+t]
  self.initial=self.initial_full[self.free].copy();self.frame=copy.deepcopy(frame)
 def proposal(self,z,*,success,status):
  assert success is True and type(status)is int and status==0,'NOT_AN_ACCEPTED_OPTIMIZER_RETURN'
  v=self.evaluate(z);p=self.input_packet;f=self.frame
  assert float(abs(v['equalities']).max())<=1e-8 and float(v['inequalities'].min())>=-1e-8 and v['minimum_sampled_clearance']>=base.geometry.REQUIRED,'ORIGINAL_MATH_GATE_REQUIRED'
  mask=np.ones(len(v['inequalities']),dtype=bool);width=len(base.geometry.feature([-4.,-2.,0.],self.known)[0]);mask[(self.N+1)*width+np.arange(self.N)*(width+1)+width]=False;assert float((v['inequalities'][mask]-1e-7).min())>=-1e-8,'FIXED_STRONGER_PROPOSAL_GEOMETRY'
  lo,hi=self.bounds();assert np.isfinite(z).all()and(np.asarray(z)>=lo-1e-10).all()and(np.asarray(z)<=hi+1e-10).all(),'ORIGINAL_VARIABLE_BOUNDS'
  query=dict(episode_id=f['episode_id'],origin_native=p['native_tick'],origin_sim_time=p['sim_time'],receipt_sha256=cursor.digest(f['receipt']),state_sha256=cursor.state_digest(p),query_sequence=f['query_sequence'],source_freeze_sha256=f['source_freeze_sha256'],numerical_admission_sha256=f['numerical_admission_sha256'],query_nonce=f['query_nonce'])
  return dict(query=query,success=True,status=0,native_author_PRIEST=False,interval_s=self.h,speeds=v['speeds'].tolist(),curvatures=v['curvatures'].tolist(),rear_poses=v['poses'].tolist())
