"""Bounded zero-model source/decompressed SHA closure; never overwrites an archive."""
import fcntl,hashlib,importlib.util,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v885_remaining_static_routes';REC=R/'records/nav2_v885_20261108'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from handshake import verify_sources
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    completion=json.loads((O/'COMPLETION.json').read_text());assert completion['closed'];verify_sources(R,C/'SOURCE_FREEZE.json')
    assert hashlib.sha256((R/'REVIEW_PENDING').read_bytes()).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    if (O/'FINALIZED.json').exists():raise RuntimeError('ALREADY_FINALIZED_NO_OVERWRITE')
    if (O/'cloud').exists()and any((O/'cloud').iterdir()):raise RuntimeError('EXISTING_ARCHIVE_DIAGNOSE_READ_ONLY')
    from audit import audit
    audits=[]
    for row in completion['rows']:
        out=Path(row['output']);task=json.loads((out/'TASK.json').read_text());old=json.loads((out/'INDEPENDENT_AUDIT.json').read_text())if(out/'INDEPENDENT_AUDIT.json').exists()else None
        checked=audit(task)
        if old is not None:assert old==checked,'AUDIT_READBACK_CHANGED'
        audits.append(dict(task_id=row['task_id'],audit=checked))
    final_audit=dict(passed=True,scope='Closed source/record consistency only; navigation result separate',scientific_status=completion['status'],rows=audits,models=0,integrations=0,source_sha_verified=True,guard_restored=True,lock_idle=True)
    dump(O/'FINAL_INDEPENDENT_AUDIT.json',final_audit);dump(REC/'FINAL_INDEPENDENT_AUDIT.json',final_audit);dump(REC/'COMPLETION.json',completion)
    report=R/'docs/NAV2_RUNTIME_V885_REPORT.md';lines=['# V885同版本剩余静态路线回归',f"\n状态：{completion['status']}。本轮与旧17:00窗口独立，旧V881时序失败及未知重放计数保持。",f"\n导航尝试{completion['attempted_navigation']}，未执行{completion['unexecuted_navigation']}；动态、新24、比较、消融、训练、实机均未执行。",'\n|任务|通过|实际原生|自身重放|末距目标m|','|---|---|---|---|---|']
    for row in completion['rows']:lines.append(f"|{row['task_id']}|{row['passed']}|{row.get('actual_native')}|{row.get('replay_native')}|{row.get('goal_m')}|")
    lines+=['\nNone代表未知/未完成，不推断为0。原100ms门及物理/控制/重放门不降低。前缀保存合格不等于导航通过，循环GC暂缓不证明旧因果或实时性。', '\n同版本完整异步ROS重复各自要求安全到达及自身重放；不声称两次导航逐位相同。剩余两条静态回归不是动态验收或RP-CCR创新证明。', '\n本地完整来源SHA/解压SHA归档后，必要证据仍须联网上传及下载回读才允许清理。远端未核验原件不删，不重试旧批上传。']
    report.write_text('\n'.join(lines)+'\n')
    spec=importlib.util.spec_from_file_location('v885_archive',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=True)
    files=[]
    for base in [C,O,R/'runs/v858_nav2_verified/v885',REC]:
        if base.exists():files += [p for p in m.walk(base)if not any(s in p.relative_to(base).parts for s in ['cloud','__pycache__'])and p.name not in ['finalize.console','validation.console']]
    files.append(report);archive=m.archive('v885-runtime-evidence',files)
    index=dict(repository='frank8763/phase-',release_tag='phase-nav2-v885-20261108',status='LOCAL_SOURCE_DECOMPRESSION_PART_SHA_VERIFIED_REMOTE_PENDING',archives=[{k:v for k,v in archive.items()if k!='files'}])
    dump(REC/'RECORD_INDEX.json',index);dump(O/'cloud/RECORD_INDEX.json',index)
    dump(O/'FINALIZED.json',dict(status='LOCAL_FINALIZED_REMOTE_PENDING',source_and_decompressed_sha_verified=True,part_reassembly_sha_verified=True,scientific_status=completion['status'],raw_deleted=False,remote_verified=False,models_this_finalize=0,integrations_this_finalize=0,at=time.time()))
if __name__=='__main__':main()
