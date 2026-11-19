# 2026-11-18 offline baseline relay

Closed: EVIDENCE_OR_OPERATION_STOP. Original hard stop2026-11-19 09:00+0800;10GiB. Frozen branch sources, no automatic tuning.

|Task|Result|Actual native|Own replay|Goal distance|
|---|---|---:|---:|---:|
|rpp_causal_default_static_main|PASSED|9190|9190|0.3905153568767649|
|rpp_causal_default_static_repeat|PASSED|9195|9195|0.39051535524721187|
|rpp_causal_default_dynamic_main|EVIDENCE_OR_OPERATION_STOP|4705|4705|4.125266368281245|

Unexecuted: rpp_causal_default_dynamic_repeat, rpp_causal_preview_static_main, rpp_causal_preview_static_repeat, rpp_causal_preview_dynamic_main, rpp_causal_preview_dynamic_repeat, rpp_causal_slow_static_main, rpp_causal_slow_static_repeat, rpp_causal_slow_dynamic_main, rpp_causal_slow_dynamic_repeat, coherent_mppi_causal_static_main, coherent_mppi_causal_static_repeat, coherent_mppi_causal_dynamic_main, coherent_mppi_causal_dynamic_repeat

One exposedWE course percontroller; repeats not independent samples. Dynamic task uses causal publicmap/range occupancy and renewed exactfootprintlattice proposals pluslocalcontroller; no hiddenactortruth orRPCCRglobal guarantee. This is finite engineering development, not fixed24/newgeneralization/real-time or algorithm-superiority evidence. PriorRPCCRV1281fixed24success unchanged. Complete ownstate/control/contact replay and all audit gates required for each reported pass. Unknown counts explicitly retained.

Raw originals kept; this offline archive has local SHA verification only. No network needed for the run. GitHub transport/remoteSHA/restore before any cleanup.

## 2026-11-19晨间独立检查

原批11月18日22:18:31提前闭批，22:18:33本地归档完成；未持续通宵，不称09:00正常完成。两静态任务分别9190/9195实际＋相同自身重放，全审核通过，重复长度不同不视作独立任务或精确轨迹重复。动态4705实际＋4705完整自身重放，误差0，最低实际.250033155/坏接触0；4475真实actor返回，发现后仅续行.0445908m即原地停住，最终距目标4.125266m，功能失败。尾200请求实际为0且车体停稳，但不是正常COMPLETE_STOP_TAIL阶段完成，原该审核假保持，不追认全门。合计23090实际/23090重放精确，规范Vehicle3次内部构造未知。其余13任务未执行。

主错误是native观测socket.sendto的TimeoutError。保存源显示ROS在同一线程同步propose进行搜索，期间不能收取datagram；native给sendto设置20ms超时，异常列表未包含TimeoutError。零模型真实AF_UNIX队列测试在接收端不读取时重现发送超时（约20ms），原handler不捕获。说明调度通信缺陷足以导致本次中断；不是这批再次触及15cm安全门，也不能说新动态路线已实际通过。详细见MORNING_CHECK_20261119.json及COMMUNICATION_REPRO_20261119.json。

下一修订需规划与I/O解耦，有限队列/最新观测策略、观测年龄与过期指令拒绝保持；停车心跳不被规划阻塞，规划超时不无限延长。先对同生产边界做拥塞/长规划/失联/根截止/完整保存注入资格，再另批有限物理，不重启原已关闭夜窗。当前7330冻结SHA不变、guard原字节恢复、锁空闲、无后台，raw和本地归档均保留；远端备份待完成，不删唯一证据。此次仅检查/零模型诊断。
