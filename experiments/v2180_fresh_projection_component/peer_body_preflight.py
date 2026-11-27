"""Execute actual worker body using explicit FAKE authority/SciPy backends only."""
from pathlib import Path
import os,sys,types,importlib.util,json,hashlib,io,contextlib,signal,copy,math,datetime
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
assert os.sched_getaffinity(0)=={0}and not(S/'PEER_BODY_SOFTWARE.json').exists()
import numpy as np
from handshake import bind,digest
old=R/'runs/v2176_sccr_common_plant_component/components/SCCR/actual/cycle_000000_origin.json';receipt=json.loads(old.read_text())['receipt'];known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
a=dict(scope='ONE_FRESH_REST_ORIENTATION_PROJECTION_ONLY',maximum_queries=1,models_authorized=False,run_id='SYNTHETIC_FAKE_WORKER_ONLY',query_nonce='SYNTHETIC_FAKE_NOT_ACTUAL_NLP',source_freeze_sha256='a'*64,worker_sha256=hashlib.sha256((C/'peer_entry.py').read_bytes()).hexdigest());authraw=(json.dumps(a,separators=(',',':'))+'\n').encode()
frame=dict(schema='FRESH_REST_ORIENTATION_PROJECTION_V1',episode_id=a['run_id'],query_sequence=0,query_nonce=a['query_nonce'],source_freeze_sha256=a['source_freeze_sha256'],numerical_admission_sha256='',receipt=receipt,public_known=known,public_known_sha256=hashlib.sha256((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_bytes()).hexdigest(),whole_goal_xy=[4.,-2.]);frame,claim=bind(authraw,frame)
rows=[]
for case in ['success_numpy_scalars','status8','exception','nonfinite_x','nonfinite_fun','wrongshape']:
 calls=[0]
 def fake(fun,x0,*,jac,bounds,constraints,method,options):
  calls[0]+=1;assert method=='SLSQP'and options==dict(maxiter=200,ftol=1e-10,disp=False)
  assert np.isfinite(fun(x0))and jac(x0).shape==x0.shape
  for c in constraints:
   v=c['fun'](x0);j=c['jac'](x0);assert j.shape==(len(v),len(x0))
  if case=='exception':raise RuntimeError('EXPLICIT_FAKE_OPTIMIZER_EXCEPTION_NO_REAL_NLP')
  x=x0.copy();f=float(fun(x0))
  if case=='nonfinite_x':x[0]=np.nan
  if case=='wrongshape':x=np.zeros(2)
  if case=='nonfinite_fun':f=float('nan')
  return types.SimpleNamespace(x=x,fun=np.float64(f),success=np.bool_(case!='status8'),status=np.int64(8 if case=='status8'else 0),message='EXPLICIT SOFTWARE FAKE; NO SLSQP',nit=np.int64(1),nfev=np.int64(1),njev=np.int64(1))
 scipy=types.ModuleType('scipy');scipy.__version__='1.14.1';opt=types.ModuleType('scipy.optimize');opt.minimize=fake;scipy.optimize=opt;sys.modules['scipy']=scipy;sys.modules['scipy.optimize']=opt
 spec=importlib.util.spec_from_file_location('CP_explicit_fake_worker_'+case,C/'peer_entry.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 original_sha=m.sha;m.authority=lambda:(a,{},{});m.read=lambda p:claim if Path(p).name=='PROJECTION_PEER_ONCE.json'else (_ for _ in()).throw(AssertionError('UNEXPECTED_REAL_ADMISSION_READ'))
 m.sha=lambda p:hashlib.sha256(authraw).hexdigest()if Path(p).name=='PROJECTION_OPTIMIZER_ADMISSION.json'else original_sha(p)
 previous=sys.stdin;sys.stdin=types.SimpleNamespace(buffer=io.BytesIO(json.dumps(frame,allow_nan=False).encode()+b'\n'));stream=io.StringIO()
 try:
  with contextlib.redirect_stdout(stream):code=m.main()
 finally:sys.stdin=previous;signal.alarm(0)
 raw=stream.getvalue();parts=[(line.split(' ',1)[0],json.loads(line.split(' ',1)[1]))for line in raw.splitlines()];answer=next(value for tag,value in parts if tag=='PROJECTION_REPLY');ret=[v for tag,v in parts if tag=='PROJECTION_RAW_RETURN'];assert calls[0]==1 and answer['NLP_attempted_calls']==1
 assert answer['passed']==(case=='success_numpy_scalars')and code==(0 if answer['passed']else 1)
 if case=='exception':assert answer['NLP_returns']==0 and answer['inflight_unknown']and not ret
 else:
  assert answer['NLP_returns']==1 and not answer['inflight_unknown']and len(ret)==1;assert [tag for tag,v in parts].index('PROJECTION_RAW_RETURN')<[tag for tag,v in parts].index('PROJECTION_REPLY')
  if case.startswith('nonfinite'):assert ret[0]['x']is None or ret[0]['fun']is None
 rows.append(dict(case=case,passed=True,actual_real_NLP=0,explicit_fake_calls=calls[0],worker_returncode=code,source_derived_fake_NLP_returns=answer['NLP_returns'],fake_inflight_unknown=answer['inflight_unknown'],stdout_bytes=len(raw.encode()),stdout_sha256=hashlib.sha256(raw.encode()).hexdigest(),first_error=answer.get('first_error')))
assert not any(n in sys.modules for n in ['mujoco','torch','jax'])
x=dict(passed=True,actual_worker_body_executed_with_explicit_fake_authority_and_fake_optimizer=True,cases=rows,real_SLSQP_models_physics_Source=0,serialization_numpy_scalars_and_nonfinite_returns=True,raw_return_precedes_acceptance=True,attempts_returns_inflight_separate=True,source_sha256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [C/'peer_entry.py',C/'peer_body_preflight.py',C/'fresh_problem.py',C/'handshake.py']},created_at=datetime.datetime.now().astimezone().isoformat());text=json.dumps(x,indent=2,allow_nan=False)+'\n';assert len(text.encode())<96*1024;(S/'PEER_BODY_SOFTWARE.json').write_text(text);print(json.dumps(dict(passed=True,actual_worker_FAKE_backend_cases=len(rows),real_NLP_models_physics=0,maximum_reply_stdout_bytes=max(v['stdout_bytes']for v in rows))))
