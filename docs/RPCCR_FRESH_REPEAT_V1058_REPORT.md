# V1058 真实起点动态回归第一段

{
  "combined_original_main_and_repeat_counts": {
    "model_initializations": 2,
    "historical_replay_native": 0,
    "navigation_native": 89657,
    "own_replay_native": 89657,
    "private_mujoco_native": 0
  },
  "closed": true,
  "fresh_west_east_main_and_repeat_passed": false,
  "original_v1056_batch_error_kept": true,
  "main_reexecuted": false,
  "combined_three_route_development_passed": false,
  "error": {
    "error": "AssertionError('FIRST_FUNCTIONAL_FAILURE_STOP')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1058_fresh_repeat_entry/driver.py\", line 24, in main\n    result=json.loads((Path(task['output'])/'RESULT.json').read_text());proof=audit_native(task);row=dict(task=task,result=result,audit=proof,passed=code==0 and result['passed']and proof['passed']);rows.append(row);dump(O/'RESULTS.json',rows);assert proof['safety_passed'],'SAFETY_OR_EVIDENCE_FAILURE';assert row['passed'],'FIRST_FUNCTIONAL_FAILURE_STOP'\nAssertionError: FIRST_FUNCTIONAL_FAILURE_STOP\n"
  },
  "counts": {
    "model_initializations": 1,
    "historical_replay_native": 0,
    "navigation_native": 38929,
    "own_replay_native": 38929,
    "private_mujoco_native": 0
  },
  "unknown_counts": [],
  "unexecuted_task_ids": [],
  "hard_deadline_unix": 1794400200.0,
  "closed_unix": 1794398172.8275652,
  "guard_original": true,
  "new24_executed": 0,
  "training_updates": 0,
  "hardware_steps": 0
}

原V1056真实t0主任务不重跑，本入口只接续其原未执行的完整重复；历史命令/状态恢复0，原审计入口错误保持，源与控制算法字节不改。三路线总门尚未通过：NS动态交接未资格，EW规范初态被原统一预测储备拒绝，两路线本批未执行，不能报0/3失败率。固定24项未执行。开发提案库来自已观察WE，属于开发回归，不是未见任务。实际/自身重放/私有分账及功能/安全结论见RESULTS与各车独立审计。20:30硬截止不延长；原失败不升级；非实时/任意动态或递归安全保证。
