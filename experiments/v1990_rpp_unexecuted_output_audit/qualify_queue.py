"""Real metadata alias/continuation/cleanup guard tests in fixture-only roots."""
from context import R,C,O,load,put
from pathlib import Path
import copy,hashlib,json,os
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 os.sched_setaffinity(0,{6});campaign=load('RPP_night_queue_software_only',C/'campaign.py');fixture=O/'queue_software_fixture';fixture.mkdir(exist_ok=False);root=fixture/'alias_root';root.mkdir();s=root/'rounds/common_02__RPP';s.mkdir(parents=True);(root/'runtime_archives').mkdir()
 for n in ['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','SOURCE_INHERITED_CHAINS.json','AUTHORIZATION.json','PRIOR_CLOSED_BARRIERS.json','LIMITS_DRAFT.json','NATIVE_DEPENDENCIES.json']:(root/n).write_text('{"fixture_only":true}\n')
 original=campaign.ROOT;campaign.ROOT=root
 try:
  row=dict(round_id='common_02__RPP',output_root=str(s.relative_to(R)));assert campaign.attach(row)==s
  assert all((root/n).stat().st_ino==(s/n).stat().st_ino for n in ['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json'])
  try:campaign.attach(row)
  except AssertionError:duplicate_refused=True
  else:raise AssertionError('DUPLICATE_METADATA_VIEW_ACCEPTED')
 finally:campaign.ROOT=original
 good=dict(closed=True,qualified_whole_navigation_passed=True,valid_finite_method_negative=False,secondary_errors=[],outer_first_error=None);finite=dict(good,qualified_whole_navigation_passed=False,valid_finite_method_negative=True)
 assert campaign.can_continue(good)and campaign.can_continue(finite)
 negatives=[dict(good,closed=False),dict(good,qualified_whole_navigation_passed=False),dict(finite,secondary_errors=[dict(stage='safety')]),dict(good,outer_first_error=dict(error='owner')),dict(closed=True)]
 assert not any(campaign.can_continue(x)for x in negatives)
 os.environ['PHASE_RPP_ASSIGNMENT']='common_02__RPP';cleanup=load('RPP_new_cache_cleanup_fixture_only',R/'experiments/v1992_rpp_remaining_runtime_recovery/cache_cleanup.py');cleanup_out=[]
 for case in ['changed_SHA','source_protected','verified_cache']:
  base=fixture/case;src=base/'ROOT';S=src/'rounds/common_02__RPP';D=src/'runtime_archives/common_02__RPP';(S/'actual').mkdir(parents=True);(D/'remote_delivery').mkdir(parents=True);cleanup.ROOT=src;cleanup.S=S;cleanup.D=D
  payload=S/'actual/PREDICTIONS.pack';payload.write_bytes(b'fixture-only-not-physical'*100);kept=S/'actual/RESULT.json';kept.write_text('{"fixture_only":true}\n')
  entry=dict(path=str(payload.relative_to(R)),sha256=sha(payload),bytes=payload.stat().st_size);write=lambda p,x:p.write_text(json.dumps(x)+'\n')
  write(src/'SOURCE_FREEZE.json',dict(files={str(payload.relative_to(R)):sha(payload)}if case=='source_protected'else{}));write(S/'COMPLETION.json',dict(closed=True,review_restored=True,lock_idle=True,fixture_only=True));write(D/'ARCHIVE_INDEX.json',dict(files=[entry]));write(D/'FULL_REMOTE_VERIFIED.json',dict(passed=True,every_asset_actual_download_SHA=True,every_member_SHA_and_link_text=True,whole_archive_SHA=True,recovery_index_download_SHA=True,fixture_only=True));write(D/'TRANSPORT_CLEANUP.json',dict(passed=True,fixture_only=True));write(D/'remote_delivery/RESULT.json',dict(passed=True,fixture_only=True));write(D/'remote_delivery/CLAIM.json',dict(pid=999999999,fixture_only=True))
  if case=='changed_SHA':payload.write_bytes(b'changed')
  try:cleanup.main()
  except AssertionError:
   assert case!='verified_cache'and payload.exists()and kept.exists();cleanup_out.append(dict(case=case,delete_refused=True))
  else:
   assert case=='verified_cache'and not payload.exists()and kept.exists()and read(S/'LOCAL_RAW_CACHE_CLEANUP.json')['passed'];cleanup_out.append(dict(case=case,verified_cache_only_removed=True))
 value=dict(passed=True,metadata_views_actual_hardlink_exact_bytes=True,duplicate_alias_refused=duplicate_refused,qualified_whole_and_finite_only_continue=True,technical_safety_unknown_cases_refused=len(negatives),actual_cache_cleanup_function_fixture_cases=cleanup_out,fixtures_never_used_for_runtime_admission=True,models=0,RPP_DLL=0,physical_native=0,replay_native=0,canonical_ledger_unchanged=True)
 put(O/'QUEUE_SOFTWARE_PROOF.json',value);print(json.dumps(value));return value
if __name__=='__main__':check()
