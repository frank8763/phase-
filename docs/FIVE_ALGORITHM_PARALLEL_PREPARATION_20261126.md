# 五算法准备与并行组件验收 · 2026-11-26

更新：2026-11-26T14:34:35.873614+08:00。本轮新增验证均不含Phase车辆模型、物理步、重放、训练或正式任务。CPU7与CPU2同时实际执行组件，CPU6保留MPPI。Stage保留核未使用。

| 方法 | 本轮实际进展 | 尚需完成 |
|---|---|---|
| PRIEST | 原作者当前归档t0求解通过：1构造、1优化、12CEM，16.80s；固定110batch/13projection/seed0 | 当前共享控制律、完整5+2200响应、原车capture/replay独审 |
| PSF | CPU2硬约束过滤LP的可行/不可行接口验收通过 | 原Phase非线性模型、名义控制器、误差界、终端不变集与实车仿真接口 |
| PCBF | CPU2软约束辅助问题+性能过滤两阶段验收通过 | 原2023终端barrier/收紧与恢复条件的Phase适配；不得软化实际安全门 |
| SVG-MPPI | 已有8000采样原作者与当前控制接口资格按SHA保留 | 原车完整停车、全状态重放、独立审核；倒车适用性仍未资格 |
| SCCR | 原版输入依赖清单确认：186维中50维camera/depth未提供 | 相同传感合同兼容性；不以零填充、mask或真值冒充原版 |

PSF/PCBF本轮共8性能LP+4辅助LP，残差独立核验，0.264s；标量线性夹具不是Phase动力学，也不借用论文全车保证。五方法正式60slot均未启动。

PRIEST求解返回的是参考多项式，并非执行器命令。额外1001时间点纯数学读出：t0零速切向奇异，949非奇异点超过参考speed.1或curvature1/1.32范围，最大参考speed0.397111；原响应策略首6点preview命令[0.08959019416365194, 0.049774141827173185, False]通过原twist域，但并不代表后续轨迹/车辆响应/停车安全通过。未裁剪、重调seed或重跑优化器。该晚补分析仅本地，未声称位于已闭runtime归档。

源码16815成员；Git新源51e280b3；新建Release单POST不确定失败原件保留、不重POST。改用已有Phase证据集合Release458985230，明确其target为c42d4346，不能误称其旧Git包含新源。新源41members/111251B、runtime70members/123704B全部实际远端asset/member/whole/indexSHA回读与精确duplicate清理/组件barrier闭。集合映射单列COLLECTION_DELIVERY_SUPPLEMENT。

MPPI第10项7455actual/replay、独审/重放通过、完整停车预测拒绝/未whole到达，全remote/barrier与派生duplicate retirement闭。第11项原parent在claim前因16MiBmetadata拒，未数算法失败；新parent仅将约1.21MiB由已结束RPP的空闲metadata16MiB涵盖，原两lane合计32MiB/15GiB/joint16095019008保持，索引与anchors不删、全部数值源不改。现在11首次CPU6child1425973/start31424344真实运行，12尚未claim。当前正式账{'denominator': 120, 'registered': 59, 'closed': 58, 'unexecuted': 61, 'qualified_success': 7}。

原协议见[PROTOCOL](../experiments/v2064_five_algorithm_parallel_math/PROTOCOL.md)，组件证据见[实时检查](../runs/v2064_five_algorithm_parallel_math/FIVE_METHOD_LIVE_STATUS.json)。
