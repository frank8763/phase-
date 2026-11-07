"""One launch, two prerequisite-gated stages, one immutable campaign deadline."""
import datetime
import fcntl
import os
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path
from evidence_rules import dump, read, sha

repo = Path(__file__).resolve().parents[2]
own = Path(__file__).parent
root = repo/'runs/dynamic_acceptance_20261105'
authorization = repo/'RPCCR_DYNAMIC_ACCEPTANCE_AUTHORIZATION_20261105.json'
ledger_path = repo/'RPCCR_DYNAMIC_ACCEPTANCE_LEDGER_20261105.json'
current_path = repo/'CURRENT_EXPERIMENT.json'
root.mkdir(parents=True,exist_ok=True)
lock = (root/'campaign.lock').open('a+')
fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
assert not (root/'ROUND_WINDOW.json').exists(), 'CAMPAIGN_ALREADY_STARTED_NO_RETRY'
auth = read(authorization)
deadline = auth['absolute_deadline_unix']
assert time.time()+40500 < deadline, 'INSUFFICIENT_CAMPAIGN_BUDGET'
assert read(root/'ZERO_MODEL_QUALIFICATION.json')['passed'], 'PREPARATION_NOT_QUALIFIED'
assert (repo/'REVIEW_PENDING').exists()
guard = (repo/'REVIEW_PENDING').read_bytes()
(root/'REVIEW_PENDING.before').write_bytes(guard)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
window = dict(started_unix=time.time(),absolute_deadline_unix=deadline,pid=os.getpid(),round_closed=False,
              physics_only_run_phase=True,training_updates=0,stage_access=0,real_robot=0)
