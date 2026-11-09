"""Separate supplemental closure; never overwrite the original V909 archive."""
import fcntl,hashlib,importlib.util,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v909_output_continuation';OLD=R/'runs/v909_timed_command_contract';REC=R/'records/nav2_v909_20261109'
sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from handshake import verify_sources
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    done=json.loads((O/'COMPLETION.json').read_text());assert done['closed'];assert not(O/'FINALIZED.json').exists()
    verify_sources(R,C/'SOURCE_FREEZE.json');assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes()
    REC.mkdir(exist_ok=True)
    for p in O.glob('*.json'):
        if p.name not in ['WORKER.json','ACTIVE.json']:(REC/('CONTINUATION_'+p.name)).write_bytes(p.read_bytes())
    total=lambda key:None if any(x.get(key)is None for x in done['rows'])else sum(x[key]for x in done['rows'])
    summary=dict(status=done['status'],original_operational_failure_preserved=True,original_case00_actual_native=420,original_case00_own_replay_native=420,
                 platform_total_actual_native_including_original=done['platform_total_actual_native'],platform_total_own_replay_including_original=done['platform_total_replay_native'],
                 platform_unexecuted=done['remaining_platform_unexecuted'],navigation_actual_native=total('actual_native'),navigation_own_replay_native=total('replay_native'),navigation_private_native=total('private_native'),
                 navigation_attempted=len(done['rows']),navigation_unexecuted=done['unexecuted_navigation'],new24=0,training=0,hardware=0,deadline_unix=done['deadline_unix'],stopping_reason=done['error'],remote_pending=True)
    (REC/'CONTINUATION_RESULT_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    report=R/'docs/NAV2_TIMED_COMMAND_V909_CONTINUATION_REPORT.md'
    report.write_text('# V909 有限执行与刹停资格：一次输出入口接续\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\n原V909因工厂写入根限制而闭批NOT_PASSED不改。其首组实际420步及完整自重放420步保留并复用，本接续只绑定同一冻结程序的操作输出根，不重复已执行工况、没有改科学阈值；继承原2026-11-09 12:07:58.802325绝对截止。平台经验界不是形式化动力学保证；一条路线开发和重复也不等于24项确认。任何新失败后不再接续。远端下载与SHA回读前不清理必须证据。\n')
    spec=importlib.util.spec_from_file_location('v909_supplement_archive',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=False)
    files=[]
    for base in [C,REC,R/'runs/v858_nav2_verified/v909']:files.extend(m.walk(base))
    files.extend(p for p in m.walk(O)if 'cloud'not in p.relative_to(O).parts and p.name not in ['campaign.console','finalize.console'])
    files.extend([report,OLD/'ACCOUNTING_RECONCILIATION.json',OLD/'campaign.console',OLD/'finalize.console'])
    group=m.archive('phase-v909-continuation-20261109',files)
    original=json.loads((REC/'RECORD_INDEX.json').read_text())
    combined=dict(repository='frank8763/phase-',release_tag='phase-timed-command-v909-20261109',archives=[*[dict(g,local_cloud=str((OLD/'cloud').relative_to(R)))for g in original['archives']],dict({k:v for k,v in group.items()if k!='files'},local_cloud=str(m.OUT.relative_to(R)))])
    (REC/'COMBINED_RECORD_INDEX.json').write_text(json.dumps(combined,indent=2)+'\n')
    proof=dict(status='LOCAL_FINALIZED_REMOTE_PENDING',scientific_status=done['status'],all_sources_and_decompressed_sha_verified=True,original_archive_preserved=True,models=0,integrations=0,at=time.time())
    (O/'FINALIZED.json').write_text(json.dumps(proof,indent=2)+'\n');(REC/'CONTINUATION_FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
