# V1090 overnight route validation and conditional confirmation

```json
{
  "closed": true,
  "passed": false,
  "version": "v1090",
  "three_route_development_passed": false,
  "confirmation_passed": false,
  "error": {
    "error": "AssertionError('FIRST_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1090_active_corridor/campaign.py\", line 61, in main\n    for task in tasks[:5]:run(task)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1090_active_corridor/campaign.py\", line 48, in run\n    rp=out/'RESULT.json';rp=rp if rp.exists()else out/'physics/paired/ENTRY_FAILURE_RESULT.json';result=json.loads(rp.read_text())if rp.exists()else dict(passed=False,missing_result=True);row=dict(task=task,result=result,returncode=code);rows.append(row);dump(O/'RESULTS.json',rows);assert code==0 and result['passed'],'FIRST_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE'\nAssertionError: FIRST_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE\n"
  },
  "attempted": [
    "main_west_east"
  ],
  "unexecuted": [
    "repeat_west_east",
    "main_east_west",
    "repeat_east_west",
    "repeat_ns_regression",
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
    "new_actual_native": 24535,
    "own_replay_native": 24535,
    "replay_state_initializations": 1,
    "private_mujoco_native": 0,
    "training_updates": 0,
    "analytical_prediction_native": 230200
  },
  "development_counts": {
    "vehicle_initializations": 1,
    "historical_replay_native": 0,
    "new_actual_native": 24535,
    "own_replay_native": 24535,
    "replay_state_initializations": 1,
    "private_mujoco_native": 0,
    "training_updates": 0,
    "analytical_prediction_native": 230200
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

## 11月13日晨检与零模型复现

**未通过；昨晚22:31提前停，未跑满通宵。**22:29:41启动，22:31:12写闭批，约91秒。只执行首WE主，24535新实际原生与24535完整自身重放，误差0、接触一致；首15560发现，20160恢复根，已执行4375/8350走廊。剩余4开发导航、24预检、24主及3固定重复全部未执行，不能报0/24通过率。原NS主+重复成功保持。

实际记录最低净空.276984656m、坏接触0；已执行恢复局部跟踪最大.00436077m/.00275504rad/.01032649rad，均在原门内。发现后实际累计路程.663882686m，未完成整个有限段或原目标；末距原目标4.047803m。完整25门独立审核未运行，不以自身重放代替独立功能审核。

保存态原设置零模型复现：全24535步ctrl重建误差2.22e-16，根24535/走廊cursor4375、剩3975原生。唯一拒绝是full_raw_geometry：静态最小.243403618892<原.243534210202，差.000130591310m（约.131mm），发生在预测未来第914步。动态最小.457057225m，速度/控制/完整2200预测尾/终端全周期门均过。说明是实际测量重新定根后，未执行的静态转弯后缀失去原规划净空余量；不是撞击、模型入口错误、动态占据拒绝、控制抢权或实际局部误差越门。近阈值不能作为降低原门的理由。

**退出缺陷必须明示：**实际末平移速度.074569858m/s，纵速.072874437，yawrate-.044297242，尚未停稳。代码在重认证拒绝处抛异常、完成记录与自身重放后退出，没有实际执行完整2200停车或已保留可执行后备。仿真进程结束会停止模型时钟，不能称真实车辆安全停车。原生记录无坏接触并不弥补此缺陷；原末状态和失败不改。下一优先验证应为该保存状态的证书拒绝→后备控制执行→实际停稳闭环，再独立处理静态参考/滚动可恢复余量，不能继续盲加搜索额度或直接恢复整路。

原批源、结果、归档保持，REVIEW_PENDING原字节恢复/Phase锁空闲，父和watchdog均已退出。196来源37932229字节本地32MiB块/来源/解压SHA回读完成，远端待交付。原09:00截止不延长，本次晨检和复现0新模型/积分，不自动重启导航。
