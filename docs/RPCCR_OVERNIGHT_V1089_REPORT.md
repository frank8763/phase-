# V1089 overnight route validation and conditional confirmation

```json
{
  "closed": true,
  "passed": false,
  "version": "v1089",
  "three_route_development_passed": false,
  "confirmation_passed": false,
  "error": {
    "error": "AssertionError('FIRST_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1089_route_scene_contract/campaign.py\", line 61, in main\n    for task in tasks[:4]:run(task)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1089_route_scene_contract/campaign.py\", line 48, in run\n    rp=out/'RESULT.json';rp=rp if rp.exists()else out/'physics/paired/ENTRY_FAILURE_RESULT.json';result=json.loads(rp.read_text())if rp.exists()else dict(passed=False,missing_result=True);row=dict(task=task,result=result,returncode=code);rows.append(row);dump(O/'RESULTS.json',rows);assert code==0 and result['passed'],'FIRST_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE'\nAssertionError: FIRST_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE\n"
  },
  "attempted": [
    "main_west_east"
  ],
  "unexecuted": [
    "repeat_west_east",
    "main_east_west",
    "repeat_east_west",
    "t0_confirm_01",
    "t0_confirm_02",
    "t0_confirm_03",
    "t0_confirm_04",
    "t0_confirm_05",
    "t0_confirm_06",
    "t0_confirm_07",
    "t0_confirm_08",
    "t0_confirm_09",
    "t0_confirm_10",
    "t0_confirm_11",
    "t0_confirm_12",
    "t0_confirm_13",
    "t0_confirm_14",
    "t0_confirm_15",
    "t0_confirm_16",
    "t0_confirm_17",
    "t0_confirm_18",
    "t0_confirm_19",
    "t0_confirm_20",
    "t0_confirm_21",
    "t0_confirm_22",
    "t0_confirm_23",
    "t0_confirm_24",
    "confirm_main_01",
    "confirm_main_02",
    "confirm_main_03",
    "confirm_main_04",
    "confirm_main_05",
    "confirm_main_06",
    "confirm_main_07",
    "confirm_main_08",
    "confirm_main_09",
    "confirm_main_10",
    "confirm_main_11",
    "confirm_main_12",
    "confirm_main_13",
    "confirm_main_14",
    "confirm_main_15",
    "confirm_main_16",
    "confirm_main_17",
    "confirm_main_18",
    "confirm_main_19",
    "confirm_main_20",
    "confirm_main_21",
    "confirm_main_22",
    "confirm_main_23",
    "confirm_main_24",
    "confirm_repeat_01",
    "confirm_repeat_09",
    "confirm_repeat_17"
  ],
  "complete_repeats": [],
  "counts": {
    "vehicle_initializations": 1,
    "historical_replay_native": 0,
    "new_actual_native": 20160,
    "own_replay_native": 20160,
    "replay_state_initializations": 1,
    "private_mujoco_native": 0,
    "training_updates": 0,
    "analytical_prediction_native": 0
  },
  "development_counts": {
    "vehicle_initializations": 1,
    "historical_replay_native": 0,
    "new_actual_native": 20160,
    "own_replay_native": 20160,
    "replay_state_initializations": 1,
    "private_mujoco_native": 0,
    "training_updates": 0,
    "analytical_prediction_native": 0
  },
  "confirmation_t0_counts": {
    "vehicle_initializations": 0,
    "historical_replay_native": 0,
    "new_actual_native": 0,
    "own_replay_native": 0,
    "replay_state_initializations": 0,
    "private_mujoco_native": 0,
    "training_updates": 0,
    "analytical_prediction_native": 0
  },
  "confirmation_main_counts": {
    "vehicle_initializations": 0,
    "historical_replay_native": 0,
    "new_actual_native": 0,
    "own_replay_native": 0,
    "replay_state_initializations": 0,
    "private_mujoco_native": 0,
    "training_updates": 0,
    "analytical_prediction_native": 0
  },
  "confirmation_repeat_counts": {
    "vehicle_initializations": 0,
    "historical_replay_native": 0,
    "new_actual_native": 0,
    "own_replay_native": 0,
    "replay_state_initializations": 0,
    "private_mujoco_native": 0,
    "training_updates": 0,
    "analytical_prediction_native": 0
  },
  "confirmation_mains_executed": 0,
  "full24_denominator_reportable": false,
  "source_unchanged": true,
  "guard_original": true,
  "old_NS_main_and_repeat_preserved": true,
  "lockstep_not_realtime": true,
  "raw_retained": true
}
```

EW uses declared north-shifted start. Partial confirmation never reported as a full24 success rate. Source/model/control gates retained; no realtime or hardware claim.

## 首次闭批检查

V1089在首WE主真实20160原生步后停止，首发现15560、完整2200停车+2400观测（无额外前进）后，到20160的实际停车状态；原目标尚余3.883385652m。失败是live_reference.produce在原5000展开静态拓扑搜索后，未得到同时passed与functional_goal_source的完整参考；尚未启动新的动态反馈未来生成。不是原场景哈希入口错误，真实模型443数组合同已过。此时仅能说明该有界规划候选未通过，不能断言没有物理路径或控制器无法跟踪。

实际记录最低净空.276984656、坏接触0，自身20160全步状态ctrl/mocap重放误差0/接触一致；完整功能及25门独立验收未通过，不能以自身重放替代独立全门。私有MuJoCo0、恢复live解析计数0（旧静态C++和静态Python预测不在该字段，不能说所有预测0）、训练0。WE重复/EW两项/24预检/24主/3重复均未执行，不报0/24成功率。

原NS成功主+完整重复保持。父及watchdog已正常退出，原REVIEW_PENDING恢复、APPROVAL/AUTHORIZATION撤销、Phase锁空闲；源码不改，原始证据全部本地归档分块/来源/解压SHA通过，远端待交付。用户离开前检查时不得误报通宵仍在运行。按本夜首功能失败停的冻结约定不修补/重跑。仅允许有界零模型保存状态原规划复现，0新模型积分；保存诊断为runs/v1089_saved_reference_diagnosis，绝不复用旧物理授权。

保存态原设置零模型复现已完成：全20160控制重建误差2.22e-16，原5000展开精确用完，搜索墙钟1.868592秒，terminated_by_wall=false；返回ORIGINAL_PYTHON_FINITE_PROGRESS_SOURCE_NOT_ARRIVAL，局部源安全/控制/停车门全过，goal_upper=false（终点上界3.682856m）。所以直接阻塞是有界搜索未给完整目标源，不是30秒超时或已执行动态跟踪失败。保存态复现3.44秒、0模型积分，未扩大展开数或改算法。
