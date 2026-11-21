# V1437 同一90min阶段时间分账

新writer/control/peer准备均不等于整路准入。原V1436当前limits保留5400s根窗，但normal动作只留600s收尾，同时ROS关闭120+Allocator120+自身replay300+recorded audit240+repeat pair240等独立上限之和超过600；原check又对ACTUAL_STOP_TAIL使用相同截止，使正常预算耗尽后不能用已预留200个实际动作施加完整停尾。这是精确工程阶段分账缺口，不改安全/来源/控制/方法或科学修订5，旧源/资格保持。

新source首先明确共享阶段上界：normal4140、完整零尾120、peer关闭120、Allocator120、自身fullstate replay300、recorded audit240、完整repeat pair240、元数据保存60，共5340s，剩余60s根保护；同一main/repeat各独立<=5400，根截止不延。每阶段双钟/boot/累计已用时间及实际phase记录，200尾和模型解析/物理/重算/重放分别沿原限额，不借时间阶段重置native/state/reference/snapshot。

下一必须把阶段guard实际接当前lifecycle/ROSwall/stop-reserve权限/独立审核与supervisor，normal cutoff不能阻止专门stop期，也不能通过抬normal或改200ms来源门让过期动作执行。stop只使用同一当前snapshot/剩余原预算，一次固定参考不重锚；各阶段仍受5400与根截止。当前仅生产phase helper AST与预算metadata，未资格/未SOURCE_FREEZE/未准入，不启动模型/车辆。
