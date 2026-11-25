"""Once metadata review; preserve machine primary, secondary and unknowns."""
from pathlib import Path
import fcntl,hashlib,json,time
R=Path(__file__).resolve().parents[2];S=R/'runs/v1978_rpp_first_common_round';D=R/'runs/v1980_rpp_common_runtime_recovery'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 assert not p.exists();p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def write_ledger(ledger):
 p=R/'runs/v1805_common_algorithm_registry/LEDGER.json';t=p.with_suffix('.json.tmp');t.write_text(json.dumps(ledger,indent=2)+'\n');t.replace(p)
def main(barrier=False):
 c=read(S/'COMPLETION.json');assert c['closed']and c['review_restored']and c['lock_idle']and sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  with(R/n).open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 identity=read(S/'OWNED_CHILD.json');p=Path('/proc',str(identity['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=identity['start_ticks']
 ledger=read(R/'runs/v1805_common_algorithm_registry/LEDGER.json');slot=next(s for s in ledger['slots']if s['method']=='RPP'and s['task_id']=='common_01');assert slot['registered']
 if barrier:
  r=read(D/'FULL_REMOTE_VERIFIED.json');assert r['passed']and all(r[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA']);assert read(D/'TRANSPORT_CLEANUP.json')['passed']and read(D/'remote_delivery/RESULT.json')['passed']and not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists()
  assert slot['closed']
  b=dict(passed=True,closed_result_path=str((S/'COMPLETION.json').relative_to(R)),closed_result_sha256=sha(S/'COMPLETION.json'),remote_proof_path=str((D/'FULL_REMOTE_VERIFIED.json').relative_to(R)),remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),cleanup_proof_path=str((D/'TRANSPORT_CLEANUP.json').relative_to(R)),cleanup_proof_sha256=sha(D/'TRANSPORT_CLEANUP.json'),scientific_passed=read(S/'RUNTIME_CLOSED_REVIEW.json')['qualified_whole_navigation_passed'],every_block_member_whole_index_SHA_verified=True,all_originals_retained=True,models_authorized=False,late_outside_archive=True)
  put(S/'POST_ROUND_STORAGE_BARRIER.json',b);slot.update(remote_closed=True,remote_barrier_sha256=sha(S/'POST_ROUND_STORAGE_BARRIER.json'));write_ledger(ledger);print(json.dumps(dict(barrier_passed=True)));return
 assert not(S/'RUNTIME_CLOSED_REVIEW.json').exists();assert all(sha(R/n)==h for n,h in read(S/'SOURCE_FREEZE.json')['files'].items())
 path=S/'actual/RESULT.json';m=read(path)if path.exists()else None
 if m:
  assert m['closed']and sha(path)==c['machine_result_sha256']and c['all_source_SHA_verified_after_child_exit'];n=m['new_actual_native'];audit=m.get('independent_audit')or{};rep=m.get('replay')or{}
  complete=bool(type(n)is int and n>0 and m.get('evidence_saved')and m.get('fully_recorded_native')==n==m['own_replay_native']and not m.get('model_native_inflight_unknown')and rep.get('passed'))
  safe=complete and bool(audit.get('passed'))and not m['secondary_errors']and c['first_error']is None and not c['secondary_errors'];first=m.get('first_error');error=first['error']if first else None
  known={'RPP_CURRENT_CYCLE_COMPLETE_STOP_REFUSED','RPP_ORIGINAL_COMPLETE_STOP_REFUSED','RPP_ORIGINAL_WHOLE_GOAL_STOP_REFUSED','RPP_NATIVE_LIMIT_NO_WHOLE_GOAL','RPP_REGISTERED_PLAN_LIMIT','RPP_NOMINAL_PATH_NOT_FOUND','RPP_CURRENT_PATH_REVALIDATION_REFUSED','RPP_MEASURED_CUSP_CAPTURE_REFUSED','RPP_RAW_COMMAND_GEAR_REFUSED'}
  valid=bool(safe and error in {"AssertionError('"+x+"')"for x in known});whole=bool(c['passed']and m['passed']and safe and m['whole_navigation_passed']and audit.get('whole_navigation_passed'))
  review=dict(closed=True,common_method='RPP',common_task='common_01',actual_native=n,own_replay_native=m['own_replay_native'],physical=m.get('physical'),replay=rep,independent_audit=audit,first_error=first,secondary_errors=m['secondary_errors'],outer_first_error=c['first_error'],canonical_initializations=m['canonical_vehicle_initializations'],internal_factory_count=None,full_modelwork_total=None,q1159_recovery_subset=m.get('model_work'),source_all_SHA_verified_after_exit=True,machine_result_sha256=sha(path))
 else:
  valid=whole=False;review=dict(closed=True,common_method='RPP',common_task='common_01',actual_native=None,own_replay_native=None,first_error=c['first_error'],secondary_errors=c['secondary_errors'],canonical_initializations=None,internal_factory_count=None,full_modelwork_total=None,machine_RESULT_missing=True,console_path=str((S/'pilot.console').relative_to(R)),console_sha256=sha(S/'pilot.console'),unknown_not_reconstructed=True)
 classification='QUALIFIED_WHOLE_GOAL_SUCCESS'if whole else'VALID_FINITE_METHOD_REFUSAL_WITH_INDEPENDENT_PREFIX_AUDIT'if valid else'TECHNICAL_OR_UNQUALIFIED_EVIDENCE_CENSOR';review.update(classification=classification,qualified_whole_navigation_passed=whole,valid_finite_method_negative=valid,scientific_denominator_retained=True,remote_pending=True,no_statistical_superiority_claim=True)
 put(S/'RUNTIME_CLOSED_REVIEW.json',review);slot.update(registered=True,closed=True,status=classification,qualified_success=whole,actual_native=review['actual_native'],own_replay_native=review['own_replay_native'],algorithm_outcome='WHOLE_GOAL'if whole else'FINITE_REFUSAL'if valid else None,technical_failure=None if whole or valid else review['first_error'],result_path=str((S/'RUNTIME_CLOSED_REVIEW.json').relative_to(R)),result_sha256=sha(S/'RUNTIME_CLOSED_REVIEW.json'));ledger.update(registered=sum(bool(x['registered'])for x in ledger['slots']),closed=sum(bool(x['closed'])for x in ledger['slots']),qualified_success=sum(x['qualified_success']is True for x in ledger['slots']),unexecuted=sum(not x['registered']for x in ledger['slots']));write_ledger(ledger);print(json.dumps(dict(classification=classification,actual_native=review['actual_native'],own_replay_native=review['own_replay_native'])))
if __name__=='__main__':main('--barrier'in __import__('sys').argv)
