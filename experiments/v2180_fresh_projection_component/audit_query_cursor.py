"""Independent saved query/profile/journal checks. No solve or plant execution."""
from pathlib import Path
import json,hashlib,math

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def audit(out,task,source,np,*,require_complete):
 out=Path(out);read=lambda name:json.loads((out/name).read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();counts=None
 if (out/'PROJECTION_NATIVE_ACCOUNTING.json').exists():counts=read('PROJECTION_NATIVE_ACCOUNTING.json')
 if not(out/'PROJECTION_PROFILE.json').exists():
  assert not require_complete,'MISSING_SUCCESS_PROFILE'
  return dict(passed=True,scope='NO_ACCEPTED_PROFILE_CANONICAL_FAILURE_PRESERVED',profile_present=False,numerical_accounting=counts)
 f=read('PROJECTION_QUERY_FRAME.json');a_bytes=(out/'PROJECTION_OPTIMIZER_ADMISSION.json').read_bytes();a=json.loads(a_bytes);once=read('PROJECTION_PEER_ONCE.json');reply=read('PROJECTION_NATIVE_REPLY.json');close=read('PROJECTION_NATIVE_CLOSED.json');profile=read('PROJECTION_PROFILE.json');q=profile['query'];origin=read('cycle_000000_origin.json')['receipt'];after=read('PROJECTION_POST_SOLVE_ORIGIN.json')
 assert f['receipt']==origin and f['episode_id']==task['run_id']and f['query_sequence']==0 and f['whole_goal_xy']==task['goal_xy'],'QUERY_TASK_OR_RECEIPT'
 assert f['numerical_admission_sha256']==once['admission_sha256']==hashlib.sha256(a_bytes).hexdigest()and once['first_input_sha256']==digest(f),'QUERY_ADMISSION_ONCE'
 assert f['source_freeze_sha256']==a['source_freeze_sha256']and a['worker_sha256']==source['experiments/v2180_fresh_projection_component/peer_entry.py']and a['models_authorized']is False and a['maximum_queries']==1
 assert q['receipt_sha256']==digest(origin)and q['episode_id']==task['run_id']and q['query_nonce']==f['query_nonce']==once['query_nonce']==a['query_nonce']==reply['query_nonce']==close['query_nonce']
 assert reply['proposal']==profile and reply['passed']and close['math_passed']and reply['query_sha256']==digest(f)and reply['NLP_attempted_calls']==reply['NLP_returns']==close['NLP_attempted_calls']==close['NLP_returns']==1 and not reply['inflight_unknown']and not close['inflight_unknown']
 assert reply['raw_return']==read('PROJECTION_NATIVE_RAW_RETURN.json')and reply['raw_return']['success']is True and reply['raw_return']['status']==0
 p0=origin['packet'];p1=after['packet'];assert p0['native_tick']==p1['native_tick']==0 and p0['sim_time']==p1['sim_time']==0 and after['before_monotonic']>=origin['after_monotonic']
 for key in ['body','body_lateral','controller_memory','dynamic_discovered','coupled_episode','steering_motion_active']:assert p0[key]==p1[key]
 for key in ['position','velocity','native_tick']:assert p0['steering'][key]==p1['steering'][key]
 def state_hash(p):
  names={'body','body_lateral','native_tick','sim_time','dynamic_discovered','steering','controller_memory','coupled_episode','steering_motion_active'};z={n:json.loads(json.dumps(p[n]))for n in names};z['steering'].pop('measured_at');return digest(z)
 assert q['state_sha256']==state_hash(p0)==state_hash(p1)
 assert profile['success']is True and profile['status']==0 and profile['native_author_PRIEST']is False and profile['interval_s']==.5
 v=profile['speeds'];k=profile['curvatures'];poses=profile['rear_poses'];assert len(v)==21 and len(k)==20 and len(poses)==21 and np.isfinite(np.asarray(v+k)).all()and np.isfinite(np.asarray(poses)).all()
 assert min(v)>=0 and max(v)<=.1+1e-12 and max(abs(x)for x in k)<=1/1.32+1e-12 and max(abs(y-x)/.5 for x,y in zip(v,v[1:]))<=.1+1e-12 and abs(v[-1])+abs(v[-2])<=1e-12
 x,y,yaw=p0['body'][:3];assert max(abs(z-w)for z,w in zip(poses[0],[x-.3*math.cos(yaw),y-.3*math.sin(yaw),yaw]))<=1e-12
 def arc(p,v0,v1,kap,t):
  d=v0*t+(v1-v0)*t*t;half=kap*d/2;sinc=math.sin(half)/half if half else 1.;return[p[0]+d*sinc*math.cos(p[2]+half),p[1]+d*sinc*math.sin(p[2]+half),p[2]+2*half]
 maximum=0.
 for i in range(20):maximum=max(maximum,max(abs(x-y)for x,y in zip(arc(poses[i],v[i],v[i+1],k[i],.5),poses[i+1])))
 assert maximum<=1e-8
 def requests(start,n):
  out=[]
  for step in range(start,start+n):
   j=step//50;dt=(step-j*50)*.01;speed=v[j]+(v[j+1]-v[j])*dt/.5;out.append([0.,0.,False]if speed<.005 else[speed,speed*k[j],False])
  return out
 journal=read('APPLIED_JOURNAL.json');covered=0;nonzero=0;commits=0
 for cycle in range(24):
  path=out/f'PROJECTION_{cycle:06d}_PROPOSAL.json'
  if not path.exists():break
  prop=read(path.name);n=cycle*5;expected=requests(n,5);assert prop['origin_native']==n and prop['original_plan_origin_native']==0 and abs(prop['elapsed_s']-.01*n)<=1e-12 and prop['requests']==expected and prop['shadow_requests']==requests(n,10)and prop['profile_sha256']==digest(profile)
  receipt=after if cycle==0 else read(f'cycle_{cycle:06d}_origin.json')['receipt'];assert prop['origin_packet_sha256']==digest(receipt['packet'])and receipt['packet']['native_tick']==n
  assert prop['token']==digest(dict(episode=task['run_id'],native=n,receipt=digest(receipt),profile=digest(profile),prefix=expected))
  actual=[]
  for j in range(5):
   if n+j>=len(journal)or journal[n+j]['phase']!='FILTER_RECEDING_CURRENT':break
   row=journal[n+j];assert row['applied']and row['before_native']==n+j and row['request']==expected[j];actual.append(dict(episode_id=task['run_id'],before_native=n+j,request=expected[j],applied=True));nonzero+=int(abs(expected[j][0])>=.005);covered+=1
  commit_path=out/f'PROJECTION_COMMIT_{n+5:06d}.json'
  if commit_path.exists():
   commit=read(commit_path.name);assert len(actual)==5 and commit['token']==prop['token']and commit['applied_prefix_sha256']==digest(actual)and commit['end_native']==n+5 and commit['original_plan_origin_native']==0;commits+=1
  elif actual:assert not require_complete
 assert covered==sum(row['phase']=='FILTER_RECEDING_CURRENT'for row in journal),'EVERY_NORMAL_PREFIX_BOUND'
 if require_complete:assert covered==120 and commits==24 and nonzero>0 and len(journal)==2320 and all(row['request']==[0.,0.,False]for row in journal[120:])
 assert counts is not None and counts['complete_reply_and_peer_close']and counts['NLP_returns']==1 and not counts['inflight_unknown']
 return dict(passed=True,scope='INDEPENDENT_FRESH_QUERY_AND_MONOTONIC_PROFILE_JOURNAL',NLP_returns=1,optimizer_work_total=None,maximum_ideal_kinematic_residual=maximum,covered_normal_native=covered,nonzero_requests=nonzero,completed_commits=commits,profile_original_origin=0,no_replan_or_saved_plan_reuse=True,public_map_shared_new_group_only=True,new_optimizer_or_physical_steps=0)
