# V703 零积分初始化栈诊断

一次独立诊断捕获了旧初始化中的耗时规划链，未重开V702，也没有执行新导航、预测、重放或训练。旧V702前3项预检通过、第4超时及全部12导航未执行保持；新4任务成功率与触发率未评估。

同99010004、原相位，继续复用冻结factory，只在隔离进程内将mj_step/mj_step1/mj_step2全部替换成执行前拒绝函数，保持REVIEW_PENDING。每5秒全线程栈采样多次显示：Phase21 reset依据风险调用_phase21_v3_build_detour，进入adaptive_runtime_safe.plan、几何净空/路径加密、Hermite回退，随后进入cluster B样条采样。真实8m场地此时还未由arena.prepare构建。这是同输入重建观察，不是原V702被终止进程的栈；不能声称知道原进程最后一条指令。

源码确认旧reset在风险触发时会主动建detour，而当前run_static第35行先调用initialize，第42行才将phase21_v3_enable_detour设False，关闭得太晚。这给出具体的入口耦合原因：实际8m实验尚未开始，却付出了旧场地规划成本。它不说明新动态场地物理不可行，也不是RP-CCR新算法已失败。

本次诊断本身有明确局限：46.238秒退出1，最后RESULT.json写出被旧输出guard拒绝，RESULT缺失；没有重跑或伪造成功。初始阶段日志/5秒调用栈/完整异常/父进程COMPLETION均保留，初始化最终是否返回不能从缺失结果追认。析构阶段另有EGL错误，发生于诊断结束后的清理，不能反推为原V702超时原因。新增积分严格为0；原冻结6808输入和诊断冻结源码不变。

修复方向已经具体：在新独立初始化实现中，在旧reset之前关闭不需要的风险绕行分支，或直接构造固定8m场地；不得修改冻结runtime/current。随后先复核真实模型/规范初态/原始噪声与调用计数，FULL与原到达、SHADOW与原非到达全状态/控制/接触等价，再另立有界协议继续原99010001–04，不替换第4项。不能只加长超时或换种子。未来诊断应把结构化输出写到旧guard允许的子根，并先打印结果，保留本次写出失败。

本轮仅完成证据定位与修复设计，尚未实施/验证新初始化；没有自动重启V702或追加导航。[原停止报告](RPCCR_PROSPECTIVE_COMPUTE_V702_REPORT.md)，[诊断源协议](../experiments/v703_bootstrap_trace/PROTOCOL.md)，[全证据](../evidence/rpccr_bootstrap_trace_v703_20261102/README.md)。所有栈中旧绝对路径均按Phase隔离挂载映射到本仓库runtime；未读取Stage或旧混合工作区。
