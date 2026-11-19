# 2026-11-19 strict expiry and evidence recovery

Closed: ALL_FROZEN_BRANCH_DEPENDENCIES_CLOSED. New root stops2026-11-19 17:00+0800 in ROUND_WINDOW;2GiB, all old deadlines unchanged. Frozen branch sources, no automatic tuning.

|Task|Result|Actual native|Own replay|Goal distance|
|---|---|---:|---:|---:|
|entry_static_static_main|PASSED|9195|9195|0.3905153553279037|
|entry_static_static_repeat|PASSED|9190|9190|0.39051535690410194|
|periodic_mode0_dynamic_main|FUNCTIONAL_FAILURE_SAFE_COMPLETE|20795|20795|1.4847286511483246|
|periodic_mode1_dynamic_main|FUNCTIONAL_FAILURE_SAFE_COMPLETE|29330|29330|2.020584633364578|

Unexecuted: periodic_mode0_dynamic_repeat, periodic_mode1_dynamic_repeat

New staticpair followed by two existing periodic-prior planner variants on one exposedWE course. V1356 original failures remain unchanged. Repeats not independent samples. Dynamic task uses causal publicmap/range occupancy and renewed exactfootprintlattice proposals pluslocalcontroller; no hiddenactortruth orRPCCRglobal guarantee. This is finite engineering development, not fixed24/newgeneralization/real-time or algorithm-superiority evidence. PriorRPCCRV1281fixed24success unchanged. Complete ownstate/control/contact replay and all audit gates required for each reported pass. Unknown counts explicitly retained.

Raw originals kept; this offline archive has local SHA verification only. No network needed for the run. GitHub transport/remoteSHA/restore before any cleanup.

New predictor conditions on .25m bounded excursion; PERIODIC also assumes .32rad/s and estimates unknown coefficients only from corrupted returns. This is stronger prior information than V1354 speed-only, not arbitrary-motion robustness. No actor anchor/axis/phase truth online. V1357 only rejects expired inputs to zero-body braking, preserves200ms gate and adds cooperative complete ROS evidence closure.

## 13:39检查补记（零模型）

本批2026-11-19 13:32:00闭合全部可执行依赖，当前无后台物理任务。静态main9195/ownreplay9195和repeat9190/ownreplay9190均全门通过；两动态main均安全完整功能失败，各自成功依赖repeat未执行。合计68510actual/68510完整ownreplay，未知计数0，坏接触0、最低净空约.250033m，全部适用来源/时戳/控制/证据/预测覆盖审核通过。FINALIZED只是本地归档及SHA回读通过，不是动态成功。

PERIODIC mode0动态20795actual/ownreplay20795，最终余1.484729m；末多次KNOWN_STATIC_RECOVERY_RESERVE触发，12次replan用尽。规划器mode0曾返回GLOBAL_GOAL_PATH标签却报告真实body目标距离.77m，说明旧rear-goal判定不能当作原body.45m到达；实际终审正确未计成功。mode1没有这个资格豁免。

PERIODIC mode1动态29330actual/ownreplay29330，最终余2.020585m；第10计划名义body目标距.248026m，原密集/实时几何门通过，但实际续行后重复CAUSAL_FUTURE_BALL_RESERVE，末起点START_BELOW_HARD_FLOOR，12次replan用尽。说明有名义完整路径仍不等于当前闭环能保持动态安全续行。不能仅靠增加重规划次数声称解决。

两动态任务FRESHNESS_REJECTIONS均0；本次没有触发真实过期拒绝，不能以此声称所有延迟问题已经解决。实际完整ROS_COMMANDS与增量日志一致/closed=True、所有投递与拒绝审核通过，原上批证据退出路径本次没有复现。旧V1356原失败及缺失日志结论保持。

本轮Git本地提交9c662219e1afd9383384369678b36d56364b8cae包含必要记录和验证分块；唯一30秒push超时，随后只读远端仍为旧aaf21e9，远端未确认。原始证据继续留存，本次只补充本地状态，不重试push、不开新模型、不延17:00硬截止。下一修订应优先解决名义目标判定、可执行尾段与动态恢复门一致性。
