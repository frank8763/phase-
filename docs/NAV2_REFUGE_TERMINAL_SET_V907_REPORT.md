# V907 因果退让走廊记忆开发结果

```json
{
  "status": "NOT_PASSED",
  "rows": [
    {
      "task_id": "main_we",
      "passed": false,
      "returncode": 1,
      "actual_native": 12080,
      "replay_native": 12080,
      "private_native": 0,
      "goal_m": 2.6342261194429666,
      "output": "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/runs/v858_nav2_verified/v907/main_we"
    }
  ],
  "actual_navigation_native": 12080,
  "own_navigation_replay_native": 12080,
  "private_native": 0,
  "platform_actual_native": 0,
  "platform_replay_native": 0,
  "historical_platform": "V898 reused evidence only; old V896 initialization accounting remains unknown",
  "new24": 0,
  "training": 0,
  "real_robot": 0,
  "deadline_unix": 1794191909.7713351,
  "models_this_finalize": 0,
  "integrations_this_finalize": 0,
  "remote_upload_pending": true,
  "raw_cache_preserved_until_remote_verified": true
}
```

原V897及全部旧失败保持。只计本轮导航，不是24项独立确认；内部退让改为实际后退、原因果驻留准入、取消后实际刹停再恢复。原目标.45/原生净空.15和全部物理门不变。本候选共享2026-11-09已锁定10:38:29.771335总截止；不重置窗口。退让参考只用实际历史逆行路径，准入与控制一致，正常Smac参数不改，全局未来占据改为软代价50/主图126与静态可接受目标；局部原完整未来硬占据100及其控制/监督门不变。本候选在原路径含倒车回环时保留此前真实历史路径，并在当前实际位姿与新观测下重新核验原全部退出门；仍最多3次恢复，不改变驻留/净空/时间门。失败事件无可选路径按真实失败审计，不伪造通过。当前候选不是旧安全证明的继承。完整证据远端SHA和下载恢复通过后才清理。
