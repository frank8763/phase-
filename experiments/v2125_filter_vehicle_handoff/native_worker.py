"""One source-bound CPU6 ideal NLP query; read-only no Phase models."""
import os,sys,json,time,hashlib,traceback,resource,importlib.abc
from context import R,C,O,METHOD,read,native_authority,digest,sha

def main():
 a,files=native_authority() # before numpy/scipy imports
 out=__import__('pathlib').Path(a['assignment']['output']);auth=read(out/'FILTER_OPTIMIZER_ADMISSION.json');assert auth['models_authorized']is False and auth['scope']=='FILTER_OPTIMIZER_ONLY'and auth['method']==METHOD
 raw=sys.stdin.buffer.readline(1024**2+1);assert raw.endswith(b'\n')and len(raw)<=1024**2;assert not sys.stdin.buffer.read(1)
 frame=json.loads(raw);current=frame['current'];request=frame['request'];assert current['method']==request['method']==METHOD and current['input_sha256']==auth['input_sha256']and request['request_sha256']==auth['request_sha256']
 for z,key in[(current,'input_sha256'),(request,'request_sha256')]:
  clean=dict(z);h=clean.pop(key);assert digest(clean)==h
 assert request['input_sha256']==current['input_sha256']and request['origin_native']==current['native']==0 and not current['physical_authority']
 assert time.time()<auth['absolute_deadline_unix']and time.monotonic()<auth['hard_stop_monotonic']
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,n,*args):
   if n.split('.')[0]in{'mujoco','torch','jax','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('FILTER_NO_MODEL_PEER:'+n)
 sys.meta_path.insert(0,Ban());resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2);resource.setrlimit(resource.RLIMIT_CPU,(580,590));resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,)*2)
 sys.path.insert(0,str(R/'runs/v1491_priest_dependency_target/site'));import numpy as np
 from scipy.optimize import minimize
 from filter_scope import scope
 returns=[];start=time.monotonic()
 def observe(v):
  assert len(returns)<2;returns.append(v)
 with scope(files)as math_modules:answer=math_modules.filter.solve(np,minimize,request['case'],request['public_known'],METHOD,observe)
 counts=dict(optimizer_call_attempts=1,optimizer_calls=1,NLP_returns=len(returns),inflight_unknown=False,internal_optimizer_work=None,models=0,wall_s=time.monotonic()-start)
 allowed=bool(answer.get('passed')and answer.get('original_hard_geometry_passed')and answer.get('maximum_slack',float('inf'))<=1e-7)
 proposal=None
 if allowed:
  raw_command=answer['commands'][0];v,w,stale=raw_command;assert abs(v)<=.1 and abs(w)<=abs(v)/1.32+1e-12 and not stale
  proposal=dict(raw_request=raw_command,input_sha256=current['input_sha256'],method=METHOD,origin_native=0,no_clipping=True,actual_execution_permitted=False)
 value=dict(passed=True,answer=dict(numerical=answer,returns=returns,work_accounting=counts,proposal=proposal,physical_authority=False),input_bytes=len(raw),input_byte_sha256=hashlib.sha256(raw).hexdigest(),all_source_SHA_after=all(sha(R/n)==h for n,h in files.items()))
 assert value['all_source_SHA_after'];print('FILTER_REPLY '+json.dumps(value,allow_nan=False),flush=True);print('FILTER_CLOSED '+json.dumps(counts),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as x:
  print('FILTER_ERROR '+json.dumps(dict(error=repr(x),traceback=traceback.format_exc())),flush=True);raise
