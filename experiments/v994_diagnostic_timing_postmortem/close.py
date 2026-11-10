"""Close analysis/accounting and stage only this root, without model imports."""
import fcntl,hashlib,json,time
from pathlib import Path

R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
O=R/'runs/v994_diagnostic_timing_postmortem';ROOT=R/'runs/daytime_20261110_until20'
REC=R/'records/nav2_v993_20261110';OLD=R/'experiments/v993_steering_transient_diagnosis'
def read(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')==sha(ROOT/'REVIEW_PENDING.before')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert read(R/'runs/v993_steering_transient_diagnosis/COMPLETION.json')['closed']
    original=read(OLD/'SOURCE_FREEZE.json')['files']
    assert all(sha(R/p)==h for p,h in original.items())
    diagnosis=read(O/'SAVED_PREFIX_DIAGNOSIS.json');qualification=read(O/'RESPONSE_LOOP_QUALIFICATION.json')
    assert read(O/'FROZEN_FAILURE_QUALIFICATION.json')['passed']and qualification['passed']
    REC.mkdir(exist_ok=False)
    final=dict(closed=True,status=diagnosis['status'],diagnostic_evidence_passed=False,navigation_passed=False,
        counts=diagnosis['counts'],unexecuted_diagnostic_slots=[2,3],scientific_candidates_executed=0,
        new_navigation_trials=0,new24_executed=0,models_during_analysis_and_close=0,
        old_source_files_verified=len(original),original_guard_restored=True,execution_lock_idle=True,
        failed_second_task_missing_full_stop_and_replay=True,exact_failure_lag_unknown=True,
        original_mechanical_cause_unique=False,zero_model_response_loop_cases=len(qualification['cases']),
        total_deadline_unix=1794312000.,model_authority=False,automatic_extension=False)
    dump(REC/'FINAL_INDEPENDENT_ACCOUNTING.json',final)
    for src,name in [(ROOT/'USER_AUTHORIZATION.json','USER_AUTHORIZATION.json'),
                     (R/'runs/v993_steering_transient_diagnosis/COMPLETION.json','COMPLETION.json'),
                     (R/'runs/v993_steering_transient_diagnosis/RESULTS.json','RESULTS.json'),
                     (O/'SAVED_PREFIX_DIAGNOSIS.json','SAVED_PREFIX_DIAGNOSIS.json'),
                     (O/'FROZEN_FAILURE_QUALIFICATION.json','FROZEN_FAILURE_QUALIFICATION.json'),
                     (O/'RESPONSE_LOOP_QUALIFICATION.json','RESPONSE_LOOP_QUALIFICATION.json')]:
        (REC/name).write_bytes(src.read_bytes())
    closure=dict(final,closed_unix=time.time(),stop_reason='V993 original timing gate failed; no dependency resumed',
                 report='docs/RPCCR_STEERING_DIAGNOSTICS_V993_V994_REPORT.md')
    dump(ROOT/'CLOSURE.json',closure)
    dump(ROOT/'LEDGER.json',dict(status='CLOSED_NOT_PASSED_TIMING_INTERRUPTION',absolute_deadline_unix=1794312000.,
        diagnostic_started=True,diagnostic_slots_completed=1,diagnostic_slot_failed=1,diagnostic_slots_unexecuted=[2,3],
        candidate_started=False,model_authority=False,counts=diagnosis['counts'],closed_before_deadline=True))
    state=read(R/'CURRENT_EXPERIMENT.json');state.update(status='REVIEW_PENDING',source_revision='V993_CLOSED_TIMING_INTERRUPTION',
        decision_freeze=str((OLD/'SOURCE_FREEZE.json').relative_to(R)),protocol=str((OLD/'PROTOCOL.md').relative_to(R)),
        report=closure['report'],active_entrypoint=None,active_run=None,active_window=None,next_physical_authorized=False,
        execution_window_closed=True,v994_zero_model_diagnosis=dict(models=0,integrations=0,original_counts=diagnosis['counts'],
            execution_loop_fault_cases=16,physical_cause_unresolved=True,physical_ready=False))
    dump(R/'CURRENT_EXPERIMENT.json',state)
    with(R/'RESEARCH_STATUS.md').open('a')as f:
        f.write('\n- V993固定转向辨识未通过：第一保持转角800新原生/6883全重放通过；第二301新原生后NATIVE_WALL_LAG，完整停车/重放未执行，另两项与候选/整路依赖停止。2车辆/12166历史/1101新增/6883自身重放/私有0，全部已执行保存前缀净空>=.273036567/坏0/控制与历史重建通过；第二175.51ms后置记录间隔不是准确故障lag，唯一GC/调度/IO因果未知。V994无模型AST故障精确重现与16项新计时循环资格通过，不重启模型或修改1965冻结源。20:00原总截止保持，实际15:07:58停而非跑满；guard/锁保持，动态仍未通过。见docs/RPCCR_STEERING_DIAGNOSTICS_V993_V994_REPORT.md。\n')
    files={str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()and p.name!='SOURCE_FREEZE.json'}
    dump(C/'SOURCE_FREEZE.json',dict(final=True,models=0,integrations=0,physical_authority=False,files=files,
         original_v993_freeze_sha256=sha(OLD/'SOURCE_FREEZE.json')))
    print(json.dumps(final))
if __name__=='__main__':main()
