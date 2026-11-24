"""Metadata-only accounting of one closed actual; never rerun its audit."""
from pathlib import Path
import fcntl,hashlib,json,os,sys,time
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v1884_teb_remaining_seven'
RID=os.environ['PHASE_EVENING_ASSIGNMENT'];O=ROOT/'rounds'/RID;D=ROOT/'runtime_archives'/RID
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');t.replace(p)
def main():
 os.sched_setaffinity(0,{5});row=next(x for x in read(ROOT/'PLAN_LOCKED.json')['assignments']if x['round_id']==RID);method=row['method'];c=read(O/'COMPLETION.json')
 assert c['closed']and c['review_restored']and c['lock_idle']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if(O/'OWNED_CHILD.json').exists():
  identity=read(O/'OWNED_CHILD.json');p=Path('/proc',str(identity['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=identity['start_ticks']
 ledgerpath=R/'runs/v1805_common_algorithm_registry/LEDGER.json';ledger=read(ledgerpath);slot=next(x for x in ledger['slots']if x['method']==method and x['task_id']==row['common_task'])
 if '--barrier'in sys.argv:
  for name in ['FULL_REMOTE_VERIFIED.json','TRANSPORT_CLEANUP.json','remote_delivery/FINALIZED.json']:assert read(D/name)['passed']
  assert not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists()
  b=dict(passed=True,closed_result_path=str((O/'COMPLETION.json').relative_to(R)),closed_result_sha256=sha(O/'COMPLETION.json'),remote_proof_path=str((D/'FULL_REMOTE_VERIFIED.json').relative_to(R)),remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),cleanup_proof_path=str((D/'TRANSPORT_CLEANUP.json').relative_to(R)),cleanup_proof_sha256=sha(D/'TRANSPORT_CLEANUP.json'),scientific_passed=c['passed'],every_block_member_whole_index_SHA_verified=True,all_originals_retained=True,models_authorized=False,late_outside_archive=True,unix=time.time())
  assert not(O/'POST_ROUND_STORAGE_BARRIER.json').exists();put(O/'POST_ROUND_STORAGE_BARRIER.json',b);slot.update(remote_closed=True,remote_barrier_sha256=sha(O/'POST_ROUND_STORAGE_BARRIER.json'));put(ledgerpath,ledger);print(json.dumps(dict(barrier_passed=True,round_id=RID)));return
 assert not(O/'RUNTIME_CLOSED_REVIEW.json').exists()
 for n,h in read(ROOT/'SOURCE_FREEZE.json')['files'].items():assert sha(R/n)==h
 path=O/'actual/RESULT.json';m=read(path)if path.exists()else None
 if m:
  assert m['closed']and sha(path)==c['machine_result_sha256']and c['all_source_SHA_verified_after_child_exit']
  n=m['new_actual_native'];audit=m.get('independent_audit')or m.get('independent_prefix_audit')or{};rep=m.get('replay')or{}
  complete=bool(type(n)is int and n>0 and m.get('evidence_saved')and m.get('fully_recorded_native')==n==m['own_replay_native']and not m.get('model_native_inflight_unknown')and rep.get('passed'))
  safe=complete and bool(audit.get('passed'))and not m['secondary_errors'];first=m.get('first_error');error=first['error']if first else None
  known={'RP-CCR':{'NO_CURRENT_WHOLE_GOAL_SOURCE','FIRST_DISCOVERY_NOT_NORMAL_DRIVING','DISCOVERY_STOP_PREDICTION_REJECTED','NO_MEASURED_HANDOFF_ONWARD_SOURCE','NO_STATIC_RECOVERY_SOURCE','EW_FRESH_DOMAIN_SOURCE_REFUSED'},'DWA':{'DWA_CURRENT_CYCLE_COMPLETE_STOP_REFUSED','DWA_CURRENT_5_NATIVE_RETAINED_STOP_REFUSED','DWA_REFERENCE_NO_FINITE_CURRENT_COMMAND','DWA_NATIVE_LIMIT_NO_WHOLE_GOAL','DWA_FIXED_NATIVE_WORK_FINISHED_WITHOUT_WHOLE_GOAL'},'TEB':{'TEB_ORIGINAL_FINITE_QUERY_REFUSED','TEB_RAW_CURVATURE_OUTSIDE_COMMON_CAP','TEB_RAW_SPEED_IN_BRAKING_DEADBAND','TEB_IN_PLACE_ROTATION_REFUSED','TEB_CURRENT_CYCLE_COMPLETE_STOP_REFUSED','TEB_CURRENT_5_NATIVE_RETAINED_STOP_REFUSED','TEB_NATIVE_LIMIT_NO_WHOLE_GOAL','TEB_FIXED_NATIVE_WORK_FINISHED_WITHOUT_WHOLE_GOAL'}}
  valid=bool(safe and error in {"AssertionError('"+value+"')"for value in known[method]})
  whole=bool(c['passed']and m['passed']and safe and (m.get('actual_original_goal_reached')if method=='RP-CCR'else m.get('whole_navigation_passed')and audit.get('whole_navigation_passed')))
  review=dict(closed=True,common_method=method,common_task=row['common_task'],actual_native=n,own_replay_native=m['own_replay_native'],physical=m.get('physical'),replay=rep,independent_audit=audit,first_error=first,secondary_errors=m['secondary_errors'],outer_first_error=c['first_error'],canonical_initializations=m['canonical_vehicle_initializations'],internal_factory_count=None,full_modelwork_total=None,source_all_SHA_verified_after_exit=True)
 else:
  valid=whole=False;review=dict(closed=True,common_method=method,common_task=row['common_task'],actual_native=None,own_replay_native=None,first_error=c['first_error'],secondary_errors=c['secondary_errors'],canonical_initializations=None,internal_factory_count=None,full_modelwork_total=None,machine_RESULT_missing=True,console_path=str((O/'pilot.console').relative_to(R)),console_sha256=sha(O/'pilot.console'),unknown_not_reconstructed=True)
 classification='QUALIFIED_WHOLE_GOAL_SUCCESS'if whole else'VALID_FINITE_METHOD_REFUSAL_WITH_INDEPENDENT_PREFIX_AUDIT'if valid else'TECHNICAL_OR_UNQUALIFIED_EVIDENCE_CENSOR'
 review.update(classification=classification,qualified_whole_navigation_passed=whole,valid_finite_method_negative=valid,scientific_denominator_retained=True,remote_pending=True,no_statistical_superiority_claim=True)
 put(O/'RUNTIME_CLOSED_REVIEW.json',review);put(ROOT/'reports'/RID/'RESULT.json',review)
 slot.update(registered=True,closed=True,status=classification,qualified_success=whole,actual_native=review['actual_native'],own_replay_native=review['own_replay_native'],algorithm_outcome='WHOLE_GOAL'if whole else'FINITE_REFUSAL'if valid else None,technical_failure=None if whole or valid else review['first_error'],result_path=str((O/'RUNTIME_CLOSED_REVIEW.json').relative_to(R)),result_sha256=sha(O/'RUNTIME_CLOSED_REVIEW.json'))
 ledger.update(registered=sum(bool(x['registered'])for x in ledger['slots']),closed=sum(bool(x['closed'])for x in ledger['slots']),qualified_success=sum(x['qualified_success']is True for x in ledger['slots']),unexecuted=sum(not x['registered']for x in ledger['slots']));put(ledgerpath,ledger)
 print(json.dumps(dict(round_id=RID,classification=classification,actual_native=review['actual_native'],own_replay_native=review['own_replay_native'])))
if __name__=='__main__':main()
