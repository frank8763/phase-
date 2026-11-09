# RP-CCR主线归位：V933固定记录与V934真实动态开发

## 结论

**V934 NOT_PASSED，首次功能失败已封账，不自动追加物理候选。** 本次已恢复RPP+RP-CCR主线，未继续改MPPI。原西向东动态主180秒未到达，45.56秒真实发现actor后仅续行.202587米，目标剩4.018338米；发现后>=1米和最终到达均失败，完整重复与新24未执行。

18,202新实际原生/18,202完整自身控制重放、私有模型积分0；最低实际净空.269113535米，坏接触0，全状态和接触重放误差0，原生最大墙钟滞后.003330秒。实际因果运动支撑、原命令证书与原生入口、恢复选择来源及完整物理证据审核PASS；功能FAIL，不以安全停车冒充动态完成。

## 为什么这次改动没有产生预期作用

V933对已归档V924的781个非零名义命令拒绝进行了同一准入门的固定输入复核：31个有获证进展控制、392个有获证退让控制、30个仅能停、328个无新获证控制。原2073个已通过名义提案保持原样。这个结果指出旧调度漏评替代动作；它不是新动态成功率，也没有证明实际新轨迹能够走到这些旧状态。

V934将固定13原范围控制接入真实派发函数，保留RPP、因果追踪/周期预测、.155预测/.15实际、经验执行界与完整刹停/终端证书；零命令/静默停车绝不改成恢复运动。真实运行中，新恢复分支触发0次。发现后37个非零名义提案均未进入替代分支，此后2635个请求为零。上游116次规划中仅38次成功；73次Smac208、4次虚拟终点根205、1次其他失败。车停在约x=.205/y=-.679；上游已经失去可执行参考，名义层不再给出被拒的非零命令。

因此这次没有验证到新恢复机制的闭环效果，也不能据此否证它的动作选择收益。**我在本轮实验设计中遗漏了“规划已停、非零提案不存在”这一实际入口；只有固定旧状态上的正例不足以保证新运行触发干预。** 这是本次实验安排的缺口，不能归咎于用户、断网或实体车必然走不了。

## RP-CCR应该如何收敛

恢复机制必须覆盖“正常参考消失或被时域占据阻断”的状态，并通过真实可执行走廊/控制交接恢复名义层，不能只等一个非零控制被拒再介入。全周期运动并集作为静态硬占据会消除时间通行窗口；208也可能是预算/表示问题，不是物理完备无解。下一次设计应先用实际停滞状态复现上游失路，在同一原因果状态和时间下联立参考、执行证书和恢复入口，证明干预实际触发且可持续续接；不能盲目把碰撞监控零命令改成运动或降低安全门。

已通过静态的V884/V885 FeasibleRPP插件与FollowPath参数继续冻结为基座，不再更换名义控制器来代替RP-CCR进展。V929/V931是未合格MPPI基线分支；其失败不抹掉旧静态通过，也不构成论文算法优势证据。当前Nav2实现还使用公开.32rad/s周期先验和经验执行误差界，不能声称继承原更宽运动类或原328步安全理论。

本次不再启动新物理/新候选，不用剩余17:40窗口复制重跑。旧静态23/24、旧动态开发和确认前8项6成功2失败均保留各自版本，不拼接为最终验收。论文仍缺最终同版本动态确认、公平对照/消融和实机结果；本轮不能支持“动态已完成”或保证RAS投稿。源码、原失败与证据上传同仓GitHub并回读后清缓存。

完整计数：
```json
{
  "status": "NOT_PASSED",
  "models_in_analysis": 0,
  "integrations_in_analysis": 0,
  "actual_native": 18202,
  "own_replay_native": 18202,
  "private_native": 0,
  "minimum_clearance_m": 0.26911353511423786,
  "bad_contacts": 0,
  "goal_m": 4.018338260805572,
  "final_speed_m_s": 3.0174846819042794e-06,
  "first_actor_detection": {
    "native_tick": 4556,
    "sim_time": 45.559999999999505,
    "xy": [
      0.00792387950933737,
      -0.6649834863360342
    ],
    "rays": [
      31
    ],
    "source": "actual physical sensor return and corrupted range; offline-only actor attribution"
  },
  "postdiscovery_actual_travel_m": 0.2025874448213109,
  "total_travel_m": 4.476638443869186,
  "original_full_independent_audit_passed": false,
  "full_evidence_audit_passed": true,
  "functional_checks": {
    "action_success": false,
    "strict_arrival": false,
    "actual_stopped": true,
    "dynamic_discovery_and_continuation": false
  },
  "runtime_error": "ProtocolError('NAVIGATION_DEADLINE')",
  "maximum_native_lag_s": 0.0033302580122835934,
  "routes": 116,
  "passed_routes": 38,
  "route_error_codes": {
    "205": 4,
    "208": 73,
    "None": 1
  },
  "virtual_terminal_root_205": 4,
  "dispatched_decisions": 3581,
  "after_detection_decisions": 2672,
  "after_detection_nonzero_nominal": 37,
  "after_detection_zero_nominal": 2635,
  "new_recovery_decisions": 0,
  "new_recovery_physical_benefit_established": false,
  "old_saved_refusals": 781,
  "old_saved_component_modes": {
    "CERTIFIED_PROGRESS_ALTERNATIVE": 31,
    "CERTIFIED_STOP_ONLY": 30,
    "CERTIFIED_CLEARANCE_RECOVERY": 392,
    "NO_NEW_CERTIFIED_CONTROL": 328
  },
  "component_counterfactual_is_not_online_success": true,
  "new24": "UNEXECUTED",
  "repeat": "UNEXECUTED",
  "mainline": "Fixed passed FeasibleRPP nominal controller plus RP-CCR causal risk/admission/corridor/recovery. MPPI excluded.",
  "closed_reason": "180-second dynamic goal deadline; discovery-continuation>=1m and arrival both failed. New arbitration never triggered because no rejected nonzero proposal reached it in this realized run.",
  "next_design_finding": "Recovery must handle a missing/blocked nominal reference before ordinary motion disappears. Do not override collision-monitor zero blindly; restore time-consistent executable recovery corridor through a separately validated control handoff. Spatial full-cycle occupancy and planner/execution semantics need joint diagnosis; 208 is not proof of no feasible physical trajectory."
}
```
