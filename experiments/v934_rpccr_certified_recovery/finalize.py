"""Idempotence-protected zero-model accounting and local archive closure."""
import fcntl,importlib.util,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v934_rpccr_certified_recovery';REC=R/'records/nav2_v934_20261109'
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
    report=R/'docs/RPCCR_CERTIFIED_RECOVERY_V934_REPORT.md'
    report.write_text('# V934 RP-CCR获证恢复调度开发\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\n本轮回到通过静态三路线的FeasibleRPP原FollowPath，未改变底层控制、模型、场景或传感。仅在非零名义提案被原RP-CCR门拒绝且有因果actor支撑后，检查固定13旧范围控制，选择原.155执行/完整2秒刹停与全周期终端证书均通过的进展或退让。零命令与静默停车续证不改成运动；1秒解析轨迹仅作排序，不是后继安全或可达保证。原.15实际/接触自体ctrl速率/完整状态重放门全部保持。只覆盖公开.32频率/.25幅/.08速课程，经验执行界非形式证明；有限原WE开发不等于新24或RAS创新。所有旧失败/源/截止保持。\n')
    spec=importlib.util.spec_from_file_location('v934_archive',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    from types import SimpleNamespace
    import tarfile
    def expanded_open(*args,**kw):
        if str(kw.get('mode','')).startswith('w'):kw['dereference']=True
        return tarfile.open(*args,**kw)
    m.tarfile=SimpleNamespace(open=expanded_open)
    m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=False)
    files=[]
    for base in [C,R/'runs/v858_nav2_verified/v934',REC]:files.extend(m.walk(base))
    files.extend(p for p in m.walk(O)if not any(x in p.relative_to(O).parts for x in ['cloud','restore','saved','response_restore','response_saved','audit_fixture','audit_fixture02']) and p.name not in ['campaign.console','finalize.console'])
    files.append(report);archive=m.archive('phase-v934-20261109',files)
    (REC/'RECORD_INDEX.json').write_text(json.dumps(dict(repository='frank8763/phase-',release_tag='phase-rpccr-recovery-v934-20261109',archives=[{k:v for k,v in archive.items()if k!='files'}]),indent=2)+'\n')
    proof=dict(status='LOCAL_FINALIZED_REMOTE_PENDING',scientific_status=done['status'],all_sources_and_decompressed_sha_verified=True,models=0,integrations=0,at=time.time())
    (REC/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(proof,indent=2)+'\n');(O/'FINALIZED.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
