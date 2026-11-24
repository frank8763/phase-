"""Closed machine-evidence accounting only, no model/audit/replay rerun."""
from pathlib import Path
import hashlib,json,os,sys,time,fcntl
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1829_teb_common_exact_bridge';D=R/'runs/v1831_teb_common_runtime_recovery';ROOT=R/'runs/v1805_common_algorithm_registry'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 os.sched_setaffinity(0,{5});c=read(O/'COMPLETION.json');assert c['closed']and c['review_restored']and c['lock_idle'];assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 i=read(O/'OWNED_CHILD.json');p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split()[21]!=i['start_ticks']
 if '--barrier'in sys.argv:
  for n in ['FULL_REMOTE_VERIFIED.json','TRANSPORT_CLEANUP.json','remote_delivery/FINALIZED.json']:assert read(D/n)['passed']
  assert not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists()
  b=dict(passed=True,closed_result_path=str((O/'COMPLETION.json').relative_to(R)),closed_result_sha256=sha(O/'COMPLETION.json'),remote_proof_path=str((D/'FULL_REMOTE_VERIFIED.json').relative_to(R)),remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),cleanup_proof_path=str((D/'TRANSPORT_CLEANUP.json').relative_to(R)),cleanup_proof_sha256=sha(D/'TRANSPORT_CLEANUP.json'),every_block_member_whole_index_SHA_verified=True,scientific_passed=c['passed'],all_originals_retained=True,models_authorized=False,late_outside_archive=True);assert not(O/'POST_ROUND_STORAGE_BARRIER.json').exists();put(O/'POST_ROUND_STORAGE_BARRIER.json',b)
  ledger=read(ROOT/'LEDGER.json');row=next(x for x in ledger['slots']if x['method']=='TEB'and x['task_id']=='common_01');row['remote_barrier_sha256']=sha(O/'POST_ROUND_STORAGE_BARRIER.json');row['remote_closed']=True;put(ROOT/'LEDGER.json',ledger);print(json.dumps(dict(remote_closed=True)));return
 assert (O/'actual/RESULT.json').exists(),'MACHINE_RESULT_MISSING_KEEP_COUNTS_UNKNOWN'
 m=read(O/'actual/RESULT.json');assert m['closed']and sha(O/'actual/RESULT.json')==c['machine_result_sha256']and c['all_source_SHA_verified_after_child_exit']
 for n,h in read(O/'SOURCE_FREEZE.json')['files'].items():assert sha(R/n)==h
 n=m['new_actual_native'];complete=bool(type(n)is int and n>0 and m['evidence_saved']and m['fully_recorded_native']==n==m['own_replay_native']and not m.get('model_native_inflight_unknown')and(m.get('replay')or{}).get('passed'))
 independent=m.get('independent_audit')or{};safe=complete and bool(independent.get('passed'))and not m['secondary_errors'];first=m.get('first_error');error=None if not first else first['error']
 functional_refusals={"AssertionError('TEB_ORIGINAL_FINITE_QUERY_REFUSED')","AssertionError('TEB_RAW_CURVATURE_OUTSIDE_COMMON_CAP')","AssertionError('TEB_RAW_SPEED_IN_BRAKING_DEADBAND')","AssertionError('TEB_IN_PLACE_ROTATION_REFUSED')","AssertionError('TEB_CURRENT_CYCLE_COMPLETE_STOP_REFUSED')","AssertionError('TEB_CURRENT_5_NATIVE_RETAINED_STOP_REFUSED')","AssertionError('TEB_REFERENCE_NO_FINITE_CURRENT_COMMAND')","AssertionError('TEB_NATIVE_LIMIT_NO_WHOLE_GOAL')","AssertionError('TEB_FIXED_NATIVE_WORK_FINISHED_WITHOUT_WHOLE_GOAL')"}
 whole=bool(c['passed']and m['passed']and m.get('whole_navigation_passed')and independent.get('whole_navigation_passed'));valid_negative=safe and error in functional_refusals
 classification='QUALIFIED_WHOLE_GOAL_SUCCESS'if whole else'VALID_FINITE_METHOD_REFUSAL_WITH_INDEPENDENT_PREFIX_AUDIT'if valid_negative else'TECHNICAL_OR_UNQUALIFIED_EVIDENCE_CENSOR'
 review=dict(closed=True,common_method='TEB',common_task='common_01',classification=classification,qualified_whole_navigation_passed=whole,valid_finite_method_negative=valid_negative,actual_native=n,own_replay_native=m['own_replay_native'],physical=m.get('physical'),replay=m.get('replay'),independent_audit=independent,first_error=first,secondary_errors=m['secondary_errors'],outer_first_error=c['first_error'],canonical_initializations=m['canonical_vehicle_initializations'],internal_factory_count=None,full_modelwork_total=None,source_members=len(read(O/'SOURCE_FREEZE.json')['files']),source_all_SHA_verified_after_exit=True,no_global_algorithm_failure_or_superiority_claim=True,scientific_denominator_retained=True,remote_pending=True)
 assert not(O/'RUNTIME_CLOSED_REVIEW.json').exists();put(O/'RUNTIME_CLOSED_REVIEW.json',review)
 p=ROOT/'LEDGER.json';ledger=read(p);row=next(x for x in ledger['slots']if x['method']=='TEB'and x['task_id']=='common_01');row.update(registered=True,closed=True,status=classification,qualified_success=whole,actual_native=n,own_replay_native=m['own_replay_native'],algorithm_outcome='FINITE_REFUSAL'if valid_negative else'WHOLE_GOAL'if whole else None,technical_failure=None if valid_negative or whole else first,result_path=str((O/'RUNTIME_CLOSED_REVIEW.json').relative_to(R)),result_sha256=sha(O/'RUNTIME_CLOSED_REVIEW.json'));ledger.update(closed=sum(bool(x['closed'])for x in ledger['slots']),qualified_success=sum(x['qualified_success']is True for x in ledger['slots']));put(p,ledger)
 text='# 首TEB共同任务实际结果\n\n分类：'+classification+'。原HCP point-goal适配/原配置未调，不冒完整ROSplugin。\n\n'+json.dumps(review,ensure_ascii=False,indent=2)+'\n\n原全部20消融与历史G4C/Final300另账；此case不能单独说明相对RPCCR收益或统计优势。\n'
 (R/'docs/TEB_COMMON_PHASE_V1829_REPORT.md').write_text(text);print(json.dumps(dict(classification=classification,actual_native=n,own_replay_native=m['own_replay_native'],whole=whole)))
if __name__=='__main__':main()
