"""One conditional launch after V705 fully closes; never run alongside it."""
import fcntl,hashlib,json,os,subprocess,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
nightroot=repo/'runs/global_dynamic_overnight_20261102';nightroot.mkdir(exist_ok=True)
with (nightroot/'launch.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 ledger=read(repo/'GLOBAL_DYNAMIC_OVERNIGHT_LEDGER_20261102.json')
 assert ledger['hard_deadline_unix']==1793664000. and not ledger['closed']
 if ledger['development_revisions_started'] or (repo/'runs/v706_global_field_qualification/LAUNCH.json').exists():
  print(json.dumps({'status':'ALREADY_LAUNCHED_OR_BUDGET_USED','no_new_instance':True}));raise SystemExit(0)
 root=repo/'runs/v705_rpccr_prospective_pairs';current=read(repo/'CURRENT_EXPERIMENT.json')
 if not (root/'FINALIZED.json').exists() or not (repo/'runs/v705_git_sync_result.json').exists() or current.get('active_automation')=='phase-v705':
  print(json.dumps({'status':'WAITING_FOR_V705_FULL_CLOSURE','integrations':0}));raise SystemExit(0)
 final=read(root/'FINALIZED.json');a=read(root/'FINAL_INDEPENDENT_AUDIT.json')
 assert final['status']==a['status']=='PROSPECTIVE_COMPUTE_EVIDENCE_COMPLETE' and all(a['checks'].values()),'V705_COMPLETE_EVIDENCE_NOT_PASSED'
 assert a['full_condition_success_rates']['FULL']==1.,'V705_FULL_NOT_FOUR_OF_FOUR'
 assert (repo/'REVIEW_PENDING').exists(),'OLD_REVIEW_CLOSURE_NOT_COMPLETE'
 assert time.time()+5400+300<1793664000.,'INSUFFICIENT_OVERNIGHT_DEVELOPMENT_BUDGET'
 freeze=read(own/'CANDIDATE_FREEZE.json');assert all(hashlib.sha256((repo/n).read_bytes()).hexdigest()==h for n,h in freeze['files'].items()),'PREPARED_SOURCE_CHANGED'
 with (repo/'runs/v648_static_unknown/execution.lock').open('a+') as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
 out=repo/'runs/v706_global_field_qualification';out.mkdir(exist_ok=True);assert not (out/'development01').exists()
 original=(repo/'REVIEW_PENDING').read_bytes();(out/'REVIEW_PENDING.before').write_bytes(original)
 (repo/'REVIEW_PENDING').unlink()
 try:
  with (repo/'runs/v706_driver.console').open('w') as stream:
   child=subprocess.Popen(['timeout','--signal=TERM','--kill-after=5s','5710s','python','-B',str(own/'execute_development.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
 except BaseException:
  (repo/'REVIEW_PENDING').write_bytes(original);raise
 dump(out/'LAUNCH.json',{'outer_pid':child.pid,'outer_limit_s':5710,'development_limit_s':5400,'finalization_allowance_s':300,'overnight_hard_deadline_unix':1793664000.,'v705_status':final['status'],'conditional_prerequisites_verified':True})
 current.update(status='V706_GLOBAL_FIELD_DEVELOPMENT_LAUNCHED',protocol=str(own.relative_to(repo)/'PROTOCOL.md'),active_run='runs/v706_global_field_qualification/development01',active_pid=child.pid,active_automation='phase-global-overnight',analysis_active='V706',analysis_window_closed=False,report='docs/RPCCR_GLOBAL_FIELD_V706_REPORT.md');dump(repo/'CURRENT_EXPERIMENT.json',current)
 print(json.dumps({'status':'V706_LAUNCHED_ONCE','outer_pid':child.pid}))
