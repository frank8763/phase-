# V1056 真实起点动态回归第一段

{
  "closed": true,
  "fresh_west_east_main_and_repeat_passed": false,
  "combined_three_route_development_passed": false,
  "error": {
    "error": "ValueError('NONCAUSAL_OR_DUPLICATE_SCAN')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1056_fresh_route_regression/driver.py\", line 24, in main\n    result=json.loads((Path(task['output'])/'RESULT.json').read_text());proof=audit_native(task);row=dict(task=task,result=result,audit=proof,passed=code==0 and result['passed']and proof['passed']);rows.append(row);dump(O/'RESULTS.json',rows);assert proof['safety_passed'],'SAFETY_OR_EVIDENCE_FAILURE';assert row['passed'],'FIRST_FUNCTIONAL_FAILURE_STOP'\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1056_fresh_route_regression/audit.py\", line 42, in audit_native\n    reconstructed.update(scan)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1024_full_route_execution/causal.py\", line 20, in update\n    self.last_scan=scan;row=self.envelope.update(scan)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v891_dynamic_consistency_software/support_envelope.py\", line 25, in update\n    if self.when is not None and now<=self.when:raise ValueError('NONCAUSAL_OR_DUPLICATE_SCAN')\nValueError: NONCAUSAL_OR_DUPLICATE_SCAN\n"
  },
  "counts": {
    "model_initializations": 1,
    "historical_replay_native": 0,
    "navigation_native": 50728,
    "own_replay_native": 50728,
    "private_mujoco_native": 0
  },
  "unknown_counts": [],
  "unexecuted_task_ids": [
    "repeat_west_east",
    "main_north_south",
    "repeat_north_south",
    "main_east_west",
    "repeat_east_west"
  ],
  "hard_deadline_unix": 1794400200.0,
  "closed_unix": 1794397596.7812998,
  "guard_original": true,
  "new24_executed": 0,
  "training_updates": 0,
  "hardware_steps": 0
}

本批仅原WE真实t0主与成功条件完整重复；历史命令/状态恢复0。三路线总门尚未通过：NS动态交接未资格，EW规范初态被原统一预测储备拒绝，两路线本批未执行，不能报0/3失败率。固定24项未执行。开发提案库来自已观察WE，属于开发回归，不是未见任务。实际/自身重放/私有分账及功能/安全结论见RESULTS与各车独立审计。20:30硬截止不延长；原失败不升级；非实时/任意动态或递归安全保证。
