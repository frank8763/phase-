"""Journal-only closure change, saved-data quota seam, no numerical calls."""
from context import R,C,O,read,put,sha,load
from pathlib import Path
import ast,json,os,subprocess,time,traceback
def main():
 os.sched_setaffinity(0,{5});assert not(O/'SOURCE_ONCE.json').exists();put(O/'SOURCE_ONCE.json',dict(unix=time.time(),models=0));files={};result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,constructors=0,queries=0,physics=0,replay=0)
 try:
  P=R/'runs/v2021_mppi_parallel_counter_affinity';old=R/'experiments/v2021_mppi_parallel_counter_affinity';H=R/'experiments/v2028_mppi_journal_snapshot_evidence'
  assert read(P/'SOURCE_QUALIFICATION.json')['passed']and read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']and read(P/'COMPONENT_POST_STORAGE_BARRIER.json')['passed'];x=read(P/'COMPLETION.json');assert x['closed']and x['actual_native']==x['own_replay_native']==2210 and x['machine_first_error']['stage']=='SAVE_JOURNAL'and x['independent_audit']is None
  files.update(read(P/'SOURCE_FREEZE.json')['files']);prior=files.copy();same=[]
  for p in old.glob('*.py'):
   if p.name=='qualify_source.py':continue
   expected=p.read_text().replace(old.name,C.name).replace('v2022_mppi_parallel_counter_evidence','v2028_mppi_journal_snapshot_evidence')
   if p.name=='driver.py':
    line="     attempt('SAVE_JOURNAL',lambda:save('APPLIED_JOURNAL.json',journal))\n";assert expected.count(line)==1;expected=expected.replace(line,'');needle="     if result.get('evidence_saved')and not inside and len(v.rows)==actual and remaining(window)>800:";assert expected.count(needle)==1;expected=expected.replace(needle,"     attempt('JOURNAL_QUIESCENT_FRESH_GRANT',lambda:refresh('COMPLETE_ZERO_TAIL_OR_CLOSURE',ttl=300))\n     attempt('SAVE_JOURNAL',lambda:save('APPLIED_JOURNAL.json',journal))\n"+needle)
   if p.name=='owner.py':expected=expected.replace('35*1024**2','(34*1024**2+256*1024)').replace('console<=1024**2','console<=64*1024').replace('CONSOLE_1MIB','CONSOLE_64KIB')
   assert(C/p.name).read_text()==expected,'NON_JOURNAL_SOURCE_CHANGE:'+p.name;same.append(p.name)
  fixture=R/'runs/v1973_rpp_file_input_ready_barrier/actual/APPLIED_JOURNAL.json';assert len(read(fixture))==2210
  # Snapshot values are explicitly synthetic quota states, not a new census.
  script="import sys,os,json;from pathlib import Path;sys.path.insert(0,"+repr(str(C))+");from context import R,C,O,load,read;from quota import EvidenceQuota,base,grant;import resources;out=O/'software_journal';out.mkdir();limits=read(O/'LIMITS_DRAFT.json');snapshot=lambda output,limits:(13*1024**2,14*1024**3);base.measure=snapshot;grant.base.measure=snapshot;base.used=lambda path:13*1024**2;grant.base.used=base.used;q=EvidenceQuota(out,limits);q.bind_external_names([]);q.write_enforcement_active=True;resources.reserve_terminal(q);q.prepare_grant(1,phase='COMPLETE_ZERO_TAIL_OR_CLOSURE',valid_for_s=300,external_writers=[]);journal=read(R/"+repr(str(fixture.relative_to(R)))+");atomic=load('original_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py').atomic;boundary=load('original_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py').OutputBoundary;red=False\ntry:q.atomic(out/'APPLIED_JOURNAL.json',journal,atomic)\nexcept AssertionError as e:assert str(e)=='BYTE_GRANT_EXHAUSTED';red=True\nassert red and not(out/'APPLIED_JOURNAL.json').exists();resources.prepare(q,'COMPLETE_ZERO_TAIL_OR_CLOSURE',ttl=300)\nwith boundary(out,q.charge_write):q.atomic(out/'APPLIED_JOURNAL.json',journal,atomic)\nassert read(out/'APPLIED_JOURNAL.json')==journal;print(json.dumps(dict(passed=True,exhausted_grant_refused=True,fresh_quiescent_grant_original_atomic_and_boundary_passed=True,rows=len(journal),serialized_bytes=(out/'APPLIED_JOURNAL.json').stat().st_size,synthetic_quota_snapshot_not_actual_census=dict(task_bytes=13*1024**2,allruns_bytes=14*1024**3),models=0,physical_steps=0,replay=0,full_original_journal_fields_unchanged=True)))"
  p=subprocess.run(['taskset','-c','6','/usr/bin/python3','-B','-c',script],cwd=R,env=dict(os.environ,PHASE_REPO=str(R)),capture_output=True,timeout=20);(O/'JOURNAL_SOFTWARE.console').write_bytes(p.stdout+p.stderr);assert p.returncode==0,p.stderr.decode();software=json.loads(p.stdout);put(O/'JOURNAL_SOFTWARE_PROOF.json',software);test=O/'software_journal/APPLIED_JOURNAL.json';assert len(read(test))==2210;test.unlink()
  p=subprocess.run(['taskset','-c','6','/usr/bin/python3','-B',str(C/'pilot_entry.py')],cwd=R,env=dict(os.environ,PHASE_REPO=str(R)),capture_output=True,timeout=10);assert p.returncode!=0 and b'MPPI_COMPONENT_NOT_ADMITTED'in p.stderr
  for folder in [C,H,R/'experiments/v2025_mppi_quiescent_journal_grant']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in [O/n for n in ['PILOT_TASK.json','LIMITS_DRAFT.json','NATIVE_DEPENDENCIES.json','AUTHORIZATION.json','JOINT_RESOURCE_RESERVATION.json','JOURNAL_SOFTWARE_PROOF.json']]+[P/n for n in ['SOURCE_QUALIFICATION.json','SOFTWARE_CHECK_PROOF.json','COMPONENT_POST_STORAGE_BARRIER.json','COMPLETION.json','RUNTIME_CLOSED_REVIEW.json']]+list((R/'runs/v2024_mppi_closed_component_cold_cache').glob('*.json'))+[fixture]:files[str(p.relative_to(R))]=sha(p)
  for p in (R/'runs/v2025_mppi_quiescent_journal_grant').glob('*.json'):files[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in files.items())
  proof=dict(passed=True,only_journal_order_quiescent_grant_and_narrower_parent_console_changed=True,all_source_bodies_equal_except_explicit_journal_IO_change=same,actual_saved_journal_original_atomic_boundary_software=software,old2210_actual_replay_error0_without_independent_audit_not_upgraded=True,no_old_numerical_replay_or_audit_reexecuted=True,unadmitted_entry_before_model=True)
  put(O/'SOFTWARE_CHECK_PROOF.json',proof);files[str((O/'SOFTWARE_CHECK_PROOF.json').relative_to(R))]=sha(O/'SOFTWARE_CHECK_PROOF.json');put(O/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False));put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(source_members_seen=len(files),models_authorized=False))
 finally:result['closed']=True;put(O/'SOURCE_QUALIFICATION.json',result);put(O/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,constructors=0,queries=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
