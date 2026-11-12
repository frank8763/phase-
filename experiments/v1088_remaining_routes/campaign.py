"""Four fixed tasks, same science, no NS rerun and no new confirmation."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];ORIGINAL=R/'experiments/rpccr_execution_core/fresh_campaign.py'
def once(s,old,new):
 assert s.count(old)==1,old
 return s.replace(old,new)
def patched_source():
 s=ORIGINAL.read_text()
 s=once(s,"CORE/cfg['worker']","Path(cfg['worker_path'])")
 s=once(s,"CORE/cfg['audit']","Path(cfg['audit_path'])")
 s=once(s,'wall=time.time();mono=time.monotonic();w=dict(',"boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();wall=time.time();mono=time.monotonic();w=dict(")
 s=once(s,'duration_s=5400,old_windows_unchanged=True)','duration_s=5400,old_windows_unchanged=True,boot_id=boot)')
 s=once(s,'rows=[];attempted=[];error=None;child=None;repeat=None','rows=[];attempted=[];error=None;child=None;repeat=None;repeat_pairs=[]')
 s=once(s,"assert min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())>2000", "assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'CROSS_BOOT_AUTHORITY_REJECTED';assert min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())>1850")
 old="dump(O/'RESULTS.json',rows)\n  repeat=same_complete(tasks[0],tasks[1])"
 new="dump(O/'RESULTS.json',rows)\n   if task['kind']=='repeat':\n    baseline=next(t for t in tasks if t['kind']=='main'and t['case_id']==task['case_id']);pair=same_complete(baseline,task);repeat_pairs.append(dict(case_id=task['case_id'],**pair));dump(O/'COMPLETE_REPEATS.json',repeat_pairs)\n  repeat=dict(passed=len(repeat_pairs)==2 and all(p['passed']for p in repeat_pairs),pairs=repeat_pairs)"
 s=once(s,old,new)
 s=once(s,'len(rows)==2','len(rows)==4')
 s=once(s,"(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));", "(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'AUTHORIZATION.json',dict(models_authorized=False,closed=True,user_text='下一步开始',no_automatic_additional_model=True));dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));")
 s=once(s,"passed=error is None and len(rows)==4", "passed=error is None and all(sha(R/p)==h for p,h in freeze.items())and (R/'REVIEW_PENDING').read_bytes()==guard and len(rows)==4")
 s=once(s,"latest_report=cfg['report']);", "latest_report=cfg['report'],next_physical_authorized=False,next_scope='Review remaining-route results; no automatic new24 or additional physics');")
 s=s.replace('Fresh canonical t0 NS navigation main plus conditional same-version full repeat, observed development route','Remaining fixed WEST_EAST and declared north-shifted EAST_WEST mains and full repeats; NS milestone reused read-only')
 s=s.replace('single NS main+repeat gate only; three-route/24 not executed','two remaining routes main+repeat only; no new24 executed')
 s=s.replace('This is one observed NS developmental route from canonical t0, not three-route or24 confirmation.','These are two observed development routes; existing NS milestone is separate. EAST_WEST starts at declared(4,-1.9), not original(4,-2). No24 confirmation.')
 return s
if __name__=='__main__':
 cfg=json.loads(Path(sys.argv[1]).read_text());O=Path(cfg['run_root'])
 assert json.loads((O/'AUTHORIZATION.json').read_text())['models_authorized']
 prerequisite=json.loads((R/'records/nav2_v1088_preparation_20261112/COMPLETION.json').read_text());assert prerequisite['passed'],'CLOSED_EVIDENCE_BACKUP_REQUIRED'
 tasks=json.loads(Path(cfg['task_table']).read_text());assert [t['case_id']for t in tasks]==['WEST_EAST','WEST_EAST','EAST_WEST','EAST_WEST']and[t['kind']for t in tasks]==['main','repeat','main','repeat']
 assert json.loads((R/'runs/v1087_ns_repeat_after_shutdown/COMPLETION.json').read_text())['passed']
 exec(compile(patched_source(),str(ORIGINAL),'exec'),dict(__name__='__main__',__file__=str(ORIGINAL)))
