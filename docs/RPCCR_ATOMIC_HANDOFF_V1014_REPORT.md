# V1014停稳原子交接通宵实验

状态：NOT_PASSED。截止2026-11-11 08:00，不延长；旧失败/窗口保持。

科学：新鲜零速许可与恢复停车所有权原子交接；原180秒导航内最多8完整进展段，每段原输入/几何/跟踪/.4米进展/200步停车门不变，提交前预留完整段时间。纯解析预测状态重建允许1e-12浮点差，实际qpos/qvel/ctrl/mocap全重放仍1e-8，控制与身体请求仍精确。

分账：

```json
{
  "status": "NOT_PASSED",
  "stop_reason": {
    "error": "AssertionError('FIRST_DEVELOPMENT_FUNCTION_OR_SAFETY_EVIDENCE_FAILURE')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1014_atomic_handoff_navigation/campaign.py\", line 63, in main\n    assert task['stage']=='confirmation'and row['evidence_passed'],'FIRST_DEVELOPMENT_FUNCTION_OR_SAFETY_EVIDENCE_FAILURE'\nAssertionError: FIRST_DEVELOPMENT_FUNCTION_OR_SAFETY_EVIDENCE_FAILURE\n"
  },
  "known_counts": {
    "navigation_models": 1,
    "navigation_native": 7930,
    "own_replay_native": 7930,
    "private_native": 0,
    "preflight_models": 3
  },
  "unknown_counts": [],
  "confirmation_executed": 0,
  "confirmation_unexecuted": 24,
  "confirmation_successes": 0,
  "full24_rate": null,
  "models_during_closure": 0,
  "old_failures_preserved": true,
  "guard_original": true,
  "execution_lock_idle": true
}
```

完整行驶发现、因果控制、实际停车、续行、目标和完整重放全部门通过才记成功。开发/重复/旧批不混新24；未执行不报0/24。有限单actor课程，非任意地图/遮挡/多actor/实时/递归安全或RAS保证。训练/实机/Stage0。网络离线时保留有界必要原证据，待重新联网进行零模型上传校验。
