"""Persistent source-bound CPU6 ideal NLP peer, one solve per fresh frame."""
import os,sys,json,time,traceback,resource,importlib.abc
from context import R,C,O,METHOD,read,native_authority,sha

def main():
 a,files=native_authority()
 out=__import__('pathlib').Path(a['assignment']['output']);auth=read(out/'FILTER_OPTIMIZER_ADMISSION.json')
 assert auth['models_authorized']is False and auth['scope']=='FILTER_OPTIMIZER_ONLY'and auth['method']==METHOD and auth['maximum_queries']==20
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,n,*args):
   if n.split('.')[0]in{'mujoco','torch','jax','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('FILTER_NO_MODEL_PEER:'+n)
 sys.meta_path.insert(0,Ban());resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2);resource.setrlimit(resource.RLIMIT_CPU,(3500,3510));resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,)*2)
 sys.path.insert(0,str(R/'runs/v1491_priest_dependency_target/site'));import numpy as np
 from scipy.optimize import minimize
 from filter_scope import scope
 from peer_contract import decode
 from proposal_gate import admissible
 calls=0;total_returns=0;start=time.monotonic()
 for raw in iter(lambda:sys.stdin.buffer.readline(1024**2+1),b''):
  assert time.time()<auth['absolute_deadline_unix']and time.monotonic()<auth['hard_stop_monotonic']
  frame,ack=decode(raw,calls,METHOD,auth['run_id']);current=frame['current'];request=frame['request']
  if calls==0:assert current['input_sha256']==auth['first_input_sha256']
  returns=[];tick=time.monotonic()
  def observe(v):assert len(returns)<2;returns.append(v)
  with scope(files)as modules:answer=modules.filter.solve(np,minimize,request['case'],request['public_known'],METHOD,observe)
  calls+=1;total_returns+=len(returns)
  counts=dict(optimizer_call_attempts=1,optimizer_calls=1,NLP_returns=len(returns),inflight_unknown=False,internal_optimizer_work=None,models=0,wall_s=time.monotonic()-tick)
  allowed=admissible(answer);proposal=None
  if allowed:
   raw_command=answer['commands'][0];v,w,stale=raw_command;assert abs(v)<=.1 and abs(w)<=abs(v)/1.32+1e-12 and not stale
   proposal=dict(raw_request=raw_command,input_sha256=current['input_sha256'],method=METHOD,origin_native=request['origin_native'],no_clipping=True,actual_execution_permitted=False,prediction_maximum_slack=answer.get('maximum_slack'),ideal_future_hard_geometry_passed=answer.get('original_hard_geometry_passed'),original_physical_shadow_and_admission_required=True)
  print('FILTER_REPLY '+json.dumps(dict(passed=True,answer=dict(numerical=answer,returns=returns,work_accounting=counts,proposal=proposal,physical_authority=False),transport_ack=ack),allow_nan=False),flush=True)
 closed=dict(optimizer_calls=calls,NLP_returns=total_returns,inflight_unknown=False,models=0,internal_optimizer_work=None,wall_s=time.monotonic()-start,all_source_SHA_after=all(sha(R/n)==h for n,h in files.items()))
 assert closed['all_source_SHA_after'];print('FILTER_CLOSED '+json.dumps(closed),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as x:print('FILTER_ERROR '+json.dumps(dict(error=repr(x),traceback=traceback.format_exc())),flush=True);raise
