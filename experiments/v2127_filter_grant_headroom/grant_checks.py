"""Reproduce actual resources.prepare/base.admit seam with saved allocation only."""
import json
from context import R,C,SOURCE as S,load,put,sha

def main():
 P=R/'runs/v2126_filter_receding_current/components/PSF';m=json.loads((P/'actual/RESULT.json').read_text());proof=json.loads(m['first_error']['error'].split('EVIDENCE_ALL_RUNS_WRITE_QUOTA_REFUSED:',1)[1][:-2]);limits=json.loads((P/'LIMITS_DRAFT.json').read_text())
 quota=load('regression_current_quota',C/'quota.py');new=load('regression_current_resources',C/'resources.py');old=load('regression_frozen_resources',R/'experiments/v2126_filter_receding_current/resources.py')
 # resources imports `quota`; ensure that is the actual new production module.
 import sys;prior=sys.modules.get('quota');sys.modules['quota']=quota
 events=[]
 try:
  for label,delta in [('original_logged',0),('later_allocation',8*1024**2),('root_exhausted',1024**3)]:
   q=quota.EvidenceQuota(P/'actual',limits);q.holds={'saved_unwritten_holds':proof['unwritten_holds_bytes']};q.grant=None
   quota.base.used=lambda path:proof['task_allocated_bytes'];quota.base.measure=lambda out,lim:(proof['task_allocated_bytes'],proof['all_runs_allocated_bytes']+delta)
   calls=[]
   def prepare(capacity_bytes,**kw):
    calls.append(capacity_bytes);return quota.base.EvidenceQuota.admit(q,capacity_bytes,'PREPARE_BYTE_GRANT_BEFORE_FRESH_WIRE')
   q.prepare_grant=prepare
   try:old.prepare(q,'STOPPED_EVENT_PREPARATION')
   except AssertionError as x:assert 'EVIDENCE_ALL_RUNS_WRITE_QUOTA_REFUSED'in str(x)
   else:raise AssertionError('ORIGINAL_BUG_NOT_REPRODUCED')
   if label=='root_exhausted':
    try:new.prepare(q,'STOPPED_EVENT_PREPARATION')
    except AssertionError as x:assert 'NO_RESOURCE_GRANT_HEADROOM'in str(x)
    else:raise AssertionError('ROOT_CAP_BYPASSED')
    events.append(dict(case=label,refused_before_grant=True));continue
   answer=new.prepare(q,'STOPPED_EVENT_PREPARATION');assert calls[-1]<calls[-2]
   assert answer['all_runs_allocated_bytes']+answer['rounded_pending_and_error_reserve_bytes']+limits['remaining_archive_download_reserve_bytes']+limits['root_reserve_bytes']<=limits['storage_limit_bytes']
   events.append(dict(case=label,old_cap=calls[-2],new_cap=calls[-1],original_base_admission_passed=True))
  # All normal, closure, replay and audit callers use exactly the same prepare seam.
  unchanged=['navigation.py','native_client.py','native_worker.py','current_request.py','audit_component.py','response.py','base_quota.py','granted_quota.py','quota.py','filter.py','geometry.py','kinematics.py','oracle.py','request.py']
  assert all((C/n).read_bytes()==(R/'experiments/v2126_filter_receding_current'/n).read_bytes()for n in unchanged)
  value=dict(passed=True,models=0,optimizer_queries=0,physical_native=0,old_error_reproduced=True,cases=events,only_auto_grant_size_changed=True,original_caps_and_NLP_and_safety_gates_unchanged=True,unchanged_modules=unchanged,raw_result_path=str((P/'actual/RESULT.json').relative_to(R)),raw_result_sha256=sha(P/'actual/RESULT.json'))
  put(S/'GRANT_HEADROOM_REGRESSION.json',value);print(json.dumps(value))
 finally:
  if prior is None:sys.modules.pop('quota',None)
  else:sys.modules['quota']=prior
if __name__=='__main__':main()
