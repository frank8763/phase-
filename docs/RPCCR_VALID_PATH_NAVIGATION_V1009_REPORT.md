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
