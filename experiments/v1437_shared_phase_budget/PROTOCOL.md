# V1437 同一90min阶段时间分账

新writer/control/peer准备均不等于整路准入。原V1436当前limits保留5400s根窗，但normal动作只留600s收尾，同时ROS关闭120+Allocator120+自身replay300+recorded audit240+repeat pair240等独立上限之和超过600；原check又对ACTUAL_STOP_TAIL使用相同截止，使正常预算耗尽后不能用已预留200个实际动作施加完整停尾。这是精确工程阶段分账缺口，不改安全/来源/控制/方法或科学修订5，旧源/资格保持。

新source首先明确共享阶段上界：normal4140、完整零尾120、peer关闭120、Allocator120、自身fullstate replay300、recorded audit240、完整repeat pair240、元数据保存60，共5340s，剩余60s根保护；同一main/repeat各独立<=5400，根截止不延。每阶段双钟/boot/累计已用时间及实际phase记录，200尾和模型解析/物理/重算/重放分别沿原限额，不借时间阶段重置native/state/reference/snapshot。

下一必须把阶段guard实际接当前lifecycle/ROSwall/stop-reserve权限/独立审核与supervisor，normal cutoff不能阻止专门stop期，也不能通过抬normal或改200ms来源门让过期动作执行。stop只使用同一当前snapshot/剩余原预算，一次固定参考不重锚；各阶段仍受5400与根截止。当前仅生产phase helper AST与预算metadata，未资格/未SOURCE_FREEZE/未准入，不启动模型/车辆。

生产接入现已写出，详见PREPARATION_CHECKPOINT02；以上“下一必须接入”已由源码完成。仍仅AST、未资格/未冻结，native/ROS/审计生命周期不能据此launch。必须先源复核及一次必要phase-path零模型资格，不重复旧I/O或peer夹具。

唯一新phase入口资格：CPU2/run_phase/单锁/原writeguard/profile禁Predictor/Allocator构造step/compute，最多90s，0模型/解析积分/物理/实际replay/ROS节点。直接执行当前PhaseRuntime/NativePhaseGate、软件过去normal截止到已预留stop权限、仅clock字段绑定/阻止新事务、8阶段handoff、双钟/boot/重入和次保存错误保首错；真实Unix datagram Pump.close只测新关闭flag，ROS complete receipt明确软件文件输入。没有实际wire/证书/数组/新scan，不能作为actual生命周期或车辆准入。源审补根alarm在写receipt时保持、异常后rootalarm恢复、关闭receipt要求无保存gap。成功或失败都一次闭批/source SHA冻结不重刷。
