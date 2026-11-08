"""Offline bounded archive and accurate accounting; no cloud or model dependency."""
import fcntl,hashlib,importlib.util,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v896_overnight_20261108';REC=R/'records/nav2_overnight_20261108'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from handshake import verify_sources
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=json.loads((O/'COMPLETION.json').read_text());assert d['closed'];verify_sources(R,C/'SOURCE_FREEZE.json');assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes();REC.mkdir(exist_ok=True)
    for name in ['COMPLETION.json','RESULTS.json','PREFLIGHTS.json','AUTHORIZATION.json','ROUND_WINDOW.json','PLATFORM_ENTRY_ERROR.json','ENTRY_CONTINUATION_APPROVAL.json','platform_continuation_result.json']:
        if(O/name).exists():(REC/name).write_bytes((O/name).read_bytes())
    rows=d['rows'];total=lambda key:None if any(x.get(key)is None for x in rows)else sum(x[key]for x in rows)
    summary=dict(status=d['status'],rows=rows,actual_navigation_native=total('actual_native'),own_navigation_replay_native=total('replay_native'),private_native=total('private_native'),platform_actual_native=1200,platform_replay_native=1200,original_platform_factory_steps='NOT_SEPARATELY_INSTRUMENTED_UNKNOWN',new24=0,training=0,real_robot=0,deadline_unix=1794182400.,models_this_finalize=0,integrations_this_finalize=0,remote_upload_pending=True,raw_cache_preserved_until_remote_verified=True)
    (REC/'RESULT_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    report=R/'docs/NAV2_REFUGE_OVERNIGHT_20261108_REPORT.md';report.write_text('# 2026-11-08有限夜间动态开发\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n原V894及全部旧失败保持。0新24，不是独立确认或RAS/递归安全保证。原V896输出入口失败保持，V898仅一次用户批准输出接续；导航新候选无冻结后修补或重启。原08:00不延期。断网不丢原件或重试云同步，2GiB有界缓存，联网后远端逐SHA和恢复核验才清。\n')
    spec=importlib.util.spec_from_file_location('night_archive',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=True);assert not list(m.OUT.iterdir()),'EXISTING_ARCHIVE_NO_OVERWRITE'
    files=[]
    for base in [C,R/'experiments/v896_overnight_platform',R/'experiments/v898_platform_output_continuation',R/'experiments/v899_refuge_qualification',R/'runs/v858_nav2_verified/v897',R/'runs/v858_nav2_verified/v898_platform',R/'runs/v899_refuge_qualification',REC]:files.extend(m.walk(base))
    files.extend([p for p in m.walk(O)if 'cloud'not in p.relative_to(O).parts and p.name not in ['night.console','watchdog.console','finalize.console']]);files.append(report)
    archive=m.archive('phase-night-20261108',files);index=dict(repository='frank8763/phase-',release_tag='phase-refuge-night-20261108',archives=[{k:v for k,v in archive.items()if k!='files'}],status='OFFLINE_LOCAL_VERIFIED_REMOTE_PENDING');(REC/'RECORD_INDEX.json').write_text(json.dumps(index,indent=2)+'\n')
    proof=dict(status='LOCAL_FINALIZED_REMOTE_PENDING',source_verified=True,all_archive_source_and_decompressed_sha_verified=True,scientific_status=d['status'],models=0,integrations=0,at=time.time());(O/'FINALIZED.json').write_text(json.dumps(proof,indent=2)+'\n');(REC/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof),flush=True)
if __name__=='__main__':main()
