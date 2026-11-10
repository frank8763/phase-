# V974白天单项：模块绑定与西向东动态整路

结果：**NOT_PASSED**；单次原WE10010001/相位.6573753567727383动态180秒+2秒停车，窗口硬截止1794278552.1031067，实际关闭1794273246.8350868。
本轮最多90分钟、只此一主；没有自动重复、三路线、24确认或通宵。用户要求白天逐项推进，夜间另安排。旧08:00窗口和所有失败保持。

## 昨晚实际发生的事

V971在2026-11-09 22:57:17提前关闭。原完整WE执行18201原生、完整自身控制重放18201，私有0，距目标8.001964m；3600发令全为零，0条计划/0非零Nav2命令。149规划请求每次ValueError（expected2而实供3），不是走到最后两米或计算超时。坏接触0、最低实际.314989m、状态重放通过，不等于动态功能通过。其余任务和24未执行。
快速零模型复现直接运行实际worker懒导入及实际planner协程，确认规划端选中V891两字段旧代理，物理端选中V881旧factory，缺少预期V958适配器和原精确传感绑定。V971原审核因缺EXACT_SENSOR_BINDING文件失败，原失败不追认。先前预目标/FollowPath组件资格未覆盖真实NavigateToPose全局代理，也未覆盖实际native懒导入；这是本轮工程检查遗漏。

## 本轮改动与资格

以仓库内受SHA核验的本地别名固定V968科学模块；规划包装器使用原三字段原子快照，已知接口异常立即停止，真实NO_PATH/几何拒绝门不改。原生factory明确委托原V968/V959/V958，并在真实t0核验控制compute源文件、适配器SHA、转向编码器和EXACT_SENSOR_BINDING，未通过禁止第一步积分。
同两复现从红变绿；真实factory guard用明确无模型夹具接受正确源，拒绝昨晚真实坏SETUP及积分后绑定。参数、模型、19静态体/小actor/传感噪声、控制安全门与原RP-CCR科学函数不改。
真实安装Nav2的NavigateToPose→Smac→RPP→安全准入软件演练通过：3规划/59条获证非零前进。合成运动学peer，0模型/0物理积分，不能当实际动态通过。首软件演练管理服务35秒未响应，0模型，原记录保留；第二次增加服务调用/响应诊断后成功（STARTUP响应约2.233秒），没有延长启动门或证明该偶发超时唯一原因、实时可靠性。

## 新旧积分分账

V974新主：实际8038，自身控制重放8038，私有0，距目标2.9903467000926223m，最低实际0.2730365667394967m，坏接触0。
功能通过False，证据通过False，独立总门False。
原生错误：None。审核错误：AssertionError('ACTUAL_REFERENCE_TRACKING_ENVELOPE_FAILED')。闭批原因：{'error': "AssertionError('SINGLE_ROUTE_FUNCTION_SAFETY_OR_EVIDENCE_FAILURE')", 'traceback': 'Traceback (most recent call last):\n  File "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v974_daytime_binding_gate/campaign.py", line 20, in main\n    assert rc==0,\'SINGLE_ROUTE_FUNCTION_SAFETY_OR_EVIDENCE_FAILURE\'\nAssertionError: SINGLE_ROUTE_FUNCTION_SAFETY_OR_EVIDENCE_FAILURE\n'}。
旧V971的18201/18201与旧V968组件2794/2794、旧18响应全部独立，不混本轮一主或新24分母。

## 范围与收尾

原逐原生.15净空/完整自体与接触未知0/合法ctrl与速率/静态体固定/无积分外根写/完整状态控制重放≤1e−8保留；原.155准入、非反向.02/.035经验管、.2s命令+2s刹停、50ms新权限/200ms expiry/100Hz100ms门不变。必须真实行驶测距发现—原因果参考—发现后实际续行>=1m—目标<=.45并实际停稳。全生效恢复参考仍独立.04/.035跟踪审核。
发现前较弱反应式合同/3m起步排除先验、单.08m/s且.32周期小actor条件明示；不恢复旧328定理，不是任意遮挡/多actor/地图/实时/递归安全/RAS保证。一主成功也不是24动态验收。训练/SAC/实机0，Stage隔离。
模型授权关闭、原guard恢复、锁空闲、全部源SHA核验。今天此项结束后停下复盘，不自动通宵。必要新证据与昨晚失败记录分组归档，同仓库Release下载/memberSHA核验后按清单清理；新批唯一30秒push/5秒HEAD核验，失败保留必要缓存，不循环重试。
