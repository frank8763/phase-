"""Idempotence-protected zero-model accounting and local archive closure."""
import fcntl,importlib.util,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v929_executable_mppi';REC=R/'records/nav2_v929_20261109'
sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from handshake import verify_sources
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not(O/'FINALIZED.json').exists(),'ALREADY_FINALIZED'
    done=json.loads((O/'COMPLETION.json').read_text());assert done['closed'];verify_sources(R,C/'SOURCE_FREEZE.json')
    assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes()
    REC.mkdir(exist_ok=True)
    for name in ['COMPLETION.json','RESULTS.json','AUTHORIZATION.json','ROUND_WINDOW.json','ZERO_MODEL_QUALIFICATION.json','PROJECTION_QUALIFICATION.json','FULL_STARTUP_QUALIFICATION.json','CONTROLLER_SOFTWARE_QUALIFICATION.json','BUILD_RESULT.json','PREPARATION_ERRORS.json','PLATFORM_RESULT.json','REPEAT.json']:
        if(O/name).exists():(REC/name).write_bytes((O/name).read_bytes())
    platform=json.loads((O/'PLATFORM_RESULT.json').read_text())if(O/'PLATFORM_RESULT.json').exists()else{}
    total=lambda key:None if any(x.get(key)is None for x in done['rows'])else sum(x[key]for x in done['rows'])
    summary=dict(status=done['status'],platform_actual_native=platform.get('actual_native'),platform_own_replay_native=platform.get('replay_native'),
                 navigation_actual_native=total('actual_native'),navigation_own_replay_native=total('replay_native'),navigation_private_native=total('private_native'),
                 platform_passed=platform.get('passed',False),attempted_navigation=len(done['rows']),unexecuted_navigation=done['unexecuted_navigation'],new24=0,training=0,hardware=0,
                 deadline_unix=done['deadline_unix'],remote_pending=True,closed_reason=done['error'])
    (REC/'RESULT_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    report=R/'docs/EXECUTABLE_MPPI_V929_REPORT.md'
    report.write_text('# V929 可执行采样 MPPI 开发\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\n本轮为成熟导航基线适配：MPPI候选在评分前统一挡位、曲率与实际速度限值，实测速度初始化，最终完整车身轨迹碰撞核验；静态主与重复先通过，才条件动态主与重复。原19实体、车辆、传感、目标与逐原生.15米/控制速率/接触/全状态重放门保持。未部署原RP-CCR不确定性和全周期停车证明，不称新24动态验收或论文创新。异步重复逐条完整到达和自身重放，未要求不同导航逐状态相同。V928拒绝的ARX拟合未部署；零车辆启动缺诊断消息链接库的准备失败保留。\n')
    spec=importlib.util.spec_from_file_location('v929_archive',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    from types import SimpleNamespace
    import tarfile
    def expanded_open(*args,**kw):
        if str(kw.get('mode','')).startswith('w'):kw['dereference']=True
        return tarfile.open(*args,**kw)
    m.tarfile=SimpleNamespace(open=expanded_open)
    m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=False)
    files=[]
    for base in [C,R/'runs/v858_nav2_verified/v929',REC]:files.extend(m.walk(base))
    files.extend(p for p in m.walk(O)if not any(x in p.relative_to(O).parts for x in ['cloud','restore','saved','response_restore','response_saved','audit_fixture','audit_fixture02','headers','debs']) and p.name not in ['campaign.console','finalize.console'])
    files.append(report);archive=m.archive('phase-v929-20261109',files)
    (REC/'RECORD_INDEX.json').write_text(json.dumps(dict(repository='frank8763/phase-',release_tag='phase-timed-command-v929-20261109',archives=[{k:v for k,v in archive.items()if k!='files'}]),indent=2)+'\n')
    proof=dict(status='LOCAL_FINALIZED_REMOTE_PENDING',scientific_status=done['status'],all_sources_and_decompressed_sha_verified=True,models=0,integrations=0,at=time.time())
    (REC/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(proof,indent=2)+'\n');(O/'FINALIZED.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
