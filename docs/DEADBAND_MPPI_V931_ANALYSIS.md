# V931 死区修订后的完整静态验证

**NOT_PASSED**。原西向东静态主任务180秒未到达，完整2秒停车后结束。原18,202实际原生和18,202完整自身重放、私有0；最低实际净空0.253464156米，坏接触0，qpos/qvel/ctrl/mocap与接触重放误差0。静态重复、动态主、动态重复3项未执行，新24未执行，不报确认成功率。

## 修复验证与剩余故障

原V929低于.005m/s但带角速度的换挡命令，在生产C++反例先失败；V931将停车死区同时放入候选预测、SG后整控制序列和已选择控制历史。112万候选、7个浮点边界、2240个真实上游SG输出、19生产入口/审计正负例和真实Nav2旧保存body/scan及前进→倒行两实际参考40次输出演练通过，均0车辆模型。物理运行后3274个MPPI输出全部符合死区，3271条最终命令均在校验前完整留存并被接受，原直接拒绝缺口已修复。不能把修复这个异常当作导航到达。

本次实际累计行走4.076542米、倒行0.912993米，最终距原目标5.793154米，最好5.769074米。149次规划发布中85条原始路径首有效段倒行；控制器随参考发生108次挡位切换、3274次输出中1123次为倒行挡。平均期望纵向速度.012814m/s、实际.012097m/s，期望纵向速度积分2.332369米、实际2.201874米：纵向执行总体跟随了缓慢且正反交替的请求，不能简单归因为“车辆前进命令完全跟不上”。转向请求与实际yaw-rate RMSE .051496rad/s，仍有动态失配，但没有建立唯一因果结论。

108次切换中99次在新参考发布前后150毫秒内；85条首倒行参考的倒行前缀中位长度.179110米、最大.569587米，不能把它们全称为浮点小段或一律删除。这是时间关联，尚非唯一因果证明。

这说明首要下一问题是全局重规划/局部路径裁剪、换挡和控制历史的连续性。需要确认哪些短倒行段是实际可执行恢复、哪些是随新参考重置产生的来回；保持已可执行参考直到明确失效或完成真实换挡，再用同一固定轨迹做反证。不能无证禁倒车、跳过曲率/净空门或仅加长回合。原RPP静态成功可作为成熟同平台基准，不能拿它的成功替代本候选到达。

MPPI计算中位2.79ms、p99 87.69ms、最大139.14ms；存在超过20Hz的慢调用，不能宣称稳定实时。原生最大墙钟滞后5.38ms，没有触发100ms模型时序门，当前直接停止是180秒功能截止，而非本轮计算超时异常。

## 原独立审核失败与零模型补核

原物理、接触、完整控制重放、startup和计时门均PASS；附加命令复核原失败原样保留，整批evidence_passed=false、passed=false。原因：冻结原生命令复核只从外部stop报文重建STOPPING，遗漏原生循环自己180秒限时停车。实际18002–18004三步已经本地零控制，外部stop在native_count18004后才接收，原复核因此错误期待上一条运动控制。独立零模型补核使用已保存receive计时区间和原冻结源码的180秒条件，区间未跨边界、18,202条控制全数匹配；篡改停车控制负例被拒。补核不覆盖原失败，也不把未到达改成PASS；下一版须显式记录本地状态转换并覆盖此边界。

## 窗口与结论范围

用户明确授权新独立90分钟，2026-11-09 16:10:21.030515至17:40:21.030515+0800；本候选首功能失败提前封账，不用剩余时间克隆修补或重跑。原V929及所有旧失败/截止不变。REVIEW_PENDING原字节恢复、执行锁空闲、当前指针闭合。无新24、训练、实机或Stage访问。

本轮为名义成熟导航基线，没有旧RP-CCR不确定性/全周期安全保证，尚未进入新动态验收或算法比较。完整新原始证据与准备失败及负例保存同仓Release，下载解压SHA全回读后清临时缓存。

详细零模型补核与计数：
```json
{
  "status": "NOT_PASSED",
  "models_in_analysis": 0,
  "integrations_in_analysis": 0,
  "actual_native": 18202,
  "own_replay_native": 18202,
  "private_native": 0,
  "minimum_clearance_m": 0.2534641556061852,
  "bad_contacts": 0,
  "goal_distance_m": 5.793154342194745,
  "actual_travel_m": 4.076541771549647,
  "best_goal_m": 5.7690736482765,
  "controller_records": 3274,
  "controller_gear_flips": 108,
  "controller_reverse_records": 1123,
  "gear_flips_within_150ms_of_new_plan": 99,
  "raw_reverse_prefix_length_m": {
    "minimum": 0.012739333126962937,
    "median": 0.17910999928949353,
    "maximum": 0.5695868518484694
  },
  "plan_count": 149,
  "raw_path_first_reverse_count": 85,
  "desired_v_mean_m_s": 0.01281380834160873,
  "measured_v_mean_m_s": 0.012096876950457802,
  "desired_v_integral_m": 2.3323693943396213,
  "measured_v_integral_m": 2.2018735425223293,
  "actual_reverse_travel_m": 0.9129930429407249,
  "desired_reverse_native_ticks": 5181,
  "actual_reverse_native_ticks": 5311,
  "zero_desired_ticks": 1747,
  "desired_w_rmse_actual": 0.051496047596554795,
  "mppi_compute_s": {
    "p50": 0.0027853195000000002,
    "p99": 0.08769425976,
    "maximum": 0.139143914
  },
  "maximum_native_wall_lag_s": 0.005383771989727393,
  "deadband_output_contract_passed": true,
  "all_final_twists_logged_before_validation": true,
  "original_independent_audit_passed": false,
  "original_evidence_passed": false,
  "all_original_physical_checks_passed": true,
  "original_ingress_failure_preserved": true,
  "deadline_only_stop_native_ticks": [
    18002,
    18003,
    18004
  ],
  "supplemental_local_deadline_ingress_reconstruction": {
    "passed": true,
    "all_native_rows": 18202,
    "first_local_deadline_tick": 18002,
    "source_deadline_from_arm_s": 180,
    "local_receive_interval_unambiguous": true,
    "local_stop_before_external_stop_ticks": [
      18002
    ],
    "original_frozen_ingress_verdict_overwritten": false
  },
  "supplemental_control_tamper_negative_passed": true,
  "arrival_passed": false,
  "unexecuted_navigation": 3,
  "new24": "UNEXECUTED",
  "scope": "Deadband defect fixed; static functional deadline failure remains. Supplement explains 3 local STOPPING rows, never retroactively changes original failed batch or proves arrival."
}
```

补充相关性计数初次JSON写出因NumPy int64失败，0模型、原补充归档保留；显式int规范化后重新写出并以独立更正归档追加，原物理审核与功能失败不变。
