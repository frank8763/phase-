"""Explicit software state machine, no model/controller/path-search imports."""
import copy,types
from context import R,C,load

def check(np):
 nav=load('SVG_fullroute_software_state_machine',C/'navigation.py');saved={};proof_lengths=[];calls=[];closed=[]
 class Vehicle:
  def __init__(self):self.count=0;self.x=0.;self.d=types.SimpleNamespace(time=0.);self.adapter=types.SimpleNamespace(parked_target=None)
  def step(self,v,w,stale):self.count+=1;self.d.time=.01*self.count;self.x+=.2 if v else 0.
  def scan(self):return dict(native_tick=self.count,time=self.d.time)
 v=Vehicle()
 def packet(v):return dict(native_tick=v.count,sim_time=v.d.time,body=[v.x,0.,0.],state=[v.x,0.,0.,0.,0.,0.,0.,0.])
 class Evidence:
  def __init__(self,*a):self.first=None;self.snapshots=[]
  def update(self,z):pass
 class Control:
  def __init__(self,*a,**k):self.pending=None
  def frame(self,np,receipt,**kw):
   assert kw['gear']==1,'SVG_AUTHOR_FORWARD_REFERENCE_ONLY_REVERSE_UNQUALIFIED';assert self.pending is None;self.pending=receipt['packet']['native_tick'];return dict(native=self.pending)
  def proposal(self,raw,**kw):assert self.pending==raw['native'];self.pending=None;return dict(body_request=[.08,0.,False],physical_authority=False,actual_execution_permitted=False)
  def close(self):closed.append('control')
 class Client:
  constructors=0
  def __init__(self,save,frame):Client.constructors+=1;self.first=frame;self.count=0
  def query(self,frame=None):
   frame=frame or self.first;self.count+=1;calls.append(frame['native']);return dict(passed=True,raw=dict(native=frame['native']),counts=dict(constructor_returns=1,author_solve_attempts=self.count,author_solve_returns=self.count))
  def close(self):closed.append('client')
 def prove(q,setup,p,requests,*args):
  proof_lengths.append(len(requests));x=p['body'][0];ss=[np.asarray([x,0.,0.,0.,0.,0.,0.,0.])]
  for command in requests:x+=.2 if command[0]else 0.;ss.append(np.asarray([x,0.,0.,0.,0.,0.,0.,0.]))
  return dict(passed=True,origin_packet=p,original_whole_checks=dict(goal_upper=True)),np.asarray(ss),None,None
 segments=[dict(gear=1,poses=[[-.3,0.,0.],[.7,0.,0.]]),dict(gear=1,poses=[[.7,0.,0.],[1.7,0.,0.]])]
 def replacement(label,path):
  if label=='SVG_current_observation':return types.SimpleNamespace(scan_only=lambda z,*a:z,acquire=lambda v,b,s:dict(packet=packet(v)))
  if label=='SVG_original_response':return types.SimpleNamespace(prove=prove)
  if label=='SVG_original_causal_evidence':return types.SimpleNamespace(Evidence=Evidence)
  if label=='observed_route':return types.SimpleNamespace(propose=lambda *a,**kw:(np.zeros((20,4)),{}),revalidate=lambda *a,**kw:(True,{}))
  if label=='SVG_original_singlegear_segments':return types.SimpleNamespace(split=lambda p:copy.deepcopy(segments),validate=lambda *a,**kw:(True,{}))
  if label=='SVG_qualified_current_control':return types.SimpleNamespace(CurrentControl=Control)
  if label=='SVG_compact_current_evidence':return types.SimpleNamespace(pack=lambda **kw:dict(software_only=True,query=kw['cycle']))
  if label=='SVG_persistent_native_client':return types.SimpleNamespace(Client=Client)
  raise AssertionError('UNEXPECTED_SOFTWARE_FIXTURE_DEPENDENCY:'+label)
 nav.load=replacement;nav.read=lambda p:dict(known={});nav.__dict__['__import__'] if False else None
 # No actual SOURCE exists yet: only this module's import lookup of the freeze
 # digest is replaced. All navigation flow and thresholds remain its real code.
 import context
 oldsha=context.sha;context.sha=lambda p:'software-fixture-freeze'
 binding=dict(q=types.SimpleNamespace(np=np,initial=lambda p:dict(state=p['state'])),packet=packet,old=types.SimpleNamespace(previous=types.SimpleNamespace(stopped=lambda p:True)),predictive_arrays=types.SimpleNamespace(persist=lambda *a:{}))
 try:
  result=nav.run(v,binding,dict(goal_xy=[2.,0.],run_id='explicit-software',maximum_control_native=57600),{},C,lambda n,x:saved.update({n:x}),types.SimpleNamespace(admit=lambda n,label:None),lambda *a:None)
 finally:context.sha=oldsha
 assert result['passed']and result['whole_goal_with_original_stop']and v.count==4410
 assert Client.constructors==1 and calls==[0,2205]and closed==['control','client']
 assert proof_lengths==[2210,2205,2200,2210,2205,2200]
 executed=[x for n,x in saved.items()if n.endswith('_executed.json')]
 assert [x['executed_native']for x in executed]==[5,2200,5,2200]
 return dict(passed=True,explicit_software_vehicle=True,physical_native=0,solver_queries=0,logical_native=4410,persistent_fake_constructors=1,fresh_query_ticks=calls,full_prediction_lengths=proof_lengths,segment_then_whole_stop=True)
