"""Idempotence-protected zero-model accounting and local archive closure."""
import fcntl,importlib.util,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v945_rpccr_observation_liveness';REC=R/'records/nav2_v945_20261109'
sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from handshake import verify_sources
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not(O/'FINALIZED.json').exists(),'ALREADY_FINALIZED'
    done=json.loads((O/'COMPLETION.json').read_text());assert done['closed'];verify_sources(R,C/'SOURCE_FREEZE.json')
    assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes()
    REC.mkdir(exist_ok=True)
    for name in ['COMPLETION.json','RESULTS.json','AUTHORIZATION.json','ROUND_WINDOW.json','ZERO_MODEL_QUALIFICATION.json','RECOVERY_SAVED_QUALIFICATION.json','RECOVERY_CALLBACK_QUALIFICATION.json','LOCAL_STOP_AUDIT_QUALIFICATION.json','NATIVE_SEAM_QUALIFICATION.json','INGRESS_QUALIFICATION.json','PREPARATION_ERRORS.json','PLATFORM_RESULT.json','REPEAT.json']:
        if(O/name).exists():(REC/name).write_bytes((O/name).read_bytes())
    platform=json.loads((O/'PLATFORM_RESULT.json').read_text())if(O/'PLATFORM_RESULT.json').exists()else{}
    total=lambda key:None if any(x.get(key)is None for x in done['rows'])else sum(x[key]for x in done['rows'])
    summary=dict(status=done['status'],platform_actual_native=platform.get('actual_native'),platform_own_replay_native=platform.get('replay_native'),
                 navigation_actual_native=total('actual_native'),navigation_own_replay_native=total('replay_native'),navigation_private_native=total('private_native'),
                 platform_passed=platform.get('passed',False),attempted_navigation=len(done['rows']),unexecuted_navigation=done['unexecuted_navigation'],new24=0,training=0,hardware=0,
                 deadline_unix=done['deadline_unix'],remote_pending=True,closed_reason=done['error'])
    (REC/'RESULT_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    report=R/'docs/RPCCR_CERTIFIED_RECOVERY_V945_REPORT.md'
    report.write_text('# V945 RP-CCR持续观测活性回归\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\nV943获证恢复与FeasibleRPP原样保留，仅将持续监督200ms与新命令/安装50ms门分开，并持久化故障输入和部分事务事件。所有原命令/原生安全门、旧证书有效期、路径跟随界和目标门保持。历史V827三路线/V828六完整成功不能当作本版本成功，未执行新24。完整解释见RPCCR_REGRESSION_RECOVERY_V945_REPORT.md。\n')
    spec=importlib.util.spec_from_file_location('v945_archive',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    from types import SimpleNamespace
    import tarfile
    def expanded_open(*args,**kw):
        if str(kw.get('mode','')).startswith('w'):kw['dereference']=True
        return tarfile.open(*args,**kw)
    m.tarfile=SimpleNamespace(open=expanded_open)
    m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=False)
    files=[]
    for base in [C,R/'runs/v858_nav2_verified/v945',REC]:files.extend(m.walk(base))
    files.extend(p for p in m.walk(O)if not any(x in p.relative_to(O).parts for x in ['cloud','restore','saved','response_restore','response_saved','audit_fixture','audit_fixture02']) and p.name not in ['campaign.console','finalize.console'])
    files.append(report);archive=m.archive('phase-v945-20261109',files)
    (REC/'RECORD_INDEX.json').write_text(json.dumps(dict(repository='frank8763/phase-',release_tag='phase-rpccr-recovery-v945-20261109',archives=[{k:v for k,v in archive.items()if k!='files'}]),indent=2)+'\n')
    proof=dict(status='LOCAL_FINALIZED_REMOTE_PENDING',scientific_status=done['status'],all_sources_and_decompressed_sha_verified=True,models=0,integrations=0,at=time.time())
    (REC/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(proof,indent=2)+'\n');(O/'FINALIZED.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
