"""Explicit synthetic receipts/proofs only. No numerical backend or plant import."""
from pathlib import Path
import copy,json,os,math,time,hashlib,signal,datetime,sys
from cursor import Cursor,arc,rear,digest,state_digest,measured,DT
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
assert os.sched_getaffinity(0)=={0}and not(S/'RESULT.json').exists()
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('CURSOR_SOFTWARE60S')));signal.alarm(60)
count=[0]
def fixture(heading=0.,initial_speed=0.):
 count[0]+=1;eid='synthetic-software-only-'+str(count[0]);h=.5;v=[0.,0.,.05]+[.1]*13+[.05,.025,0.,0.,0.];assert len(v)==21
 if initial_speed:v[0]=v[1]=initial_speed
 poses=[[-4.-.3*math.cos(heading),-2.-.3*math.sin(heading),heading]];k=[0.]*20
 for i in range(20):poses.append(arc(poses[-1],v[i],v[i+1],0.,h,h))
 def packet(n):
  i=min(19,n//50);local=(n-i*50)*.01;pose=arc(poses[i],v[i],v[i+1],0.,local,h);speed=v[i]+(v[i+1]-v[i])*local/h;yaw=pose[2]
  return dict(body=[pose[0]+.3*math.cos(yaw),pose[1]+.3*math.sin(yaw),yaw,speed,0.],body_lateral=0.,native_tick=n,sim_time=.01*n,body_measured_at=0.,sent_at=0.,dynamic_discovered=False,steering=dict(position=[0.,0.],velocity=[0.,0.],native_tick=n,measured_at=0.),controller_memory=dict(last_ctrl=[n*.001,0.,0.,0.],integral=n*.0001),coupled_episode=False,steering_motion_active=False)
 def receipt(n,acq=0):
  p=packet(n);start=100.+n+acq*.01;t=start+.001;p['body_measured_at']=p['sent_at']=p['steering']['measured_at']=t
  return dict(schema='DWA_CURRENT_ACQUISITION_V1',packet_acquisitions=1,packet=p,packet_sha256=digest(p),before_monotonic=start,after_monotonic=start+.002,scan=dict(native_tick=n,time=.01*n,xy=p['body'][:2],yaw=p['body'][2],ranges=[3.]*32))
 a=receipt(0,0);b=receipt(0,1);q=dict(episode_id=eid,origin_native=0,origin_sim_time=0.,receipt_sha256=digest(a),state_sha256=state_digest(a['packet']),query_sequence=0,source_freeze_sha256='a'*64,numerical_admission_sha256='b'*64,query_nonce='SYNTHETIC-NOT-ACTUAL-'+eid)
 plan=dict(query=q,success=True,status=0,native_author_PRIEST=False,interval_s=.5,speeds=v,curvatures=k,rear_poses=poses)
 return eid,plan,a,b,receipt

def proofs(proposal):
 checks={n:True for n in ['full2200','full_raw_geometry','terminal_full_cycle_hold','terminal_body_rest','terminal_steering_rest']};out=[]
 for label,head in [('shadow',proposal['shadow_requests']),('admission',proposal['requests'])]:out.append(dict(label=label,origin_packet_sha256=proposal['origin_packet_sha256'],requests_sha256=digest(head+[[0.,0.,False]for _ in range(2200)]),native=len(head)+2200,passed=True,checks=checks.copy(),arrays_sha256='c'*64))
 return out

def applied(eid,p):return[dict(episode_id=eid,before_native=p['origin_native']+i,request=row.copy(),applied=True)for i,row in enumerate(p['requests'])]

eid,plan,a,b,receipt=fixture();c=Cursor(eid);installed=c.install(plan,a,b);records=[]
for cycle in range(16):
 r=b if cycle==0 else receipt(cycle*5);p=c.propose(r);assert p['original_plan_origin_native']==0 and p['origin_native']==cycle*5 and not p['physical_authority'];c.verify_response(p['token'],proofs(p));z=c.commit(p['token'],receipt(cycle*5+5),applied(eid,p));assert z['end_native']==(cycle+1)*5;records.append(dict(origin=p['origin_native'],elapsed=p['elapsed_s'],first_request=p['requests'][0],last_request=p['requests'][-1]))
assert c.expected==80 and c.commits==16 and c.pending is None and c.origin_native==0
assert all(row['first_request']==[0.,0.,False]for row in records[:11])and any(row['first_request'][0]>0 for row in records[11:]);assert c.plan_sha==digest(plan)
assert all(c.requests(0,5)==[[0.,0.,False]]*5 for _ in range(16)) # naive restarted-time algebra only, not a second cursor/plant
c.close()
extras=[]
for heading,speed in [(math.pi/2,0.),(.23,.01)]:
 e,p,a,b,r=fixture(heading,speed);t=Cursor(e);t.install(p,a,b);out=t.propose(b);extras.append(dict(rotated_heading=heading,initial_speed=speed,proposal=out['requests'][0],origin_state_kept=True));t.close()
negative=[]
def reject(name,stage,mutate):
 e,p,a,b,r=fixture();t=Cursor(e)
 try:
  if stage=='install':mutate(p,a,b);t.install(p,a,b)
  else:
   t.install(p,a,b);x=t.propose(b)
   if stage=='propose':mutate(t,x,r);t.propose(b)
   elif stage=='proof':z=proofs(x);mutate(z);t.verify_response(x['token'],z)
   elif stage=='commit':
    t.verify_response(x['token'],proofs(x));rows=applied(e,x);rr=r(5);mutate(rows,rr);t.commit(x['token'],rr,rows)
   elif stage=='unproved_commit':t.commit(x['token'],r(5),applied(e,x))
   elif stage=='restart':t.install(p,a,b)
   elif stage=='horizon':t.pending=None;t.expected=1000;t.current_state=state_digest(r(1000)['packet']);t.propose(r(1000))
  raise AssertionError('EXPECTED_REFUSAL_NOT_RAISED:'+name)
 except (AssertionError,ValueError,KeyError,IndexError,TypeError)as ex:
  assert not str(ex).startswith('EXPECTED_REFUSAL_NOT_RAISED');assert t.poisoned
  try:t.alive()
  except AssertionError:pass
  else:raise AssertionError('POISONED_CURSOR_RESUMED')
  negative.append(dict(name=name,first_error=repr(ex),poisoned=True))

def rehash(r):r['packet_sha256']=digest(r['packet'])
for name,fn in [
 ('foreign_episode',lambda p,a,b:p['query'].__setitem__('episode_id','foreign')),
 ('old_saved_plan_without_query',lambda p,a,b:p.pop('query')),
 ('query_native',lambda p,a,b:p['query'].__setitem__('origin_native',5)),
 ('query_native_bool',lambda p,a,b:p['query'].__setitem__('origin_native',False)),
 ('query_receipt_hash',lambda p,a,b:p['query'].__setitem__('receipt_sha256','f'*64)),
 ('query_state_hash',lambda p,a,b:p['query'].__setitem__('state_sha256','f'*64)),
 ('query_sequence',lambda p,a,b:p['query'].__setitem__('query_sequence',1)),
 ('missing_sourcebinding',lambda p,a,b:p['query'].__setitem__('source_freeze_sha256','')),
 ('status8',lambda p,a,b:p.__setitem__('status',8)),
 ('nativeauthorclaim',lambda p,a,b:p.__setitem__('native_author_PRIEST',True)),
 ('unknownprofiletruth',lambda p,a,b:p.__setitem__('actor_truth',[0.,0.])),
 ('shape',lambda p,a,b:p['speeds'].pop()),
 ('nonfinite',lambda p,a,b:p['speeds'].__setitem__(3,float('nan'))),
 ('speedbound',lambda p,a,b:p['speeds'].__setitem__(3,.2)),
 ('curvaturebound',lambda p,a,b:p['curvatures'].__setitem__(3,1.)),
 ('initialpose',lambda p,a,b:p['rear_poses'][0].__setitem__(0,-3.)),
 ('initialspeed',lambda p,a,b:p['speeds'].__setitem__(0,.01)),
 ('kinematicresidual',lambda p,a,b:p['rear_poses'][3].__setitem__(0,-3.)),
 ('terminalrest',lambda p,a,b:p['speeds'].__setitem__(-1,.01)),
 ('currentmemorychanged',lambda p,a,b:(b['packet']['controller_memory'].__setitem__('integral',1.),rehash(b))),
 ('currentencoderchanged',lambda p,a,b:(b['packet']['steering']['position'].__setitem__(0,.01),rehash(b))),
 ('currentnativechanged',lambda p,a,b:(b['packet'].__setitem__('native_tick',5),rehash(b))),
 ('currenttimechanged',lambda p,a,b:(b['packet'].__setitem__('sim_time',.05),rehash(b))),
 ('unknownpackettruth',lambda p,a,b:(b['packet'].__setitem__('actor_truth',[0.,0.]),rehash(b))),
 ('scanhiddentruth',lambda p,a,b:b['scan'].__setitem__('actor_truth',[0.,0.])),
 ('postsolveclockreversed',lambda p,a,b:b.__setitem__('before_monotonic',99.)),
]:reject(name,'install',fn)
reject('pending_proposal','propose',lambda *_:None)
for name,fn in [('wrongorigin',lambda z:z[0].__setitem__('origin_packet_sha256','f'*64)),('wrongrequests',lambda z:z[0].__setitem__('requests_sha256','f'*64)),('missingtail',lambda z:z[0].__setitem__('native',10)),('refused_response',lambda z:z[0].__setitem__('passed',False)),('missingcheck',lambda z:z[0]['checks'].pop('full_raw_geometry')),('failedcheck',lambda z:z[0]['checks'].__setitem__('full_raw_geometry',False)),('arraysmissing',lambda z:z[0].__setitem__('arrays_sha256',''))]:reject(name,'proof',fn)
for name,fn in [('partialprefix',lambda rows,r:rows.pop()),('wrongapplied',lambda rows,r:rows[0].__setitem__('applied',False)),('foreignapplied',lambda rows,r:rows[0].__setitem__('episode_id','foreign')),('wrongrequest',lambda rows,r:rows[0]['request'].__setitem__(0,.1)),('skippednative',lambda rows,r:rows[0].__setitem__('before_native',2)),('wrongcommitclock',lambda rows,r:(r['packet'].__setitem__('sim_time',.1),rehash(r)))]:reject(name,'commit',fn)
reject('unproved_commit','unproved_commit',lambda *_:None);reject('reinstall','restart',lambda *_:None);reject('expiredhorizon','horizon',lambda *_:None)
try:Cursor(eid)
except AssertionError:negative.append(dict(name='duplicate_episode_instance',refused=True))
else:raise AssertionError('DUPLICATE_EPISODE_ALLOWED')
# A closed actual receipt is only parsed as a historical fixture, never a fresh producer.
old=R/'runs/v2176_sccr_common_plant_component/components/SCCR/actual/cycle_000000_origin.json';historical=json.loads(old.read_text())['receipt'];measured(historical,0)
assert not any(n in sys.modules for n in ['numpy','scipy','torch','mujoco','jax'])
x=dict(passed=True,closed=True,scope='PURE_SOFTWARE_BINDING_AND_CURSOR_ONLY',committed_prefixes=16,committed_native_protocol_positions=80,first_nonzero_prefix_native=next(row['origin']for row in records if row['first_request'][0]>0),original_plan_origin_kept=0,monotonic_profile_no_restart=True,naive_restarted_time_first_prefix_always_zero=True,records=records,positive_input_variants=extras,negative_cases=negative,negative_count=len(negative),historical_receipt_parser_only=True,all_execution_and_prediction_evidence_is_explicit_synthetic_fixture=True,actual_NLP_NN_models_physics_replay_physicalaudit_Source=0,physical_authority=False,native_author_PRIEST=False,formal_tasks=0,source_sha256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [C/'cursor.py',C/'check.py',C/'PROTOCOL.md',old]},created_at=datetime.datetime.now().astimezone().isoformat());raw=json.dumps(x,indent=2,allow_nan=False)+'\n';assert len(raw.encode())<96*1024;(S/'RESULT.json').write_text(raw);print(json.dumps(dict(passed=True,commits=16,protocol_native=80,negative_cases=len(negative),first_nonzero_prefix_native=x['first_nonzero_prefix_native'],actual_NLP_models_physics=0)))
