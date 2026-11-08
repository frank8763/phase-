"""Bounded zero-model source/decompressed SHA closure; never overwrites an archive."""
import fcntl,hashlib,importlib.util,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v886_dynamic_development';REC=R/'records/nav2_v886_20261108'
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
    report=R/'docs/NAV2_DYNAMIC_V886_REPORT.md';lines=['# V886单actor动态开发',f"\n状态：{completion['status']}。原三路线静态通过，控制/配置精确V884；本轮继承2026-11-08 20:21:10.401绝对截止，不重置旧窗。",f"\n动态导航尝试{completion['attempted_navigation']}，条件导航未执行{completion['unexecuted_navigation']}；新24/比较/消融/训练/实机均未执行。",'\n|任务|通过|实际原生|自身重放|末距目标m|','|---|---|---|---|---|']
    for row in completion['rows']:lines.append(f"|{row['task_id']}|{row['passed']}|{row.get('actual_native')}|{row.get('replay_native')}|{row.get('goal_m')}|")
    for row in audits:
        a=row['audit'];lines.append('\n'+row['task_id']+' 独立审核：'+json.dumps({k:a.get(k)for k in ['evidence_passed','functional_passed','discovery','independently_recomputed_postdiscovery_travel_m','minimum_clearance_m','bad_contacts','maximum_state_error','reference_updates_after_detection','successful_routes_after_detection','original_dynamic_actor_configuration','independent_recorded_actor_motion']},ensure_ascii=False))
    lines+=['\nNone表示未知/未完成，不填0。t0环境初始化/内部编译加载与导航/自身重放分账，私有预测0。', '\n真实原量程发现后实际续行>=1m、之后有周期参考更新、ROS成功/目标<=.45并实际停稳<=.03，以及全部原生.15/自体/合法ctrl/静态固定/自身状态接触重放和原100ms/200ms/250ms门均必须。周期更新不冒称由发现事件触发。', '\n本轮是单小actor有限Nav2动态开发，不是新24确认、原RP-CCR328安全合同或RAS创新/算法优势证明。原观测里程计直接来自仿真真实状态，实机估计尚未接入。异步完整重复不要求两轨迹逐位相同，但每次自身完整控制重放须<=1e-8。', '\n闭批REVIEW_PENDING原字节恢复/锁空闲；必要原件远端大小digest/下载SHA/实际成员恢复核验后才清缓存，旧同步不重试，2GiB临时上限。']
    report.write_text('\n'.join(lines)+'\n')
    spec=importlib.util.spec_from_file_location('v886_archive',R/'experiments/v856_nav2_closure/package_records.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=O/'cloud';m.OUT.mkdir(exist_ok=True)
    files=[]
    for base in [C,O,R/'runs/v858_nav2_verified/v886',REC]:
        if base.exists():files += [p for p in m.walk(base)if not any(s in p.relative_to(base).parts for s in ['cloud','__pycache__'])and p.name not in ['finalize.console','validation.console']]
    files.append(report);archive=m.archive('v886-runtime-evidence',files)
    index=dict(repository='frank8763/phase-',release_tag='phase-nav2-v886-20261108',status='LOCAL_SOURCE_DECOMPRESSION_PART_SHA_VERIFIED_REMOTE_PENDING',archives=[{k:v for k,v in archive.items()if k!='files'}])
    dump(REC/'RECORD_INDEX.json',index);dump(O/'cloud/RECORD_INDEX.json',index)
    dump(O/'FINALIZED.json',dict(status='LOCAL_FINALIZED_REMOTE_PENDING',source_and_decompressed_sha_verified=True,part_reassembly_sha_verified=True,scientific_status=completion['status'],raw_deleted=False,remote_verified=False,models_this_finalize=0,integrations_this_finalize=0,at=time.time()))
if __name__=='__main__':main()
