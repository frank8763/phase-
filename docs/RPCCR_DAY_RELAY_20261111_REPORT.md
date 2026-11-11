# 2026-11-11日间离线接力实际结果

{
  "closed": true,
  "goal_continuation_and_repeat_passed": false,
  "reverse_qualified": true,
  "sources": [
    {
      "id": "source_01",
      "status": "SOURCE_WALL_CAP",
      "error": {
        "error": "TimeoutError('ROOT_SOURCE_CAP')",
        "models": 0,
        "integrations": 0
      }
    }
  ],
  "error": {
    "error": "InterruptedError('ROOT_ABSOLUTE_OR_EXTERNAL_STOP')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1047_day_relay/driver.py\", line 49, in main\n    cfg=C/'configs'/(config['id']+'.json');limit=min(HARD_END-30,time.time()+config['wall_s']+10);code=run_job([sys.executable,'-B',C/'source_job.py',cfg,str(limit-10)],O/(config['id']+'.console'),limit,'source',config['id']);result_path=O/'sources'/config['id']/'RESULT.json'\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1047_day_relay/driver.py\", line 14, in run_job\n    try:return child.wait(timeout=max(.001,remaining))\n  File \"/home/linghu/miniconda3/envs/mk_mujoco/lib/python3.10/subprocess.py\", line 1209, in wait\n    return self._wait(timeout=timeout)\n  File \"/home/linghu/miniconda3/envs/mk_mujoco/lib/python3.10/subprocess.py\", line 1953, in _wait\n    time.sleep(delay)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1047_day_relay/driver.py\", line 33, in stop\n    def stop(*_):raise InterruptedError('ROOT_ABSOLUTE_OR_EXTERNAL_STOP')\nInterruptedError: ROOT_ABSOLUTE_OR_EXTERNAL_STOP\n"
  },
  "counts": {
    "model_initializations": 3,
    "new_response_native": 2100,
    "historical_replay_native": 0,
    "new_navigation_suffix_native": 0,
    "own_replay_native": 2100,
    "private_mujoco_native": 0
  },
  "unknown_counts": [],
  "closed_unix": 1794387810.2089462,
  "hard_deadline_unix": 1794400200.0,
  "guard_original": true,
  "new24_executed": 0
}

完整实际原生、资格、失败/未执行及重复分账见runs/v1047_day_relay_20261111/COMPLETION.json。原困难任务以保存态继续主与完整重复门为准，新24未执行；不得当新独立样本或实时/RAS保证。
