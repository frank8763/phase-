# V1423 统一实际native/ROS绑定及完整记录审核

沿科学整合修订5，不新加修订。只把已冻结V1422新事件/owner和V1421真实命令泵/lifecycle绑定为同一当前生产源，新增每一个实际native步之前精确budget回调，不依赖outer check0。记录实际完整source packet/全state SHA和证书后source_checked_monotonic，让独立审核可重建200ms门；记录真实wire envelope和所有before/applied receipt，原物理/控制/误差/尾/参考门不改。

新集成独立审核读取完整INITIAL_FULL_STATE+N已施加state、全部prefix与事件journal、每current reserve完整200数组/proof、固定响应参考/因果输入与RPP来源，检查N动作/N+1状态和完整全程门。几何/来源/接触/覆盖/全状态pair是无模型审核CPU5；独立Allocator控制重算单独run_phase CPU2/锁/准确计数，实际MuJoCo全state own replay仍在CPU2原路径。任何缺文件/漏行/不明计数拒绝，不以FINALIZED/exit0替代科学通过。

本准备只真实CPU2入口/profile禁止模型/原guard与集成依赖源码资格，不运行旧物理或完整模型；新增audit source不能拿旧schema报告直接PASS。实际socket/模型peer namespace/跨模式与审核数组资格、严格goal/coverage/fullstate replay/pair、精确整路预算/全部runs10GiB运输峰值/一次启动supervisor仍须补齐，尚无完整准入文件，不启动模型或车辆。
