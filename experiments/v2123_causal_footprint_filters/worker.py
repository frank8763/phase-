"""Finite fresh environmental NLP returns on CPU6, no Phase models."""
import os,resource,time,traceback,json
from common import R,C,S,read,put,authority,sha,deny_models

def main():
 a,files,out=authority(6,'math');deny_models(solvers=False);resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(850,860))
 start=time.monotonic();rows=[];count=0;result=dict(closed=False,finite_batch_complete=False,models=0,physics=0,replay=0,formal_tasks=0,Phase_vehicle_qualified=False)
 try:
  import sys;sys.path.insert(0,str(R/'runs/v1491_priest_dependency_target/site'));import numpy as np
  from scipy.optimize import minimize
  from filter import solve
  known=read(R/read(S/'INPUTS_LOCKED.json')['public_known'])
  for case in read(S/'CASES_LOCKED.json')['cases']:
   for kind in['PSF','PCBF']:
    assert time.time()<a['absolute_end_unix']and time.monotonic()<a['hard_stop_monotonic'];returns=[]
    def observe(v):
     nonlocal count
     count+=1;assert count<=18;returns.append(v);put(out/'LAST_RETURN.json',dict(case=case['id'],method=kind,total_returns=count,value=v))
    try:answer=solve(np,minimize,case,known,kind,observe)
    except BaseException as x:answer=dict(passed=False,error=repr(x),traceback=traceback.format_exc())
    rows.append(dict(case=case,method=kind,answer=answer,returns=returns));put(out/'CASES.json',rows)
  accepted=[x for x in rows if x['answer'].get('passed')]
  result.update(finite_batch_complete=True,numerical_cases=len(rows),NLP_returns=count,accepted=len(accepted),expected_refusals=sum('expected_refusal'in x['answer']for x in rows),failed=len(rows)-len(accepted)-sum('expected_refusal'in x['answer']for x in rows),accepted_hard_geometry_failures=sum(not x['answer']['original_hard_geometry_passed']for x in accepted),accepted_command_domain_violation_max=max([x['answer']['maximum_command_domain_violation']for x in accepted],default=None),zero_slack_count=sum(x['answer']['maximum_slack']<=1e-7 for x in accepted))
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc())
 result.update(closed=True,wall_s=time.monotonic()-start,all_frozen_source_SHA_after=all(sha(R/n)==h for n,h in files.items()));put(out/'RESULT.json',result);print(json.dumps(result));return 0 if result['finite_batch_complete']and result['all_frozen_source_SHA_after']else 1
if __name__=='__main__':raise SystemExit(main())
