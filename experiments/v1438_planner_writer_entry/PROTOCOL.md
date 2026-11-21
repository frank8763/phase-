# V1438 真实planner worker输出边界

继承已闭V1437阶段源（仅零模型阶段/关闭门资格通过，不是实际生命周期），科学修订5、原任务WE10060001/原RPP.6/.1、所有源时效/控制/安全/固定参考/全200尾/全程门不变。V1437所有已测源只读不重刷。

源审明确一个尚未准入的实际缺口：PlanningJob给子进程传PLANNER角色，但route_worker.py直接main，未进入entry_boundary，故结果Path.write_text/replace并未扣独立PLANNER8MiB。环境变量不构成覆盖证明，任何旧complete coverage断言均不存在。新fork只把生产worker main接同一bounded entry，不改原FFI规划调用/原地图/原控制算法或预算。首次必要资格必须实际走PlanningJob→CPU4真实只读FFI planner→当前结果tmp/replace writer计数，不复刷旧IO/control/modelpeer fixture。只允许原WE起点/原公共map的一个明确软件请求，不是当前wire、不发布scan、0模型/积分/车辆/实际replay。

同时native save源由本机MuJoCo头文件mj_sizeModel/mj_saveModel定义核对；先按真实C模型二进制大小收费，再核已写file size。此source审查不调用MuJoCo/不构造模型，不能冒称C save已实际执行。实际canonical initializer全路径仍待准入，不把一个planner门当全部writer覆盖。

当前仅生产draft/AST，未资格/未SOURCE_FREEZE/无完整准入/ROUND_WINDOW/LAUNCH。软件planner资格authority必须modelsfalse/parent idle/PLANNER coverage false，不能伪造production activation registry真值。总task224MiB/全部runs10GiB+archive224MiB+download32MiB+root512MiB照实预留，源码新worker写一旦异常资格关批并保留首错/未执行，不重刷。
