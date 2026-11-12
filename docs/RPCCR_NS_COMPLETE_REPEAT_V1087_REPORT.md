# V1087 NS full-repeat result

原南北路线的新规范起点主任务V1085_entry及V1087完整重复已完成同科学版本闭合：两次均21351实际原生步，到原目标.308184610m并完整停车，最低实际净空.279217369m、坏接触0；各自完整控制重放误差0。主任务25门补充独立审核与重复25门正式独立审核均通过，二者全长qpos/qvel/ctrl/mocap最大误差0，模型/规范初态/发现/实际接触一致。原主批审核入口错误及V1086关机中断保持，不追认旧批原闭合结果。

770来源/74028583压缩字节归档、来源解压SHA及32MiB块重组回读通过；远端交付待完成，原件未删。REVIEW_PENDING原字节恢复，执行锁空闲。此结论是一条已观察开发NS路线，不是同版本三路线、新24项或实时/实机通过。

```json
{
  "closed": true,
  "passed": true,
  "version": "v1087",
  "scope": "One fresh complete NS repeat against saved independently supplementally audited V1085_entry main",
  "attempted": [
    "repeat_fresh_ns"
  ],
  "unexecuted": [],
  "error": null,
  "complete_repeat": {
    "passed": true,
    "maximum_state_ctrl_mocap_error": 0.0,
    "complete_length": 21351
  },
  "counts": {
    "vehicle_initializations": 1,
    "historical_replay_native": 0,
    "new_actual_native": 21351,
    "own_replay_native": 21351,
    "replay_state_initializations": 1,
    "private_mujoco_native": 0,
    "training_updates": 0,
    "analytical_prediction_native": 1422169
  },
  "new_main_samples": 0,
  "baseline_main_reexecuted": false,
  "baseline_original_failed_batch_preserved": true,
  "source_unchanged": true,
  "guard_original": true,
  "whole_route_passed": true,
  "new24_executed": false
}
```

Old V1085 entry/audit failures preserved. No three-route/24 acceptance or real-time claim.
