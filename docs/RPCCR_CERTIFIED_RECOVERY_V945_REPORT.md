# V945 RP-CCR持续观测活性回归

```json
{
  "status": "NOT_PASSED",
  "platform_actual_native": 0,
  "platform_own_replay_native": 0,
  "navigation_actual_native": 13517,
  "navigation_own_replay_native": 13517,
  "navigation_private_native": 0,
  "platform_passed": true,
  "attempted_navigation": 1,
  "unexecuted_navigation": 1,
  "new24": 0,
  "training": 0,
  "hardware": 0,
  "deadline_unix": 1794226950.9370122,
  "remote_pending": true,
  "closed_reason": {
    "error": "AssertionError('FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE main_we')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v945_rpccr_observation_liveness/campaign.py\", line 39, in main\n    launch([sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)],task['task_id'],260)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v945_rpccr_observation_liveness/campaign.py\", line 30, in launch\n    assert rc==0,'FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE '+label\nAssertionError: FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE main_we\n"
  }
}
```

V943获证恢复与FeasibleRPP原样保留，仅将持续监督200ms与新命令/安装50ms门分开，并持久化故障输入和部分事务事件。所有原命令/原生安全门、旧证书有效期、路径跟随界和目标门保持。历史V827三路线/V828六完整成功不能当作本版本成功，未执行新24。完整解释见RPCCR_REGRESSION_RECOVERY_V945_REPORT.md。
