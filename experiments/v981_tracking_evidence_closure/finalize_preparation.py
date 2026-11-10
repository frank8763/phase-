"""Close source-only repair and freeze its actual files; never launch models."""
import ast
import fcntl
import hashlib
import json
from pathlib import Path
import time

C = Path(__file__).parent
R = C.resolve().parents[1]
O = R/'runs/v981_tracking_evidence_closure'
REC = R/'records/nav2_v981_20261110'
GUARD = '4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')


def main():
    lock = (R/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING') == GUARD
    REC.mkdir(exist_ok=False)
    baseline = json.loads((O/'BASELINE_RED.json').read_text())
    assert baseline['passed'] is False and baseline['original_group_stop_loses_child_evidence']
    names=['TRACKING_QUALIFICATION.json','CLOSURE_QUALIFICATION.json','NATIVE_LOOP_QUALIFICATION.json','ENTRY_QUALIFICATION.json']
    inputs={name:json.loads((O/name).read_text()) for name in names}
    assert all(row['passed'] and row['models']==0 for row in inputs.values())
    for name in ['BASELINE_RED.json',*names]:
        (REC/name).write_bytes((O/name).read_bytes())
    authority=dict(scope='V981_SOURCE_AND_ZERO_MODEL_ONLY',models_authorized=False,
                   user_instruction='继续',prior_physical_window='V979_CLOSED_FIRST_FAILURE_NOT_REOPENED',
                   automatic_navigation=False,automatic_overnight=False,training=0,hardware=0)
    dump(REC/'AUTHORIZATION.json',authority)
    manifest={}
    for old in ['v977_state_consistent_recovery','v979_state_recovery_physical']:
        frozen=R/'experiments'/old/'SOURCE_FREEZE.json'
        manifest[str(frozen.relative_to(R))]=sha(frozen)
        for name,digest in json.loads(frozen.read_text())['files'].items():
            if (R/name).is_file():
                assert sha(R/name)==digest,name
                manifest[name]=digest
    for p in C.iterdir():
        if p.suffix in {'.py','.md'}:
            if p.suffix=='.py':ast.parse(p.read_text())
            manifest[str(p.relative_to(R))]=sha(p)
    dump(C/'SOURCE_FREEZE.json',dict(final=True,scope=authority['scope'],model_authority=False,
         models_before_freeze=0,integrations_before_freeze=0,frozen_unix=time.time(),files=manifest))
    final=dict(closed=True,status='SOURCE_AND_ZERO_MODEL_QUALIFIED_ONLY',passed=True,
               models=0,actual_native=0,private_native=0,replay_native=0,new_navigation_samples=0,
               synthetic_loop_counters_are_not_physics=True,
               original_red_bugs_reproduced=2,qualification_groups=len(inputs),
               tracking_checks=len(inputs['TRACKING_QUALIFICATION.json']['checks']),
               tracking_negative_cases=len(inputs['TRACKING_QUALIFICATION.json']['negatives']),
               owned_process_failure_cases=len(inputs['CLOSURE_QUALIFICATION.json']['cases']),
               actual_native_loop_counter_fixture_cases=len(inputs['NATIVE_LOOP_QUALIFICATION.json']['cases']),
               saved_fault_heading_upper_rad=inputs['TRACKING_QUALIFICATION.json']['saved_fault']['heading_upper_rad'],
               unchanged_heading_limit_rad=.035,unchanged_position_limit_m=.04,
               source_freeze_sha256=sha(C/'SOURCE_FREEZE.json'),frozen_files=len(manifest),
               original_guard_sha256=GUARD,execution_lock_idle_at_closure=True,
               old_v979_status_unchanged='NOT_PASSED',physical_ready=False,models_authorized=False,
               remaining_gate='Actual steering/body transient in the two fixed saved recovery states; bind online and independent audits in one separately authorized physical batch before any full route.',
               report='docs/RPCCR_TRACKING_EVIDENCE_REPAIR_V981_REPORT.md')
    dump(REC/'FINAL_ZERO_MODEL_AUDIT.json',final)
    dump(REC/'COMPLETION.json',final)
    report=f'''# V981 跟踪判定与失败收尾修复

2026-11-10，本轮只完成源码和零模型资格。**动态验收尚未通过，V979 保持 NOT_PASSED；没有新模型、物理积分、导航、私有预测、重放、训练或实机任务。**

旧版真实 `TrackingGuard` 在 V979 原故障位置稳定报航向超界；旧版真实进程组终止函数对带父死退出语义的子进程，会使其来不及写收尾文件。两个原失败反馈均保留在 `BASELINE_RED.json`。

## 修复和证据

- 原发送参考、转向/速度控制、.04 m 位置门和 .035 rad 航向门保持。在线守卫从 12.5 mm 参考点采样改为同一分析曲线的固定 .5 mm 采样，并保留半格曲率界及额外数值余量。原故障点新航向上界 {final['saved_fault_heading_upper_rad']:.9f} rad，独立中点法为 .031638789 rad；26 个可用保存姿态通过，真实越界、非有限输入、参考/证书篡改仍拒绝。不是通过修改实际轨迹或放宽门限使旧批翻案。
- 同一故障曲线 2201 个密点相对独立方法的位置最大差约 .000000684 m、航向 .000000638 rad，小于明确保留的 1e-5 数值余量。两固定保存状态的原参考均通过本次在线/独立资格。该结果只覆盖这些固定输入，不是任意地图或自交路径的连续跟踪定理。
- 父进程首次失败即标记失败并请求 STOP；在原任务/根截止内，给予最多 40 秒收尾余量，不立即杀死原生隔离外壳。卡死时仍有界升级终止，不重启导航或延长物理授权。正常 STOP 仍走原 2 秒停稳流程，硬安全/计时异常后不追加实际轨迹积分。
- 原生循环在完整轨迹写盘及自身重放前先原子写出并 fsync 计数回执。历史重建、新分支、完整自身重放分开记账；积分调用中断或记录计数不一致时保留未知，重放中断也不填零。父 STOP 不能被重新评为导航通过。
- 四种真实自有父/子进程注入通过：ROS 失败、父异常、子进程卡死、根截止。实际修改后的原生循环在五种明确非物理计数夹具通过：ROS 失败、ARM 前停止、写盘失败、重放中断、原生调用中断。夹具中的 6083 等计数是软件造数，用来检查分账逻辑，绝不计入物理实验账。

## 尚未解决的物理风险

V979 保存证据仍显示正转向修正指令下实际车体偏航短时为负。此次修复不能证明该滞后随后不会越过原 .035 rad 门，也不能证明恢复段或整路可完成。下一物理关应先验证原两固定恢复状态的完整转向瞬态，独立核验全原生轨迹与停车、命令和接触；全部通过后才讨论原西向东主任务/重复。不能直接跳到三路线、新 24 项或算法对照。

新原生入口及直接循环入口均实际验证拒绝模型授权。新 launcher 明确不能评定尚未绑定的新物理终审为 PASS。下一物理批必须事前绑定新版在线与独立密采样审核、原模型/传感/控制/安全门和新的有界授权；旧 V979 窗口不重开。

V977 原 1477 文件全部 SHA 未变；V979 1543 个本地可用冻结文件未变，13 个事先已远端核验清理的旧输入没有重下或伪造。源码冻结为 {len(manifest)} 文件；REVIEW_PENDING 原字节恢复、执行锁空闲。存储沿用仓库 Release 下载/逐成员 SHA 回读后才清理；本轮仅一次新的有界 Git 同步，旧批同步不重试。

复核结果见 `records/nav2_v981_20261110/FINAL_ZERO_MODEL_AUDIT.json`。Release 目标： https://github.com/frank8763/phase-/releases/tag/phase-rpccr-tracking-evidence-v981-20261110 。
'''
    (R/'docs/RPCCR_TRACKING_EVIDENCE_REPAIR_V981_REPORT.md').write_text(report)
    state=json.loads((R/'CURRENT_EXPERIMENT.json').read_text())
    state.update(status='REVIEW_PENDING',source_revision='V981_SOURCE_ONLY_QUALIFIED',active_entrypoint=None,
                 active_run=None,active_window=None,execution_window_closed=True,
                 decision_freeze='experiments/v981_tracking_evidence_closure/SOURCE_FREEZE.json',
                 protocol='experiments/v981_tracking_evidence_closure/PROTOCOL.md',report=final['report'],
                 next_physical_authorized=False)
    state['v981_source_repair']=final
    dump(R/'CURRENT_EXPERIMENT.json',state)
    with(R/'RESEARCH_STATUS.md').open('a')as stream:
        stream.write('\n- V981仅源码与零模型修复：旧保存航向拒绝和父组终止丢记录两红例真实复现；同原参考.5mm守卫/独立审核令故障位置上界.031639<原.035，26保存姿态及真实越界/篡改负例通过，原.04/.035/控制路径不降不改。4真实父子进程和5实际原生循环非物理计数故障夹具全过；失败STOP有界收尾/原子计数先落盘/未知不填0，不重启或延截止。V979仍NOT_PASSED，实际偏航滞后未获得物理通过；本轮模型/积分/导航/私有/重放/训练实机0，原guard和锁保持，下一先两保存状态物理关、不能自动整路/三路线/24。见docs/RPCCR_TRACKING_EVIDENCE_REPAIR_V981_REPORT.md。\n')
    print(json.dumps(dict(source_only_qualified=True,frozen_files=len(manifest),models=0,physical_ready=False)))


if __name__=='__main__':
    main()
