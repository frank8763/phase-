# V1067 刹停储备与主动因果恢复 · 三路线开发

{
  "main_attempted": 3,
  "repeat_attempted": 0,
  "main_navigation_known_started": 3,
  "main_navigation_unknown": 0,
  "closed": true,
  "deadline_unix": 1794459154.2281792,
  "closed_at": 1794454195.5989609,
  "combined_three_route_development_passed": false,
  "confirmation24_authorized": false,
  "confirmation24_executed": false,
  "main_executed": 3,
  "main_successes": 0,
  "repeat_executed": 0,
  "complete_repeat_comparisons": [],
  "counts": {
    "model_initializations": 6,
    "historical_replay_native": 0,
    "navigation_native": 116261,
    "own_replay_native": 116261,
    "private_mujoco_native": 0
  },
  "unknown_counts": [],
  "attempted_task_ids": [
    "t0_dev_north_south",
    "t0_dev_east_west",
    "t0_dev_west_east",
    "A_main_north_south",
    "A_main_east_west",
    "A_main_west_east"
  ],
  "unexecuted_task_ids": [
    "A_repeat_north_south",
    "A_repeat_east_west",
    "A_repeat_west_east"
  ],
  "error": null,
  "guard_original": true,
  "resource_policy": {
    "cpu_affinity": [
      2
    ],
    "nice": 19,
    "scheduler": 5,
    "gpu_visible": "",
    "mujoco_gl": "osmesa",
    "io_class": 3,
    "stage_process_access": false
  },
  "training_updates": 0,
  "hardware_steps": 0
}

本批只含原三路线主任务和成功后的完整重复，无24项确认授权。有限安全推进和观察恢复均不计到达成功；完整到达、发现后328实际刹停、实际续行1m及全部状态控制重放/重复门保持。原模型、19实体、3m32束传感、5%漏检及噪声不变；EW仍为用户批准北移0.10m课程。旧失败不升级，不声称实时、任意遮挡、递归安全或实机保证。
