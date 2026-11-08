# V892单actor动态开发

状态：NOT_PASSED。原三路线静态通过，控制核心精确V884，新增因果运动占据和有限等待恢复；本轮用户新批90分钟，绝对截止UNIX=1794148640.83449，旧批截止/失败保持。

动态导航尝试1，条件导航未执行1；新24/比较/消融/训练/实机均未执行。

|任务|通过|实际原生|自身重放|末距目标m|
|---|---|---|---|---|
|main_we|False|7720|7720|3.5235387408672207|

main_we 独立审核：{"evidence_passed": true, "functional_passed": false, "discovery": {"native_tick": 4516, "sim_time": 45.159999999999584, "xy": [0.020499576055951187, -0.6600020895739517], "rays": [31], "source": "actual physical sensor return and corrupted range; offline-only actor attribution"}, "independently_recomputed_postdiscovery_travel_m": 0.9260404584975424, "minimum_clearance_m": 0.26903534531169215, "bad_contacts": 0, "maximum_state_error": 0.0, "reference_updates_after_detection": 8, "successful_routes_after_detection": 8, "original_dynamic_actor_configuration": true, "independent_recorded_actor_motion": true}

None表示未知/未完成，不填0。t0环境初始化/内部编译加载与导航/自身重放分账，私有预测0。

真实原量程发现后实际续行>=1m、之后有周期参考更新、ROS成功/目标<=.45并实际停稳<=.03，以及全部原生.15/自体/合法ctrl/静态固定/自身状态接触重放和原100ms/200ms/250ms门均必须。周期更新不冒称由发现事件触发。

本轮是单小actor有限Nav2动态开发，不是新24确认、原RP-CCR328安全合同或RAS创新/算法优势证明。原观测里程计直接来自仿真真实状态，实机估计尚未接入。异步完整重复不要求两轨迹逐位相同，但每次自身完整控制重放须<=1e-8。

闭批REVIEW_PENDING原字节恢复/锁空闲；必要原件远端大小digest/下载SHA/实际成员恢复核验后才清缓存，旧同步不重试，2GiB临时上限。
