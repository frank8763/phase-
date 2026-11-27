"""Actual wrapper control-flow seam, toy arrays only, no model/NLP/physics."""
import json,sys,types,copy,math
from pathlib import Path
from context import R,C,SOURCE as S,load,put
import numpy as np
NAV=load('full_route_wrapper_under_test',C/'navigation.py')
original_load=NAV.load;original_read=NAV.read
known={'toy_explicit_software_fixture':True};passed=[]
def test(label,*,goal=1.,cusp=False,fail=None,limit=None):
 saved={};current={};counter={'queries':0,'plans':0};plan=[dict(gear=1,poses=[[-.3,0.,0.],[4.,0.,0.]])]
 if cusp:plan=[dict(gear=1,poses=[[-.3,0.,0.],[-.3,0.,0.]]),dict(gear=-1,poses=[[-.3,0.,0.],[4.,0.,0.]])]
 class V:
  count=0
  def __init__(self):self.d=types.SimpleNamespace(time=0.);self.adapter=types.SimpleNamespace(parked_target=None);self.x=0.
  def body(self):return [self.x,0.,0.,0.,0.]
  def step(self,v,w,stale):self.count+=1;self.d.time+=.01;self.x+=.08 if v else 0.
  def scan(self):return dict(native_tick=self.count,time=self.d.time)
 v=V()
 def packet(v):return dict(body=v.body(),native_tick=v.count,sim_time=v.d.time,dynamic_discovered=False)
 def state(p):return np.r_[p['body'][:3],np.zeros(5)]
 class E:
  first=None
  def __init__(self,*_):pass
  def update(self,z):self.last_scan=z
 def proof(q,setup,p,requests,*_):
  ss=np.tile(state(p),(len(requests)+1,1));ss[:,0]+=np.r_[0.,np.cumsum([.08 if z[0]else 0. for z in requests])]
  z=dict(passed=fail!='shadow',original_whole_checks={'goal_upper':fail!='goal'},native=len(requests),origin_packet=p)
  return z,ss,np.zeros((len(requests),4)),np.zeros((len(requests)+1,5))
 class Client:
  def __init__(self,*_):pass
  def query(self,*_):counter['queries']+=1;return dict(proposal=None if fail=='numeric'else dict(raw_request=[.08,0.,False],origin_native=v.count,actual_execution_permitted=False))
  def close(self):pass
 def route(*_args,**_kwargs):counter['plans']+=1;return np.column_stack([np.linspace(-.3,4,30),np.zeros((30,2)),np.ones(30)]),{}
 def shim(n,p):
  if p==C/'observation.py':return types.SimpleNamespace(scan_only=lambda z,*_:z,acquire=lambda v,*_:dict(packet=packet(v)))
  if p==C/'response.py':return types.SimpleNamespace(prove=proof)
  if p.name=='causal.py':return types.SimpleNamespace(Evidence=E)
  if p.name=='observed_route.py':return types.SimpleNamespace(propose=route,revalidate=lambda *_a,**_k:(fail!='route',{}))
  if p.name=='segments.py':return types.SimpleNamespace(split=lambda _:copy.deepcopy(plan),validate=lambda *_a,**_k:(fail!='handoff',{}))
  if p==C/'nominal.py':return types.SimpleNamespace(reanchor=lambda p,s:s)
  if p==C/'current_request.py':return types.SimpleNamespace(build=lambda *_a,**_k:dict(current=dict(native=v.count)))
  if p==C/'native_client.py':return types.SimpleNamespace(Client=Client)
  return original_load(n,p)
 def read(p):
  if p.name=='SETUP.json':return dict(known=known)
  if p.name=='KNOWN_FIELD.json':return known
  return saved[p.name]
 def save(n,z):assert n not in saved or n=='FILTER_CONTINUOUS_PROGRESS.json';saved[n]=copy.deepcopy(z)
 binding=dict(q=types.SimpleNamespace(np=np,initial=lambda p:dict(state=state(p))),packet=packet,predictive_arrays=types.SimpleNamespace(persist=lambda *_:{}),old=types.SimpleNamespace(previous=types.SimpleNamespace(stopped=lambda _:True)))
 previous=NAV.MAX_QUERIES
 if limit:NAV.MAX_QUERIES=limit
 try:
  NAV.load=shim;NAV.read=read
  try:result=NAV.run(v,binding,dict(goal_xy=[goal,0.],run_id='PURE_SOFTWARE_FLOW'),{},Path('/not_written'),save,types.SimpleNamespace(admit=lambda *_:None),lambda *_:None)
  except AssertionError as error:
   assert fail is not None or limit
   assert fail is None or {'goal':'WHOLE_GOAL_STOP','numeric':'NUMERICAL_OR_HARD','handoff':'GEAR_HANDOFF','route':'PATH_REVALIDATION','shadow':'COMPLETE_STOP'}[fail]in str(error),repr(error)
   result=dict(passed=False,expected_error=str(error))
  else:assert not fail and not limit and result['whole_goal_with_original_stop']and result['actual_original_goal_reached']
  if cusp and fail!='route':assert saved['cycle_000000_executed.json']['kind']=='segment_stop'
  if fail in ['numeric','route','shadow']:assert v.count==0
  if fail=='goal':assert not any(z.get('kind')=='whole_goal_stop'for z in saved.values()if isinstance(z,dict))
  passed.append(dict(case=label,software_tick_counter=v.count,queries=counter['queries'],result=result))
 finally:NAV.load=original_load;NAV.read=original_read;NAV.MAX_QUERIES=previous
for label,options in [('whole_goal_positive',{}),('stop_handoff_then_goal',dict(cusp=True)),('original_goal_gate_refusal',dict(goal=.2,fail='goal')),('numeric_refusal',dict(fail='numeric')),('capture_handoff_refusal',dict(cusp=True,fail='handoff')),('static_route_refusal',dict(fail='route')),('full_shadow_refusal',dict(fail='shadow')),('finite_query_limit',dict(goal=20.,limit=3))]:test(label,**options)
put(S/'FULL_ROUTE_SOFTWARE_FLOW.json',dict(passed=True,cases=passed,models=0,NLP_queries=0,physics=0,replay=0,uses_toy_arrays_not_scientific_predictions=True,production_navigation_function_executed=True));print(json.dumps(dict(passed=True,cases=len(passed),models=0)))
