# V943 原始账目与补充报告

结果NOT_PASSED。该批原始JSON账目及自动模板版本已归档保留；恢复走廊新机制、实际接管与失败原因见 [完整报告](RPCCR_REFERENCE_LOSS_V943_REPORT.md)。

```json
{
  "status": "NOT_PASSED",
  "platform_actual_native": 0,
  "platform_own_replay_native": 0,
  "navigation_actual_native": 6455,
  "navigation_own_replay_native": 6455,
  "navigation_private_native": 0,
  "platform_passed": true,
  "attempted_navigation": 1,
  "unexecuted_navigation": 1,
  "new24": 0,
  "training": 0,
  "hardware": 0,
  "deadline_unix": 1794225135.0809088,
  "remote_pending": true,
  "closed_reason": {
    "error": "AssertionError('FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE main_we')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v943_rpccr_segment_navigation/campaign.py\", line 39, in main\n    launch([sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)],task['task_id'],260)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v943_rpccr_segment_navigation/campaign.py\", line 30, in launch\n    assert rc==0,'FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE '+label\nAssertionError: FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE main_we\n"
  }
}
```
