"""One zero-model closure; immutable exact-byte archive and explicit limits."""
import fcntl,gzip,hashlib,json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
root=repo/'runs/v797_retained_tail_mpc'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert(repo/'REVIEW_PENDING').exists()and not(root/'FINALIZED.json').exists()
assert read(root/'ROUND_WINDOW.json')['round_closed']
with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
source_ok=all(sha(repo/n)==h for n,h in read(own/'INPUT_FREEZE.json')['files'].items())
assert source_ok,'CLOSURE_SOURCE_CHANGED'
completion=read(root/'COMPLETION.json')
raw=read(root/'RESULT.json')if(root/'RESULT.json').exists()else None
audit=read(root/'SAVED_AUDIT.json')if(root/'SAVED_AUDIT.json').exists()else None
verified=bool(raw and audit and audit['status']=='ALL_RETAINED_MPC_SAVED_EVIDENCE_VERIFIED')
qualified=bool(verified and raw['component_qualified'])
status='FIXED_RETAINED_MPC_COMPONENT_QUALIFIED'if qualified else('FIXED_RETAINED_MPC_COMPONENT_NOT_PASSED'if verified else'CORRIDOR_EVIDENCE_NOT_VERIFIED')
final=dict(status=status,evidence_complete=verified,component_qualified=qualified,
    full_global_dynamic_passed=False,source_unchanged=source_ok,completion=completion,
    new_complete_navigation=0,new_confirmation=0,training_updates=0,real_robot=0,stage_access=0,
    model_initializations_finalizer=0,integrations_finalizer=0,raw_evidence_retained=True)
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(final,indent=2)+'\n')
report=repo/'docs/RPCCR_RETAINED_MPC_V797_REPORT.md';assert not report.exists()
lines=['# V797 保留完整安全尾的短周期走廊MPC', '',f'结论：**{status}**。完整场地动态仍未验收通过。', '',
    '用户在V796闭批后授权下一步。本轮唯一控制修订是每次只执行32原生再根据真实观测更新求解，完整328预测及剩296刹停尾保留。新证书合格才替换旧尾，拒绝时执行旧尾到结束；同CEM动作/路线评分/首10随机数组和全部安全门保持。路线来自原153步，早于原200检查点，不读actor真实未来。', '',
    '这是从同一已观察旧200状态开始的有限闭环分支，不是从起点的新独立全局导航。原V793失败及V795局部结论保持。', '',
    f'旧原生重放{completion["original_replay_native"]}；私有{completion["private_integrations"]}；新分支实际{completion["actual_validation_native"]}；分支完整重放{completion["branch_replay_native"]}；实际测距{completion["actual_packets"]}包（含重复）。', '']
if raw:
    lines += [f'停止原因：`{raw["stopped_reason"]}`；尝试{raw["attempted_replans"]}次，实际提交短前缀{raw["committed_replans"]}次。',
        f'最高原任务绝对目标进展：{raw["maximum_absolute_goal_progress_m"]}m；原最好{raw["old_best_absolute_progress_m"]}m；本分支原路线弧长累计{raw["reference_arc_progress_m"]}m。',
        f'实际车辆中心跨x=0：{raw["central_root_center_crossed"]}；实际首次发现：{raw["first_discovery"]}。中心跨线与全车通过是不同事件；无发现不当检测失败。',
        f'原生实际最低净空{raw["minimum_actual_clearance_m"]:.9f}m，坏接触{raw["bad_contacts"]}，原生预测/重放误差{raw["maximum_native_error"]}。', '',
        f'物理批总墙钟{raw["wall_s"]}秒，主分支仿真时间{raw["simulated_main_branch_s"]}秒；.32秒为仿真执行前缀，不是实时求解承诺，计算期间actor按模型时钟暂停。完整私有工作如上，不能宣称等总计算或实机延迟安全。', '',
        '![实际保存轨迹与原全局路线](../runs/v797_retained_tail_mpc/actual_retained_mpc.png)', '']
else:lines+=['批有异常/未完成RESULT，原ERROR/COMPLETION保持；未知项不写成物理PASS。','']
lines += ['所有实际前缀均有完整328证书；新求解期间旧尾不变，最后剩余旧尾全部完成。逐公开真实测距更新原因果域，并核验329执行/657规划覆盖。首192提案及前32原生与V796一致；完整主分支已原样回放。模型构造实际发生，精确构造器次数未单独计数；独立保存审核/本终审为零模型与零积分。', '',
    '本轮尚未实现发现后新的因果动态全局重规划、再续行>=1m、原目标到达和全新分母确认。因此局部过口或发现不能叫动态验收，也不证明CEM、主动感知或RP-CCR相对其他方法的独立优势。不得直接宣称RAS创新/录用。', '',
    '原始输入/候选/控制/观测/真实接触/失败/未执行条件项均保留。固定单候选/一次启动结束后不自动追加修订、新池、距离或训练。', '']
report.write_text('\n'.join(lines))
dest=repo/'evidence/rpccr_retained_mpc_v797_20261104';assert not dest.exists();dest.mkdir();(dest/'blobs').mkdir()
files=[p for directory in [own,root,repo/'runs/v797_preparation']for p in directory.rglob('*')if p.is_file()and'__pycache__'not in p.parts]
files += [report,repo/'RPCCR_RETAINED_MPC_AUTHORIZATION_20261104.json']
inventory=[]
for p in sorted(set(files)):
    data=p.read_bytes();h=hashlib.sha256(data).hexdigest();blob=dest/'blobs'/(h+'.gz');packed=gzip.compress(data,mtime=0)
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
summary=dict(source_files=len(inventory),raw_bytes=sum(r['bytes']for r in inventory),all_source_and_decompressed_readback_verified=True,raw_deleted=False)
(root/'FINALIZED.json').write_text(json.dumps(dict(**final,archive=str(dest.relative_to(repo)),archive_summary=summary),indent=2)+'\n')
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
p=repo/'RPCCR_RETAINED_MPC_LEDGER_20261104.json';ledger=read(p);ledger.update(status=status,closed_at=now,round_closed=True,actual=completion,component_qualified=qualified,full_global_dynamic_passed=False,no_more_physics_this_round=True);p.write_text(json.dumps(ledger,indent=2)+'\n')
p=repo/'CURRENT_EXPERIMENT.json';current=read(p);current.update(status='REVIEW_PENDING_V797_'+status,active_entrypoint=None,active_run=None,active_window=None,active_automation=None,execution_window_closed=True,report=str(report.relative_to(repo)),retained_mpc_closure=dict(status=status,closed_at=now,component_qualified=qualified,actual=completion,full_global_dynamic_passed=False));p.write_text(json.dumps(current,indent=2)+'\n')
print(json.dumps(dict(**final,archive_summary=summary)))
