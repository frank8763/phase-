# V1084 南北保存段闭环验证：主任务与完整重复通过

两次均从规范NS起点精确恢复18074旧原生步，然后新执行1417运动步和2200完整停车步。每次27项独立审核全部通过，179个完整未来证书逐条回核；两次完整21691状态/ctrl/mocap轨迹最大误差0，模型规范初态、真实接触和首次发现一致。不是新独立整路或24确认。

|实测指标|结果|原门|
|---|---:|---:|
|最终目标距离|0.310470m|≤0.45m|
|保存态后实际位移|1.340633m|≥1m|
|最小实际净空|0.279217m|≥0.15m|
|最小完整预测raw净空|0.270014m|≥0.243534210m|
|最大局部预测位置误差|0.000994325m|≤0.04m|
|最大完整参考横向距离|0.0335592m|≤0.04m|
|最大局部航向误差|0.000657833rad|≤0.035rad|
|最大轮角误差|0.00570370rad|≤0.015rad|
|最大实际纵向速度|0.129581m/s|≤0.13m/s|
|坏接触|0|0|
|完整自身重放误差|0|≤1e-8|

本次同时修复累计纵向落后和因到达时刻变化导致的动态净空拒绝。使用实测路径进度、8原生步反馈和有限完整净空筛选后的平滑参考偏移；原未偏移方案和停车等待拒绝保留。几何前视是成熟方法，本组件结果不能单独作为RP-CCR创新或RAS验收。

运动阶段14.17s仿真对应完整未来预测墙钟144.71s（主）/144.13s（重复），约10.2倍；不支持实时性。每次额外完整停车22s，历史重放180.74s仿真。完整预测证据审核另外消耗墙钟，不能把它计成车辆实际行驶。历史/新实际/自身重放与解析预测分账见下表；工厂内部模型构造次数仍未知。

两个任务都通过后本批提前闭账，没有继续跑满90分钟，没有自动新整路/三路线/24/训练。REVIEW_PENDING原字节恢复，执行锁空闲。接下来需从规范起点验证新闭环接入的完整NS路线；本组件不能替代该验证。

# Measured-pose feedback saved-continuation validation

```json
{
  "closed": true,
  "passed": true,
  "version": "v1084",
  "scope": "same observed NS saved continuation main and conditional full repeat, not fresh navigation acceptance",
  "attempted": [
    "main_saved_ns",
    "repeat_saved_ns"
  ],
  "unexecuted": [],
  "error": null,
  "complete_repeat": {
    "passed": true,
    "maximum_state_ctrl_mocap_error": 0.0,
    "complete_length": 21691
  },
  "counts": {
    "vehicle_initializations": 2,
    "historical_replay_native": 36148,
    "new_actual_native": 7234,
    "own_replay_native": 43382,
    "replay_state_initializations": 2,
    "private_mujoco_native": 0,
    "training_updates": 0,
    "analytical_prediction_native": 1071828
  },
  "guard_original": true,
  "source_unchanged": true,
  "whole_route_passed": false,
  "new24_executed": false
}
```

This is an observed saved-state component, not a fresh route or24 confirmation. Empirical speed envelope is conditional, not global recursive safety.
