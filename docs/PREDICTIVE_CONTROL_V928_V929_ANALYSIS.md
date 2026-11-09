# V928/V929 预测与执行一致性开发结果

V929 **NOT_PASSED**。仅静态原西向东主任务已执行，静态重复/动态主/动态重复3项未执行；新24为未执行，不能报0/24。3,274实际原生、3,274自身重放，私有积分0；最低实际净空0.261342608米，坏接触0，全qpos/qvel/ctrl/mocap与接触重放误差0。实际约32.74秒后完整停车，距目标6.678018400米。源/物理/入口控制重建各门PASS，功能FAIL，不是动态通过。

本轮先复核原V862/V863记录：V862有1321条原始倒车命令出现在首段参考向前时，V863为0；不足以断言唯一根因。18旧实测响应留出验证中ARX2角误差至.106rad，拟合被拒绝，没有部署。然后保留原Nav2 MPPI优化器与评分器，把参考挡位、实际曲率与速度范围放到候选积分/评分之前，并实测速度初始化，过滤后的完整车身轨迹再查碰撞。上游预测函数固定复现55000个曲率不合法未来状态，同一投影消除；112万随机采样和18入口/独立审计正负例通过。真实7节点/完整地图/ARM与连续新扫描10条最终非零命令的软件演练通过。启动链接消息库、延迟twist依赖和固定tick夹具问题都保留，未在物理运行后修补。

## 本轮直接停止原因

参考出现倒行首段，MPPI重置后最后原始命令v=-0.000986058847m/s、w=-0.000747014245rad/s。它满足曲率1/1.32，却落入真实低层abs(v)<.005的停车死区，此时非零角速度不具备原生可执行语义。生产twist_contract按原门拒绝，ROS停、车辆完成2秒停车；不是物理碰撞或本轮计算超时。610条控制器诊断只有最后1条违反死区；609条已接受最终命令全部原生与重放已审核。实际最终被拒Twist在校验前未留存，精确向量不追认；最后原始控制器与cmd_vel_nav保存值能够独立复现同错误。软件资格遗漏了倒行切换后的低速输出，这是本版资格的明确缺口。

本轮MPPI计算p99约41.54ms、最大45.49ms，原生最大墙钟滞后3.12ms；这是该单任务实测，不是普遍实时性证明。更新后的方向投影没有证明完整到达；后续仍须检验跟踪误差和停转过渡。

## 下一候选必须满足的条件

1. 将真实低层停车死区同时纳入候选控制、预测状态和SG过滤后整条控制序列，完整轨迹重新核验后才输出；不能在已核验命令之后偷偷裁剪角速度。
2. 对真实保存的前进→倒行切换及接近停车命令做生产链回归，覆盖速度0、±.005边界、加速度/曲率/挡位和最终输出前日志；所有合法非零角速度命令都必须能由实际Adapter执行。
3. 冻结后新的静态主与重复通过才动态；该候选已关闭，不本轮补跑。即使名义MPPI基线成功，RP-CCR方法仍须在相同控制器骨架中单独接入并做配对对照、消融、未用确认集、计算预算与实机验证。

本轮是名义成熟导航基线适配，未部署旧RP-CCR全周期不确定性安全合同，不用论文成功案例替代自身验收；不声称RAS创新或24项通过。原截止与所有旧失败保持。

保存反例：
```json
{
  "models": 0,
  "integrations": 0,
  "all_diagnostics": 610,
  "all_curvature_checks_pass": true,
  "actuator_deadband_violations": [
    {
      "index": 609,
      "row": {
        "received_at": 108071.465115146,
        "gear": -1,
        "projected_samples": 45807,
        "v": -0.0009860588470473886,
        "w": -0.0007470142445527017,
        "compute_s": 0.002792574,
        "final_full_trajectory_collision_checked": true,
        "samples": 56
      },
      "error": "ValueError('IN_PLACE_ROTATION_NOT_NATIVE_REPRESENTABLE')"
    }
  ],
  "valid_saved_final_commands": 609,
  "saved_controller_commands": 610,
  "rejected_final_twist_not_logged_exactly": true,
  "last_raw_controller_command_reproduces_same_rejection": true,
  "actual_total_travel_m": 1.3307311650403815,
  "compute_p50_s": 0.0311178425,
  "compute_p99_s": 0.04153894989999999,
  "prototype_deadband_counterexample_output": [
    0.0,
    0.0
  ],
  "prototype_is_deployed": false,
  "qualification_scope": "One saved failure reproduced against actual production contract. Not a repaired navigation qualification or unique cause of all historical failures."
}
```
