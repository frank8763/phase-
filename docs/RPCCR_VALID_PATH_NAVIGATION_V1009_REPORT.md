# V1009普通Nav2检查器与有效路径保持

状态：NOT_PASSED。停止原因：`{'error': "AssertionError('FIRST_DEVELOPMENT_FUNCTION_OR_SAFETY_EVIDENCE_FAILURE')", 'traceback': 'Traceback (most recent call last):\n  File "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1009_explicit_checker_navigation/campaign.py", line 63, in main\n    assert task[\'stage\']==\'confirmation\'and row[\'evidence_passed\'],\'FIRST_DEVELOPMENT_FUNCTION_OR_SAFETY_EVIDENCE_FAILURE\'\nAssertionError: FIRST_DEVELOPMENT_FUNCTION_OR_SAFETY_EVIDENCE_FAILURE\n'}`。

只改普通BT的明确目标检查器与官方有效当前路径保持；其余物理/恢复控制/传感/安全门不改。V1010完整安装软件动作成功仅是非物理资格；V1003两个实际恢复组件通过保持，V1004与V1006原失败不抹去。

实际分账（未知不填0）：

```json
{
  "status": "NOT_PASSED",
  "error": {
    "error": "AssertionError('FIRST_DEVELOPMENT_FUNCTION_OR_SAFETY_EVIDENCE_FAILURE')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1009_explicit_checker_navigation/campaign.py\", line 63, in main\n    assert task['stage']=='confirmation'and row['evidence_passed'],'FIRST_DEVELOPMENT_FUNCTION_OR_SAFETY_EVIDENCE_FAILURE'\nAssertionError: FIRST_DEVELOPMENT_FUNCTION_OR_SAFETY_EVIDENCE_FAILURE\n"
  },
  "known_counts": {
    "navigation_models_known": 1,
    "navigation_native_known": 10076,
    "own_replay_native_known": 10076,
    "private_native_known": 0,
    "preflight_models_known": 3
  },
  "unknown_counts": [],
  "started_navigation_tasks": [
    "main_we"
  ],
  "confirmation_executed": 0,
  "confirmation_unexecuted": 24,
  "confirmation_successes": 0,
  "full24_rate": null,
  "confirmation_repeats": [],
  "old_V1004_V1006_failures_preserved": true,
  "V1003_components_reused_not_repeated": true,
  "models_during_closure": 0,
  "current_guard_original": true,
  "execution_lock_idle": true,
  "absolute_deadline_unix": 1794355200.0
}
```

旧批次、组件、开发、重复均不混新24分母。未完成全24不报全分母率。无训练、实机或Stage；不宣称实时、任意地图/遮挡、多actor、递归安全或RAS优势。

## 零模型首因补核 V1012

主任务实际发现后走1.243952m，原目标剩2.649343m。10076新增原生＋10076完整自身重放，最大qpos/qvel/ctrl/mocap误差0，接触重复无差异；私有MuJoCo积分0。3原t0初始化独立计数，不混导航。最低实际净空.272949329m，坏接触0，停止后的平动速度约1.42e-6m/s。

两段原因果恢复都完整执行了计划输入和200原生停车尾，实际目标进展.579007204/.485946270m；最大位置误差.002490016/.002452375m，最大航向误差.001915398/.001746003rad，均在原.04m/.035rad门内。说明本次两段跟踪没有越门；不是全任务成功。

直接停止原因：第二恢复段9866结束、9867释放，首个正常控制候选使用9868时刻的车体观测，检查时年龄.053441661s超过原.05s。冻结监督器在恢复结束后清空retained_proof并释放普通控制，首条新的许可尚未建立；旧许可丢弃后不能凭过期观测计算新转向，安全门因此正确停机。普通许可最后接受的观测为7976，不能跨越本次恢复继续冒用。具体调度/序列化造成这次53.44ms间隙的份额未单独记录，不能唯一归因于规划器或车辆。

原命令管审核只有no_unqualified_command_failure为false，但原总审核依然NOT_PASSED。另行调用冻结预测重建审核时，第一段状态位级相等检查因6.94e-17数值差失败（控制误差0，第二段状态误差0）；此补核异常和原严门保留，不用数值诊断追认原审核通过。补充结果明确只报告原始实际轨迹的跟踪、进展、输入对应与误差。

下一步先修“停稳恢复→普通导航”的原子交接：保留原停车所有权，等新鲜实测车体与新合格零速控制许可确认后才释放和启动普通动作；不放宽50ms门，不沿用恢复前运动许可。先以本保存故障做软件红绿交接验证，之后另议物理窗口。该修订尚未实现或获得物理资格。

本轮实际20:08:03启动、20:10:18首失败闭批，原21:38:03硬截止未重置；重复、三路线和24项均未执行，不称跑满90分钟。后台模型已关闭，REVIEW_PENDING原字节恢复、锁空闲。原全部实际来源及解压成员SHA已上传回读，Git唯一push/HEAD f013984143ef15df6ad3f0bf285188c0e8216871核验；后续补充只Release增量与本地提交，不第二push。
