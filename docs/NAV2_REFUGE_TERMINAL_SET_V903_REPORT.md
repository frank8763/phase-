# V903 同一历史退让路径准入与执行开发结果

```json
{
  "status": "NOT_PASSED",
  "rows": [
    {
      "task_id": "main_we",
      "passed": false,
      "returncode": 1,
      "actual_native": 18201,
      "replay_native": 18201,
      "private_native": 0,
      "goal_m": 4.163224527883793,
      "output": "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/runs/v858_nav2_verified/v903/main_we"
    }
  ],
  "actual_navigation_native": 18201,
  "own_navigation_replay_native": 18201,
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

原V897及全部旧失败保持。只计本轮导航，不是24项独立确认；内部退让改为实际后退、原因果驻留准入、取消后实际刹停再恢复。原目标.45/原生净空.15和全部物理门不变。本候选共享2026-11-09已锁定10:38:29.771335总截止；不重置窗口。退让参考只用实际历史逆行路径，准入与控制一致，正常Smac不改。完整证据远端SHA和下载恢复通过后才清理。
