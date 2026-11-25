"""Real framing/subprocess seam and navigation branch harness, no numerical plant."""
from context import R,C,O,load,read,put,sha
import ast,base64,hashlib,json,os,subprocess,sys,tempfile,time,zlib

def check():
 import numpy as np
 from types import SimpleNamespace as NS
 from messages import encode,decode
 out=O/('software_'+str(len(list(O.glob('software*')))));out.mkdir(exist_ok=False);negative=[]
 payload=dict(request=dict(native_tick=5,values=[.1,-0.,1e-300]),map=dict(cells=[0,253,254,255]*3600),path=[[0.,0.,0.],[1.,0.,0.]])
 frame=encode(payload);assert decode(frame)==payload and len(frame)<len(json.dumps(payload))
 wrong=json.loads(frame);wrong['sha256']='0'*64
 cases={'SHA':json.dumps(wrong),'truncated':frame[:-20],'unknown_field':json.dumps(dict(json.loads(frame),truth=1)),'extra_zlib':json.dumps(dict(json.loads(frame),payload=base64.b64encode(zlib.compress(b'{}')+b'extra').decode())),'zip_bomb':json.dumps(dict(schema='RPP_FILE_FRAME_V1',sha256='0'*64,payload=base64.b64encode(zlib.compress(b'x'*(1024**2+1))).decode()))}
 for name,value in cases.items():
  try:decode(value)
  except (AssertionError,ValueError,zlib.error):negative.append(name)
  else:raise AssertionError('FRAME_NEGATIVE_ACCEPTED:'+name)
 # Actual original OutputBoundary, append after child has observed EOF and
 # deliberately split a frame between writes. No writable pipe is introduced.
 boundary=load('same_original_output_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');charged=[];path=out/'append.jsonl'
 script="""import sys,time
sys.path.insert(0,sys.argv[1]);from messages import decode
pending='';seen=[];end=time.monotonic()+5
print('READY',flush=True)
while time.monotonic()<end:
 line=sys.stdin.readline()
 if not line:time.sleep(.002);continue
 pending+=line;assert len(pending)<=1024**2
 if not pending.endswith('\\n'):continue
 value=decode(pending);pending='';seen.append(value)
 if value.get('close'):assert seen==[{'native':0},{'native':5},{'close':True}];print('PASS',flush=True);break
else:raise AssertionError('APPEND_EOF_TIMEOUT')
"""
 def charge(p,n):assert p.is_relative_to(out);charged.append(n)
 with boundary.OutputBoundary(out,charge):
  path.write_text(encode(dict(native=0)))
  with path.open('rb')as f:
   child=subprocess.Popen(['/usr/bin/python3.12','-I','-B','-S','-c',script,str(C)],stdin=f,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   assert child.stdout.readline()==b'READY\n';time.sleep(.03);value=encode(dict(native=5));half=len(value)//2
   with path.open('a')as w:w.write(value[:half]);w.flush()
   time.sleep(.03)
   with path.open('a')as w:w.write(value[half:]+encode(dict(close=True)))
   stdout,stderr=child.communicate(timeout=5)
  assert child.returncode==0 and stdout==b'PASS\n'and not stderr
 # Execute the production loop with explicitly synthetic dynamics/modules.
 # This establishes branch/control ordering only, not safety/numerical truth.
 nav=load('RPP_production_navigation_software',C/'navigation.py');tests=[]
 def exercise(mode):
  records={};requests=[];queries=[]
  class Vehicle:
   count=0
   adapter=NS(parked_target=None)
   def scan(self):return {}
   def step(self,vr,wr,stale):self.count+=1
   @property
   def d(self):return NS(time=.01*self.count)
  v=Vehicle()
  def packet():return dict(native_tick=v.count,body=[(-.6+.025*min(v.count,10))if mode=='whole'else(-.5+.05*min(v.count,5)),0.,0.,0.,0.,0.],sim_time=.01*v.count)
  def state(p):s=np.zeros(8);s[:3]=p['body'][:3];return s
  observation=NS(scan_only=lambda z,k,t:dict(native_tick=k),acquire=lambda *a:dict(packet=packet(),packet_sha256=nav.digest(packet())))
  class Evidence:
   first=None;snapshots=[]
   def __init__(self,*a):pass
   def update(self,*a):pass
  def prove(q,setup,p,rr,goal,cs):
   start=p['native_tick'];ss=[]
   for i in range(len(rr)+1):
    s=np.zeros(8);s[0]=(-.6+.025*min(start+i,10))if mode=='whole'else(-.5+.05*min(start+i,5));ss.append(s)
   requests.append(len(rr));return dict(passed=mode!='unsafe',original_whole_checks=dict(goal_upper=True)),np.asarray(ss),np.zeros((len(rr),4)),np.zeros((len(rr)+1,5))
  class Wire:
   def __init__(self,*a,**kw):pass
   def request(self,receipt,**kw):return dict(native_tick=receipt['packet']['native_tick'])
   def reply(self,*a,**kw):return {}
   def close(self):pass
  class Client:
   def __init__(self,*a):pass
   def query(self,request,*a):queries.append(request['native_tick']);return dict(passed=True,origin_native_tick=request['native_tick'],input_sha256=nav.digest(request),solver_calls=len(queries),twist=[.2 if mode=='domain'else .1,0.])
   def close(self):records['peer_closed']=True
  class Frontend:
   def __init__(self,*a,**kw):pass
   def build(self,*a):return {}
  front=NS(Frontend=Frontend,PUBLIC=R/'software_public',PARAMS=R/'software_params')
  selected=dict(gear=1,poses=[[-.8,0.,0.],[-.55 if mode=='cusp'else 8.,0.,0.]])
  fake_route=NS(propose=lambda *a,**kw:(np.zeros((20,4)),{}),revalidate=lambda *a,**kw:(True,{}));fake_segments=NS(split=lambda p:[selected,selected],direction_allowed=lambda v,g:True,validate=lambda *a,**kw:(False,dict(reason='SYNTHETIC_CUSP_REFUSAL')))
  modules={'observation.py':observation,'response.py':NS(prove=prove),'causal.py':NS(Evidence=Evidence),'observed_route.py':fake_route,'segments.py':fake_segments,'wire.py':NS(CurrentWire=Wire),'current_map.py':front,'native_client.py':NS(Client=Client)}
  original_load=nav.load;original_read=nav.read
  nav.load=lambda n,p:modules[p.name];nav.read=lambda p:dict(known={})
  binding=dict(q=NS(np=np,initial=lambda p:dict(state=state(p))),packet=lambda v:packet(),old=NS(previous=NS(stopped=lambda p:True)),predictive_arrays=NS(persist=lambda *a:{}))
  task=dict(goal_xy=[10. if mode=='cusp'else 0.,0.],maximum_control_native=57600,run_id='software')
  try:
   answer=nav.run(v,binding,task,{'software_public':'x','software_params':'y'},out,lambda n,z:records.update({n:z}),None,lambda *a:None)
   assert mode=='whole'and answer['whole_goal_with_original_stop']and v.count==2210 and requests==[2205,2205,2200]and queries==[0,5]
  except AssertionError as e:
   expected={'domain':'RPP_RAW_COMMAND_DOMAIN_REFUSED','unsafe':'RPP_CURRENT_CYCLE_COMPLETE_STOP_REFUSED','cusp':'RPP_MEASURED_CUSP_CAPTURE_REFUSED'};assert mode in expected and str(e)==expected[mode],(mode,str(e));assert v.count==(2205 if mode=='cusp'else 0)
  finally:nav.load=original_load;nav.read=original_read
  assert records['peer_closed'];tests.append(dict(mode=mode,actual_fake_steps=v.count,queries=queries,proof_lengths=requests))
 for mode in ['whole','domain','unsafe','cusp']:exercise(mode)
 for p in C.glob('*.py'):ast.parse(p.read_text())
 proof=dict(passed=True,framing_lossless=True,negative_frames=negative,original_boundary_append_EOF_partial_line_roundtrip=True,charged_bytes=charged,navigation_branch_tests=tests,branch_tests_use_synthetic_modules_only=True,old_vehicle_component_reused_without_rerun=True,models=0,RPP_DLL=0,controller_calls=0,physical_native=0,replay_native=0)
 put(O/'SOFTWARE_CHECK_PROOF.json',proof);return proof
if __name__=='__main__':print(json.dumps(check()))