dump(root/'ROUND_WINDOW.json',window)
day = read(ledger_path)
status = 'RUNNING'
active = None
stage_results = []
signal.signal(signal.SIGTERM,lambda *_: (_ for _ in ()).throw(TimeoutError('CAMPAIGN_TERMINATED')))
try:
    for directory in ['v821_norm_route_development','v822_norm_dynamic_confirmation']:
        worker = repo/'experiments'/directory
        config = read(worker/'BATCH.json')
        freeze = read(worker/'CANDIDATE_FREEZE.json')
        assert all(sha(repo/n)==h for n,h in freeze['files'].items()), 'CANDIDATE_SOURCE_CHANGED'
        dep = read(repo/config['dependency']/'FINALIZED.json')
        assert dep['development_passed'], 'DEVELOPMENT_DEPENDENCY_NOT_PASSED'
        if config['confirmation']:
            assert dep['combined_three_route_development_passed'], 'THREE_ROUTE_DEVELOPMENT_GATE_NOT_PASSED'
        assert time.time()+config['minimum_start_budget_s']+3 < deadline, 'INSUFFICIENT_REMAINING_BUDGET_NO_PARTIAL_POOL'
        with (repo/'runs/v648_static_unknown/execution.lock').open('rb') as probe:
            fcntl.flock(probe,fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert (repo/'REVIEW_PENDING').read_bytes()==guard, 'GUARD_NOT_RESTORED'
        counter = 'confirmation_batches_started' if config['confirmation'] else 'development_extensions_started'
        assert day[counter]==0, 'STAGE_ALREADY_CLAIMED'
        day[counter] += 1
        day.update(status='RUNNING_'+config['label'],current_stage=directory,active_simulation=True)
        dump(ledger_path,day)
        stage_root = repo/config['output']
        stage_root.mkdir(exist_ok=True)
        assert not (stage_root/'driver.console').exists()
        with (stage_root/'driver.console').open('x') as stream:
            active = subprocess.Popen([sys.executable,'-B',str(worker/'execute.py')],cwd=repo,
                                      stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            dump(root/'ACTIVE.json',dict(stage=directory,pid=active.pid,absolute_deadline_unix=deadline))
            current = read(current_path)
            current.update(status='RUNNING_DYNAMIC_ACCEPTANCE',state='RUNNING_DYNAMIC_ACCEPTANCE',
                           current_experiment=config['label'],protocol=str(worker.relative_to(repo)/'PROTOCOL.md'),
                           decision_freeze=str(worker.relative_to(repo)/'CANDIDATE_FREEZE.json'),
                           active_run=config['output']+'/'+config['window'],active_pid=active.pid,
                           active_entrypoint=str(worker.relative_to(repo)/'execute.py'),execution_window_closed=False,
                           requires_user_review_before_next_experiment=False,active_automation='phase-dynamic-acceptance-20261105')
            current['dynamic_acceptance_20261105'] = dict(authorization=str(authorization.relative_to(repo)),ledger=str(ledger_path.relative_to(repo)),
                absolute_deadline_unix=deadline,active_stage=directory,source_algorithm='V820',new_confirmation_pool='10060001-10060024')
            dump(current_path,current)
            try:
                code = active.wait(timeout=min(config['batch_cap_s'],deadline-time.time())+1800)
            finally:
                if active.poll() is None:
                    os.killpg(active.pid,signal.SIGTERM)
                    try: active.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        os.killpg(active.pid,signal.SIGKILL)
                        active.wait()
                active = None
        assert code==0 and (stage_root/'FINALIZED.json').exists(), 'STAGE_DRIVER_OR_FINALIZATION_FAILED'
        final = read(stage_root/'FINALIZED.json')
        stage_results.append(dict(stage=directory,final=final,final_audit=str((stage_root/'FINAL_INDEPENDENT_AUDIT.json').relative_to(repo))))
        dump(root/'STAGES.json',stage_results)
        assert final['source_and_decompressed_sha_verified'], 'ARCHIVE_NOT_VERIFIED'
        passed = final['confirmation_passed'] if config['confirmation'] else final['combined_three_route_development_passed']
        if not passed:
            status = 'STOPPED_STAGE_NOT_PASSED'
            break
    else:
        status = 'FINITE_FULL_FIELD_DYNAMIC_CONFIRMATION_PASS'
except BaseException as error:
    status = 'STOPPED_EXCEPTION'
    dump(root/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
finally:
    (repo/'REVIEW_PENDING').write_bytes(guard)
    window.update(round_closed=True,status=status,elapsed_s=time.time()-window['started_unix'])
    dump(root/'ROUND_WINDOW.json',window)
    day.update(closed=True,status=status,current_stage=None,active_simulation=False,no_more_models_or_integrations=True,
               stage_results=stage_results,needs_review_commit_and_single_bounded_sync=True)
    dump(ledger_path,day)
    current = read(current_path)
    current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',active_pid=None,active_entrypoint=None,
                   active_run=None,active_window=None,execution_window_closed=True,requires_user_review_before_next_experiment=True)
    current.setdefault('dynamic_acceptance_20261105',{}).update(closed=True,status=status,active_stage=None)
    if status=='FINITE_FULL_FIELD_DYNAMIC_CONFIRMATION_PASS':
        current['finite_full_field_dynamic_acceptance_passed'] = True
        current['finite_full_field_dynamic_acceptance_scope'] = 'same original19 map/three registered routes/single small norm.08 actor/reactive3m discovery'
    dump(current_path,current)
    dump(root/'COMPLETION.json',dict(status=status,stages=stage_results,no_automatic_new_experiments=True,
                                    new_models_in_closure=0,new_integrations_in_closure=0))
    dump(root/'ACTIVE.json',dict(completed=True,status=status))
    (repo/'docs/RPCCR_DYNAMIC_ACCEPTANCE_20261105_REPORT.md').write_text(
        '# RP-CCR 完整场地动态验收实际结果\n\n状态：**'+status+'**。\n\n'+
        '\n'.join('- '+x['stage']+'：'+x['final']['status']+'；详见 '+x['final']['report'] for x in stage_results)+
        '\n\nV820原开发/条件重复不混新池分母。失败、未执行及准确或未知积分分账见各独立终审。'+
        'REVIEW_PENDING恢复，本轮停止模型和积分；不自动比较、修订或新池。有限.08课程，不宣称更宽.12轴类、复杂地图泛化、隐藏突入、实时性或全面算法优势。\n')
print(json.dumps(dict(status=status,stages=len(stage_results))))
