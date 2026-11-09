# V909 有限命令与刹停时序管道

```json
{
  "status": "NOT_PASSED",
  "platform_actual_native": null,
  "platform_own_replay_native": null,
  "navigation_actual_native": 0,
  "navigation_own_replay_native": 0,
  "navigation_private_native": 0,
  "platform_passed": false,
  "attempted_navigation": 0,
  "unexecuted_navigation": 2,
  "new24": 0,
  "training": 0,
  "hardware": 0,
  "deadline_unix": 1794197278.8023248,
  "remote_pending": true,
  "closed_reason": {
    "error": "AssertionError('FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE response_00')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v909_timed_command_contract/campaign.py\", line 37, in main\n    launch([str(R/'run_phase.sh'),str((C/'qualify_response.py').relative_to(R)),str(i)],'response_%02d'%i,65)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v909_timed_command_contract/campaign.py\", line 30, in launch\n    assert rc==0,'FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE '+label\nAssertionError: FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE response_00\n"
  }
}
```

本轮仅固定18工况执行/刹停资格及条件原西向东主任务和重复。旧失败和旧截止保持。内部六秒驻留门被显式修改，新的误差界只属经验资格和在线监测，不是递归安全证明、24项验收或RAS创新证明。所有原生净空、接触、控制和完整重放门保持。未执行的导航不计失败率分母。
