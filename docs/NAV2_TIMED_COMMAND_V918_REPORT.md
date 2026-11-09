# V918 有限命令与刹停时序管道

```json
{
  "status": "NOT_PASSED",
  "platform_actual_native": 0,
  "platform_own_replay_native": 0,
  "navigation_actual_native": 6975,
  "navigation_own_replay_native": 6975,
  "navigation_private_native": 0,
  "platform_passed": true,
  "attempted_navigation": 1,
  "unexecuted_navigation": 1,
  "new24": 0,
  "training": 0,
  "hardware": 0,
  "deadline_unix": 1794200306.6639833,
  "remote_pending": true,
  "closed_reason": {
    "error": "AssertionError('FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE main_we')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v918_reference_backup_balance/campaign.py\", line 39, in main\n    launch([sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)],task['task_id'],260)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v918_reference_backup_balance/campaign.py\", line 30, in launch\n    assert rc==0,'FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE '+label\nAssertionError: FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE main_we\n"
  }
}
```

本轮仅复用旧18工况资格，沿用公开周期先验，沿用全周期终端和条件误差界，采用全周期软参考/原有限硬局部预测，新增陈旧新提案保留旧合格证书且不发新命令，条件原西向东主任务和重复。旧失败和旧截止保持。只覆盖新增公开已知频率的周期课程，不能声称原任意方向.08速度类保证。执行误差界沿用V909经验资格和在线监测，不是递归安全证明、24项验收或RAS创新证明。所有原生净空、接触、控制和完整重放门保持。位置误差经验模型按当前测量速度与新命令方向区分：同向或零命令.02米、反转.04米；原18保存响应重新独立审核，全原生持续监测，非普遍动力学保证。全周期终端和旧证书保留属于新验证机制，未通过前不声称递归安全。未执行的导航不计失败率分母。
