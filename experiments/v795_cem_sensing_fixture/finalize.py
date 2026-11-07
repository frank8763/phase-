"""Close once, archive exact bytes, never construct or integrate a model."""
import fcntl,gzip,hashlib,json,time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
root=repo/'runs/v795_cem_sensing_fixture'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert (repo/'REVIEW_PENDING').exists() and not(root/'FINALIZED.json').exists()
assert read(root/'ROUND_WINDOW.json')['round_closed']
with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
source_ok=all(sha(repo/n)==h for n,h in read(own/'INPUT_FREEZE.json')['files'].items())
assert source_ok,'SOURCE_CHANGED_AT_CLOSURE'
completion=read(root/'COMPLETION.json')
raw=read(root/'RESULT.json')if(root/'RESULT.json').exists()else None
audit=read(root/'SAVED_AUDIT.json')if(root/'SAVED_AUDIT.json').exists()else None
verified=bool(raw and audit and audit['status']=='ALL_FIXED_CEM_SENSING_SAVED_EVIDENCE_VERIFIED')
qualified=bool(verified and raw['component_qualified'])
status='FIXED_STATE_CEM_SENSING_COMPONENT_QUALIFIED'if qualified else(
    'FIXED_STATE_CEM_SENSING_COMPONENT_NOT_QUALIFIED'if verified else'COMPONENT_NOT_VERIFIED')
final=dict(status=status,evidence_complete=verified,component_qualified=qualified,
    full_global_dynamic_passed=False,source_unchanged=source_ok,completion=completion,
    new_navigation=0,new_confirmation=0,training_updates=0,stage_access=0,real_robot=0,
    new_integrations_finalizer=0,raw_evidence_retained=True)
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(final,indent=2)+'\n')
report=repo/'docs/RPCCR_CEM_SENSING_V795_REPORT.md'
lines=['# V795 固定状态CEM组合控制/实际感知资格', '',
    f'实际结论：**{status}**。完整场地动态仍未验收通过。本轮完整导航0、新确认0。', '',
    '新方法只将有限CEM组合控制提案与RP-CCR原生完整安全证书结合；预测可见性只影响效用，不能成为测量。原V793及所有旧失败和截止保留。', '',
    f'原旧状态重放 {completion["original_replay_native"]} 原生；私有预测 {completion["private_integrations"]}；实际分支验证 {completion["actual_validation_native"]}；分支完整重放 {completion["branch_replay_native"]}；实际测距 {completion["actual_packets"]} 包。', '']
if raw:
    lines+=['|旧状态|第一段实际执行|第一段所选预测净进展m|第二段所选预测净进展m|真实感知净空提升m|组件资格|',
            '|---|---|---|---|---|---|']
    for r in raw['records']:
        a=r['selected'];b=r['forward_continuation']
        lines.append('|{}|{}|{}|{}|{}|{}|'.format(r['step'],r['actual_executed'],
            None if a is None else round(a['progress_m'],6),None if b is None else round(b['progress_m'],6),
            r.get('renewed_minus_aged_clearance_m'),r['component_qualified']))
    lines+=['',f'实际原生最低净空 {raw["minimum_actual_clearance_m"]:.9f}m，坏接触 {raw["bad_contacts"]}，原生模型/旧重放最大误差 {raw["maximum_native_error"]}。',
        '只有实际执行并完整重放的预测进展才是已验证实际进展；未执行的优化预测不冒称实际成功。']
else:lines+=['原始批有异常或未形成完整RESULT，详见保留ERROR与COMPLETION；不以无新碰撞或未执行项推断物理通过。']
lines+=['','这只是两个已观察早期状态的有限组件资格，不是从起点完整链、不包含动态actor发现后的全局验收、不证明CEM或主动感知机制优越。没有合格组件时不启动依赖全场导航。', '',
    '协议：`experiments/v795_cem_sensing_fixture/PROTOCOL.md`；独立保存审核：`runs/v795_cem_sensing_fixture/SAVED_AUDIT.json`。原始分母、失败与未执行条件项完整保留。', '',
    '方法参考：[iCEM](https://martius-lab.github.io/iCEM/)、[IT-MPC](https://arxiv.org/abs/1707.02342)、[PA-MPPI v2](https://arxiv.org/html/2509.14978v2)。仅借鉴有限优化/感知效用，不借用其他模型的安全定理或性能。','']
assert not report.exists();report.write_text('\n'.join(lines))
dest=repo/'evidence/rpccr_cem_sensing_v795_20261104'
assert not dest.exists();dest.mkdir();(dest/'blobs').mkdir()
files=[p for directory in [own,root] for p in directory.rglob('*')if p.is_file()and'__pycache__'not in p.parts]
files += [report,repo/'RPCCR_CEM_SENSING_FIXTURE_AUTHORIZATION_20261104.json']
inventory=[]
for p in sorted(set(files)):
    data=p.read_bytes();h=hashlib.sha256(data).hexdigest();blob=dest/'blobs'/(h+'.gz')
    packed=gzip.compress(data,mtime=0)
    if blob.exists():assert blob.read_bytes()==packed
    else:blob.write_bytes(packed)
    inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(data),sha256=h,blob=str(blob.relative_to(dest))))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
for r in inventory:
    data=gzip.decompress((dest/r['blob']).read_bytes())
    assert len(data)==r['bytes']and hashlib.sha256(data).hexdigest()==r['sha256']and sha(repo/r['path'])==r['sha256']
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(dest.rglob('*'))if p.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
assert all(sha(dest/r['path'])==r['sha256']for r in manifest)
summary=dict(source_files=len(inventory),raw_bytes=sum(r['bytes']for r in inventory),
             all_source_and_decompressed_readback_verified=True,raw_deleted=False)
(root/'FINALIZED.json').write_text(json.dumps(dict(**final,archive=str(dest.relative_to(repo)),archive_summary=summary),indent=2)+'\n')
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
ledger=read(repo/'RPCCR_CEM_SENSING_FIXTURE_LEDGER_20261104.json')
ledger.update(status=status,closed_at=now,round_closed=True,result=str((root/'FINALIZED.json').relative_to(repo)),
              actual=completion,component_qualified=qualified,new_navigation=0,new_confirmation=0)
(repo/'RPCCR_CEM_SENSING_FIXTURE_LEDGER_20261104.json').write_text(json.dumps(ledger,indent=2)+'\n')
current=read(repo/'CURRENT_EXPERIMENT.json')
current.update(status='REVIEW_PENDING_V795_'+status,active_entrypoint=None,active_run=None,active_window=None,
    active_automation=None,execution_window_closed=True,report=str(report.relative_to(repo)),
    cem_sensing_closure=dict(status=status,closed_at=now,component_qualified=qualified,actual=completion,
                             full_global_dynamic_passed=False))
(repo/'CURRENT_EXPERIMENT.json').write_text(json.dumps(current,indent=2)+'\n')
print(json.dumps(dict(**final,archive_summary=summary)))
