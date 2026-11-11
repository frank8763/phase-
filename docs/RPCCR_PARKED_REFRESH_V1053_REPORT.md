# V1053停车刷新与原困难任务续行结果

{
  "closed": true,
  "goal_continuation_and_repeat_passed": false,
  "reverse_qualified": true,
  "error": {
    "error": "AssertionError('FUNCTIONAL_FAILURE_STOP')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1053_parked_refresh_handoff/driver.py\", line 24, in main\n    result=json.loads((Path(task['output'])/'RESULT.json').read_text());proof=audit_native(task,True);rows.append(dict(task=task,result=result,audit=proof,passed=code==0 and result['passed']and proof['passed']));dump(O/'MODEL_RESULTS.json',rows);assert proof['safety_passed'],'SAFETY_OR_EVIDENCE_FAILURE';assert rows[-1]['passed'],'FUNCTIONAL_FAILURE_STOP'\nAssertionError: FUNCTIONAL_FAILURE_STOP\n"
  },
  "counts": {
    "model_initializations": 1,
    "historical_replay_native": 23640,
    "new_navigation_suffix_native": 5474,
    "own_replay_native": 29114,
    "private_mujoco_native": 0
  },
  "unknown_counts": [],
  "closed_unix": 1794394107.5566905,
  "hard_deadline_unix": 1794400200.0,
  "guard_original": true,
  "new24_executed": 0,
  "old_brake_only_contract_preserved": false
}

同原困难任务保存态续行主及完整重复。新的移动后备合同替代中间每原生立即刹停合同，不追认旧失败；不是新独立导航样本或24项验收，也不是实时/任意运动/递归安全/RAS保证。来源资格、全部实际安全/跟踪与重复证据见本轮目录。
