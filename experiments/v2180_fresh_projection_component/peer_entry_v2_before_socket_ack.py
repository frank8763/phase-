"""Source-bound readonly CPU6 one-shot ideal NLP. No model or physical authority."""
from peer_guard import R,C,S,A,read,sha,authority
import os,sys,json,time,math,signal,traceback,importlib.abc,resource

def main():
 a,w,files=authority() # BEFORE any numerical import or stdin processing
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,n,*args):
   if n.split('.')[0]in {'mujoco','torch','jax','kernel','factory','vehicle','fast_predict','coupled_model','OpenGL'}:raise AssertionError('READONLY_PROJECTION_PEER_NO_MODEL:'+n)
 sys.meta_path.insert(0,Ban());resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2);resource.setrlimit(resource.RLIMIT_CPU,(110,115));resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,)*2)
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('ONE_FRESH_QUERY_120S')));signal.alarm(120)
 sys.path.insert(0,str(R/'runs/v1491_priest_dependency_target/site'));import numpy as np;import scipy;from scipy.optimize import minimize
 assert scipy.__version__=='1.14.1'
 from fresh_problem import FreshProjection,cursor
 # Exact inherited normalized equations use their own unambiguous module alias.
 from importlib import util as spec_util
 spec=spec_util.spec_from_file_location('collocation',R/'experiments/v2177_priest_vector_orientation/collocation.py');m=spec_util.module_from_spec(spec);sys.modules['collocation']=m;spec.loader.exec_module(m)
 spec=spec_util.spec_from_file_location('CP_original_normalized',R/'experiments/v2177_priest_vector_orientation/normalized.py');normal=spec_util.module_from_spec(spec);spec.loader.exec_module(normal)
 raw=sys.stdin.buffer.readline(1024**2+1);assert len(raw)<=1024**2 and raw.endswith(b'\n')and not sys.stdin.buffer.read(1),'EXACTLY_ONE_BOUNDED_QUERY'
 frame=json.loads(raw);assert cursor.digest(frame)==read(A/'PROJECTION_PEER_ONCE.json')['first_input_sha256']and frame['query_nonce']==a['query_nonce']and frame['episode_id']==a['run_id']and frame['source_freeze_sha256']==a['source_freeze_sha256']and frame['numerical_admission_sha256']==sha(A/'PROJECTION_OPTIMIZER_ADMISSION.json'),'FRESH_QUERY_NONCE_ADMISSION_ORIGIN'
 p=FreshProjection(frame);n=normal.Normalized(p);w0=np.zeros(len(p.initial));lo,hi=n.bounds();first=p.evaluate(p.initial);assert abs(first['equalities']).max()<=1e-12 and first['minimum_sampled_clearance']>=.24353421020226934 and first['inequalities'].min()>=-1e-12,'INITIAL_REPRESENTATION_INAPPLICABLE'
 width=len(m.geometry.feature([-4.,-2.,0.],p.known)[0]);mask=np.ones(len(first['inequalities']),bool);mask[(p.N+1)*width+np.arange(p.N)*(width+1)+width]=False
 cache={};calls=dict(objective=0,jacobian=0,equality=0,equality_jacobian=0,inequality=0,inequality_jacobian=0)
 def arrays(x):
  key=np.asarray(x,float).tobytes()
  if cache.get('key')!=key:cache.clear();cache.update(key=key,value=n.evaluate(x))
  return cache['value']
 def obj(x):calls['objective']+=1;return n.objective(x)[0]
 def jac(x):calls['jacobian']+=1;return n.objective(x)[1]
 def eq(x):calls['equality']+=1;return arrays(x)['equalities']
 def ej(x):calls['equality_jacobian']+=1;return arrays(x)['equality_jacobian']
 def ing(x):
  calls['inequality']+=1;v=arrays(x)['inequalities'].copy();v[mask]-=1e-7;return v
 def ij(x):calls['inequality_jacobian']+=1;return arrays(x)['inequality_jacobian']
 result=dict(passed=False,NLP_attempted_calls=0,NLP_returns=0,inflight_unknown=False,internal_optimizer_work=None,compiled_SLSQP_FFI_calls=None,models=0,physical_authority=False,query_sha256=cursor.digest(frame),query_nonce=frame['query_nonce'],proposal=None)
 start=time.monotonic()
 try:
  result.update(NLP_attempted_calls=1,inflight_unknown=True);print('PROJECTION_PROGRESS '+json.dumps(result),flush=True)
  answer=minimize(obj,w0,jac=jac,bounds=list(zip(lo,hi)),constraints=[dict(type='eq',fun=eq,jac=ej),dict(type='ineq',fun=ing,jac=ij)],method='SLSQP',options=dict(maxiter=200,ftol=1e-10,disp=False));result.update(NLP_returns=1,inflight_unknown=False)
  x=np.asarray(answer.x,float);f=float(answer.fun);ret=dict(success=bool(answer.success),status=int(answer.status),message=str(answer.message),x=x.tolist()if np.isfinite(x).all()else None,raw_x_dtype=str(x.dtype),raw_x_shape=list(x.shape),raw_x_bytes_hex=x.tobytes().hex(),fun=f if math.isfinite(f)else None,raw_fun_float_hex=f.hex(),nit=int(answer.nit),nfev=int(answer.nfev),njev=int(answer.njev));print('PROJECTION_RAW_RETURN '+json.dumps(ret,allow_nan=False),flush=True)
  result['raw_return']=ret;assert x.shape==w0.shape and np.isfinite(x).all()and math.isfinite(f)and ret['success']and ret['status']==0,'ORIGINAL_STRICT_SOLVER_STATUS_OR_FINITE_RETURN'
  z=n.original(x);before=float(p.objective(p.initial)[0]);after=float(p.objective(z)[0]);assert after<=before+1e-10,'ORIGINAL_OBJECTIVE_GATE'
  result['proposal']=p.proposal(z,success=ret['success'],status=ret['status']);checked=p.evaluate(z);result.update(passed=True,maximum_equality_residual=float(abs(checked['equalities']).max()),minimum_sampled_clearance_m=float(checked['minimum_sampled_clearance']),objective_initial=before,objective_final=after)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 result.update(closed=True,wall_s=time.monotonic()-start,callback_evaluations=calls,all_source_SHA_after=all(sha(R/n)==h for n,h in files.items()))
 if not result['all_source_SHA_after']:result['passed']=False
 print('PROJECTION_REPLY '+json.dumps(result,allow_nan=False),flush=True);return 0 if result['passed']else 1
if __name__=='__main__':
 try:raise SystemExit(main())
 except BaseException as e:
  if isinstance(e,SystemExit):raise
  print('PROJECTION_ERROR '+json.dumps(dict(error=repr(e),traceback=traceback.format_exc(),canonical_NLP_attempted_calls=None,canonical_NLP_returns=None,models=None)),flush=True);raise
