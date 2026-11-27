"""Bounded pure arithmetic checks of measured-rest transform; no SLSQP/plant."""
from pathlib import Path
import os,sys,json,copy,ast,math,hashlib,signal,datetime
from fresh_problem import FreshProjection,known,PUBLIC,cursor,np
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
assert os.sched_getaffinity(0)=={4}and not(S/'FRESH_PROBLEM_SOFTWARE.json').exists()
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FRESH_TRANSFORM_SOFTWARE60S')));signal.alarm(60)
old=R/'runs/v2176_sccr_common_plant_component/components/SCCR/actual/cycle_000000_origin.json';receipt=json.loads(old.read_text())['receipt']
frame=dict(schema='FRESH_REST_ORIENTATION_PROJECTION_V1',episode_id='SOFTWARE_CURRENT_TRANSFORM_ONLY',query_sequence=0,query_nonce='SOFTWARE_ONLY_NOT_A_FRESH_ACTUAL_SOLVE',source_freeze_sha256='a'*64,numerical_admission_sha256='b'*64,receipt=copy.deepcopy(receipt),public_known=known(),public_known_sha256=hashlib.sha256(PUBLIC.read_bytes()).hexdigest(),whole_goal_xy=[4.,-2.])
p=FreshProjection(frame);value=p.evaluate(p.initial);assert abs(value['equalities']).max()<1e-12 and value['minimum_sampled_clearance']>=.24353421020226934
# Success/status arguments here are explicit software stubs; no optimizer called.
profile=p.proposal(p.initial,success=True,status=0);b=copy.deepcopy(receipt)
for name in ['before_monotonic','after_monotonic']:b[name]+=.01
for owner,key in [(b['packet'],'body_measured_at'),(b['packet'],'sent_at'),(b['packet']['steering'],'measured_at')]:owner[key]+=.01
b['packet_sha256']=cursor.digest(b['packet']);cur=cursor.Cursor(frame['episode_id']);cur.install(profile,receipt,b);prop=cur.propose(b);assert profile['query']['receipt_sha256']==cursor.digest(receipt)and prop['origin_native']==0;cur.close()
fd=0.;eqfd=0.;cases=[]
for theta in [0.,.17]:
 f=copy.deepcopy(frame);f['receipt']['packet']['body'][2]=theta;f['receipt']['scan']['yaw']=theta;f['receipt']['packet_sha256']=cursor.digest(f['receipt']['packet']);z=FreshProjection(f)
 assert max(abs(a-b)for a,b in zip(z.initial_full[:3],cursor.rear(f['receipt']['packet'])))<1e-12
 x=z.initial+np.array([1e-4*math.sin(.17*i+.31)for i in range(len(z.initial))]);v=z.evaluate(x)
 for j in range(4):
  d=np.array([math.cos((j+1)*.13*i+.2)for i in range(len(x))]);d/=np.linalg.norm(d);h=1e-7;up=z.evaluate(x+h*d);dn=z.evaluate(x-h*d)
  eqfd=max(eqfd,float(abs((up['equalities']-dn['equalities'])/(2*h)-v['equality_jacobian']@d).max()));fd=max(fd,float(abs((up['inequalities']-dn['inequalities'])/(2*h)-v['inequality_jacobian']@d).max()))
 cases.append(dict(heading=theta,initial_rear=z.initial_full[:3].tolist(),variable_shape=len(z.initial),derivative_directions=4,geometry_positive_claim=theta==0.))
assert fd<2e-6 and eqfd<1e-7
negative=[]
def reject(name,fn):
 f=copy.deepcopy(frame);fn(f)
 try:FreshProjection(f)
 except (AssertionError,ValueError,TypeError,KeyError)as e:negative.append(dict(name=name,error=repr(e)))
 else:raise AssertionError('EXPECTED_FRESH_QUERY_REFUSAL:'+name)
def rehash(f):f['receipt']['packet_sha256']=cursor.digest(f['receipt']['packet'])
for n,fn in [
 ('extra_truth',lambda f:f.__setitem__('actor_truth',[0.,0.])),
 ('wrong_schema',lambda f:f.__setitem__('schema','old_saved_plan')),
 ('no_nonce',lambda f:f.__setitem__('query_nonce','')),
 ('old_querysequence',lambda f:f.__setitem__('query_sequence',1)),
 ('missing_admission_binding',lambda f:f.__setitem__('numerical_admission_sha256','')),
 ('public_dynamic_geometry',lambda f:f['public_known']['known_circles'].append([0.,0.,.2])),
 ('public_hash',lambda f:f.__setitem__('public_known_sha256','f'*64)),
 ('goal_substitution',lambda f:f.__setitem__('whole_goal_xy',[-3.4,-2.])),
 ('nonrest_no_reset',lambda f:(f['receipt']['packet']['body'].__setitem__(3,.01),rehash(f))),
 ('nonzero_yaw_rate',lambda f:(f['receipt']['packet']['body'].__setitem__(4,.01),rehash(f))),
 ('nonzero_lateral',lambda f:(f['receipt']['packet'].__setitem__('body_lateral',.01),rehash(f))),
 ('stale_native',lambda f:(f['receipt']['packet'].__setitem__('native_tick',5),rehash(f))),
 ('source_time',lambda f:(f['receipt']['packet'].__setitem__('sim_time',.05),rehash(f))),
]:reject(n,fn)
assert not any(n in sys.modules for n in ['scipy','mujoco','torch','jax'])
r=dict(passed=True,scope='FRESH_REST_QUERY_CONSTRUCTION_SOFTWARE_ONLY',initial_clearance=value['minimum_sampled_clearance'],maximum_equality_error=float(abs(value['equalities']).max()),finite_difference_equality_max=eqfd,finite_difference_inequality_max=fd,transformed_cases=cases,negative_cases=negative,negative_count=len(negative),receipt_query_profile_cursor_roundtrip=True,steering_controller_memory_preserved_in_origin_fingerprint=True,nonrest_rejected_not_reset=True,whole_goal_unchanged=[4.,-2.],solver_success_parameters_are_explicit_software_stubs=True,historical_receipt_only_fixture_not_fresh_execution=True,actual_NLP_models_physics_replay_Source=0,source_sha256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [C/'fresh_problem.py',C/'check_fresh_problem.py',C/'PROTOCOL.md',old]},created_at=datetime.datetime.now().astimezone().isoformat());raw=json.dumps(r,indent=2,allow_nan=False)+'\n';assert len(raw.encode())<96*1024;(S/'FRESH_PROBLEM_SOFTWARE.json').write_text(raw);print(json.dumps({k:v for k,v in r.items()if k not in ['negative_cases','source_sha256']}))
