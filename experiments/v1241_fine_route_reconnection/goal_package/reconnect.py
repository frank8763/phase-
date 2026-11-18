"""Finite whole-route action reconnection with freshly measured state/time."""
from pathlib import Path
import copy,hashlib,json,time
from .candidate_search import q,np,PreviewGeometry
from .admission import preview

C=Path(__file__).resolve().parents[1];R=C.parents[1]

def generate(x,table,origin,offset,deadline,checkpoint=lambda _:None,*,shadow_origin):
 assert x['setup']['case']['id']=='NORTH_SOUTH' and offset==0
 assert shadow_origin is not None
 bank=json.loads((C/'PROPOSAL_BANK.json').read_text())['items']
 geometry=PreviewGeometry(q.Geometry(x,table),offset)
 engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients'])
 fine_work=0;admissions=0;trials=[];selected=None;best=None;started=time.monotonic()
 wait_upper=min(2000,int(geometry.period/.01))
 cache={};proposals=0
 def evaluate(moving,wait,label):
  nonlocal best,proposals
  assert time.monotonic()<deadline,'FULL_ROUTE_RECONNECTION_DEADLINE'
  key=(tuple(tuple(r)for r in moving),int(wait))
  if key in cache:return cache[key],None
  assert proposals<3200,'FINITE_FULL_ROUTE_PROPOSAL_CAP'
  proposals+=1
  rows=([(0.,0.,int(wait),0)]if wait else[])+copy.deepcopy(moving)+[(0.,0.,2200,0)]
  ss,uu,mm=engine.simulate(origin,rows)
  sh,_,_=engine.simulate(shadow_origin,rows)
  proof=q.proof(geometry,x,ss,uu,q.requests_of(rows),mm)
  shadow=q.proof(geometry,x,sh,uu,q.requests_of(rows),mm)
  margin=min(proof['minimum_raw_m'],shadow['minimum_raw_m'])
  t=dict(id=label,wait=int(wait),margin=float(margin),nominal_passed=bool(proof['passed']and shadow['passed']),
         goal_upper_m=proof['goal_upper_m'],native=len(ss)-1)
  trials.append(t)
  if best is None or (t['nominal_passed'],t['margin'])>(best['nominal_passed'],best['margin']):
   best=t;checkpoint(dict(stage='whole_route_reconnection',proposals=proposals,best=best,cpp_native=engine.native))
  candidate=dict(rows=rows,states=ss,controls=uu,memory=mm,proof=proof,initial_wait=int(wait))
  cache[key]=t;return t,candidate
 def admit(t,candidate):
  nonlocal fine_work,admissions,selected
  if not t['nominal_passed']or t['margin']<q.REQUIRED+.022 or candidate is None:return False
  assert admissions<8,'FINITE_FEEDBACK_ADMISSION_CAP'
  admissions+=1
  a,_=preview(x,table,origin,shadow_origin,offset,candidate,deadline);fine_work+=a['python_native']
  t['admission_passed']=a['passed']
  if not a['passed']:return False
  reserve=min(a['feedback_proof']['minimum_raw_m'],a['continuous_shadow_proof']['minimum_raw_m'])-q.REQUIRED
  t['feedback_reserve_m']=reserve
  if reserve<.022:return False
  a.update(nominal_execution_reserve_m=reserve,required_nominal_reserve_m=.022)
  selected=dict(candidate,admission=a,proposal_id=t['id']);return True
 ranked=[]
 for source in bank:
  assert hashlib.sha256((R/source['source']).read_bytes()).hexdigest()==source['sha256'],'PROPOSAL_SOURCE_CHANGED'
  initial=[]
  for wait in range(0,wait_upper+1,100):
   t,c=evaluate(source['moving_rows'],wait,source['id']+'/original')
   if t['goal_upper_m']<=.45:initial.append(t)
  if initial:ranked.append((max(t['margin']for t in initial),source))
 for _,source in sorted(ranked,key=lambda pair:(-pair[0],pair[1]['id'])):
  assert hashlib.sha256((R/source['source']).read_bytes()).hexdigest()==source['sha256'],'PROPOSAL_SOURCE_CHANGED'
  moving=source['moving_rows'];variants=[('original',copy.deepcopy(moving))]
  for i,row in enumerate(moving):
   for delta in [-25,25,-50,50]:
    if row[2]+delta<=0:continue
    one=copy.deepcopy(moving);one[i][2]+=delta
    assert sum(r[2]for r in one)<=6000
    variants.append((f'segment{i}_{delta:+}',one))
  for variant,rows in variants:
   label=source['id']+'/'+variant;coarse=[]
   for wait in range(0,wait_upper+1,100):
    t,candidate=evaluate(rows,wait,label);coarse.append(t)
    if admit(t,candidate):break
   if selected:break
   valid=[p for p in coarse if p['nominal_passed'] or p['goal_upper_m']<=.45]
   if not valid:continue
   center=max(valid,key=lambda p:p['margin'])['wait']
   for wait in range(max(0,center-100),min(wait_upper,center+100)+1,10):
    t,candidate=evaluate(rows,wait,label)
    if admit(t,candidate):break
   if selected:break
  if selected:break
 # Release full state arrays for rejected alternatives before saving reports.
 result=dict(passed=selected is not None,method='current_state_NS_retained_balanced_seeded_fallback',
   prefix_rows=None,proposal_method='whole_route_fine_single_primitive_duration_reconnection',
   proposals=proposals,admissions=admissions,trials=trials,best=best,
   analytical_cpp_native=engine.native,admission_python_native=fine_work,
   wall_s=time.monotonic()-started,models=0,physical_native=0,physical_eligible=False)
 if selected:result.update(selected)
 return result
