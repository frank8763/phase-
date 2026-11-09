"""Offline bounded archive and accurate accounting; no cloud or model dependency."""
import fcntl,hashlib,importlib.util,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v900_refuge_terminal_set';REC=R/'records/nav2_v900_20261109'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from handshake import verify_sources
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    d=json.loads((O/'COMPLETION.json').read_text());assert d['closed'];verify_sources(R,C/'SOURCE_FREEZE.json');assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes();REC.mkdir(exist_ok=True)
    for name in ['COMPLETION.json','RESULTS.json','PREFLIGHTS.json','AUTHORIZATION.json','ROUND_WINDOW.json','PLATFORM_ENTRY_ERROR.json','ENTRY_CONTINUATION_APPROVAL.json','platform_continuation_result.json']:
        if(O/name).exists():(REC/name).write_bytes((O/name).read_bytes())
    rows=d['rows'];total=lambda key:None if any(x.get(key)is None for x in rows)else sum(x[key]for x in rows)
    summary=dict(status=d['status'],rows=rows,actual_navigation_native=total('actual_native'),own_navigation_replay_native=total('replay_native'),private_native=total('private_native'),platform_actual_native=0,platform_replay_native=0,historical_platform='V898 reused evidence only; old V896 initialization accounting remains unknown',new24=0,training=0,real_robot=0,deadline_unix=d['deadline_unix'],models_this_finalize=0,integrations_this_finalize=0,remote_upload_pending=True,raw_cache_preserved_until_remote_verified=True)
    (REC/'RESULT_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    report=R/'docs/NAV2_REFUGE_TERMINAL_SET_V900_REPORT.md';report.write_text('# V900 因果退让终端区域开发结果\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\n原V897及全部旧失败保持。只计本轮导航，不是24项独立确认；内部退让改为实际后退、原因果驻留准入、取消后实际刹停再恢复。原目标.45/原生净空.15和全部物理门不变。新独立90分钟，不延长任何旧窗。完整证据远端SHA和下载恢复通过后才清理。\n')
    spec=importlib.util.spec_from_file_location('night_archive',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=True);assert not list(m.OUT.iterdir()),'EXISTING_ARCHIVE_NO_OVERWRITE'
    files=[]
    for base in [C,R/'runs/v858_nav2_verified/v900',REC]:files.extend(m.walk(base))
    files.extend([p for p in m.walk(O)if 'cloud'not in p.relative_to(O).parts and p.name not in ['night.console','watchdog.console','finalize.console']]);files.append(report)
    archive=m.archive('phase-v900-20261109',files);index=dict(repository='frank8763/phase-',release_tag='phase-refuge-terminal-v900-20261109',archives=[{k:v for k,v in archive.items()if k!='files'}],status='OFFLINE_LOCAL_VERIFIED_REMOTE_PENDING');(REC/'RECORD_INDEX.json').write_text(json.dumps(index,indent=2)+'\n')
    proof=dict(status='LOCAL_FINALIZED_REMOTE_PENDING',source_verified=True,all_archive_source_and_decompressed_sha_verified=True,scientific_status=d['status'],models=0,integrations=0,at=time.time());(O/'FINALIZED.json').write_text(json.dumps(proof,indent=2)+'\n');(REC/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof),flush=True)
if __name__=='__main__':main()
