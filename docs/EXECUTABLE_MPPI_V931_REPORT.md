# V931 停车死区一致性 MPPI 开发

```json
{
  "status": "NOT_PASSED",
  "platform_actual_native": 0,
  "platform_own_replay_native": 0,
  "navigation_actual_native": 18202,
  "navigation_own_replay_native": 18202,
  "navigation_private_native": 0,
  "platform_passed": true,
  "attempted_navigation": 1,
  "unexecuted_navigation": 3,
  "new24": 0,
  "training": 0,
  "hardware": 0,
  "deadline_unix": 1794217221.0305147,
  "remote_pending": true,
  "closed_reason": {
    "error": "AssertionError('FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE static_main_we')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v931_deadband_consistent_mppi/campaign.py\", line 36, in main\n    launch([sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)],task['task_id'],260)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v931_deadband_consistent_mppi/campaign.py\", line 30, in launch\n    assert rc==0,'FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE '+label\nAssertionError: FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE static_main_we\n"
  }
}
```

本轮为成熟导航基线适配：MPPI候选和预测同时纳入原Adapter低于.005m/s停车死区，SG平滑后整序列及已选控制历史使用同一死区；评分前统一挡位、曲率与实际速度限值，实测速度初始化，最终完整车身轨迹碰撞核验；静态主与重复先通过，才条件动态主与重复。原19实体、车辆、传感、目标与逐原生.15米/控制速率/接触/全状态重放门保持。未部署原RP-CCR不确定性和全周期停车证明，不称新24动态验收或论文创新。异步重复逐条完整到达和自身重放，未要求不同导航逐状态相同。V928拒绝的ARX拟合未部署；V929原始换挡拒绝和所有旧失败保持；新候选固定旧实际body/scan与前后两条实际参考的真实Nav2换挡软件演练通过，0新模型资格不能当导航成功。
