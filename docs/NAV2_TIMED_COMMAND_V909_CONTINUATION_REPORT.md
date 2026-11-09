# V909 有限执行与刹停资格：一次输出入口接续

```json
{
  "status": "NOT_PASSED",
  "original_operational_failure_preserved": true,
  "original_case00_actual_native": 420,
  "original_case00_own_replay_native": 420,
  "platform_total_actual_native_including_original": 7560,
  "platform_total_own_replay_including_original": 7560,
  "platform_unexecuted": 0,
  "navigation_actual_native": 6664,
  "navigation_own_replay_native": 6664,
  "navigation_private_native": 0,
  "navigation_attempted": 1,
  "navigation_unexecuted": 1,
  "new24": 0,
  "training": 0,
  "hardware": 0,
  "deadline_unix": 1794197278.8023248,
  "stopping_reason": {
    "error": "AssertionError('CONTINUATION_FIRST_FAILURE main_we')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v909_output_continuation/campaign.py\", line 39, in main\n    launch([sys.executable,'-B',str(OPS/'entry.py'),'launch',str(tp),str(ap)],task['task_id'],260)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v909_output_continuation/campaign.py\", line 25, in launch\n    assert rc==0,'CONTINUATION_FIRST_FAILURE '+label\nAssertionError: CONTINUATION_FIRST_FAILURE main_we\n"
  },
  "remote_pending": true
}
```

原V909因工厂写入根限制而闭批NOT_PASSED不改。其首组实际420步及完整自重放420步保留并复用，本接续只绑定同一冻结程序的操作输出根，不重复已执行工况、没有改科学阈值；继承原2026-11-09 12:07:58.802325绝对截止。平台经验界不是形式化动力学保证；一条路线开发和重复也不等于24项确认。任何新失败后不再接续。远端下载与SHA回读前不清理必须证据。
