"""Fixed initialization comparison, no models or retries, all returns retained."""
import sys,time,json,resource
from common import R,C,S,read,put,sha,authority,deny_models,load

def main():
 a,files,out=authority(6,'math');deny_models(solvers=False);resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2);resource.setrlimit(resource.RLIMIT_CPU,(850,860))
 sys.path.insert(0,str(R/'runs/v1491_priest_dependency_target/site'));import numpy as np
 from scipy.optimize import minimize
 import geometry,kinematics,oracle
 variants=[('original',load('original_pcbf_body',C/'filter_original.py')),('minimal_feasible_slack',load('minimal_slack_pcbf_body',C/'filter_minimal.py'))]
 cases=read(S/'CASES_LOCKED.json')['cases'];rows=[];total=0
 for label,module in variants:
  for case in cases:
   returns=[]
   def observe(v):
    nonlocal total
    assert len(returns)<2 and total<20;returns.append(v);total+=1
   start=time.monotonic();answer=module.solve(np,minimize,case['case'],case['known'],'PCBF',observe)
   allowed=bool(answer.get('passed')and answer.get('original_hard_geometry_passed')and answer.get('maximum_slack',float('inf'))<=1e-7)
   rows.append(dict(variant=label,case_id=case['id'],role=case['role'],answer=answer,returns=returns,strict_original_physical_proposal_gate=allowed,wall_s=time.monotonic()-start))
   put(out/'RESULT_PARTIAL.json',dict(rows=rows,NLP_returns=total,models=0,partial=True))
 assert len(rows)==10 and total<=20
 positives=[r for r in rows if r['variant']=='minimal_feasible_slack'and r['role']=='POSITIVE_COMPONENT_INPUT']
 result=dict(closed=True,passed=True,rows=rows,NLP_returns=total,models=0,physics=0,replay=0,new_formal_tasks=0,internal_optimizer_work=None,no_retry=True,no_tolerance_change=True,vehicle_qualified=False,minimal_initialization_positive_component_gate=all(x['strict_original_physical_proposal_gate']for x in positives),all_frozen_source_SHA_after=all(sha(R/n)==h for n,h in files.items()))
 put(out/'RESULT.json',result);print(json.dumps(dict(closed=True,NLP_returns=total,positive_gate=result['minimal_initialization_positive_component_gate'],models=0)))
if __name__=='__main__':main()
