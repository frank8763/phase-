# 论文证据核查与下一步 · 2026-11-26

最新进展 · 2026-11-26 15:39：SVG V2079独立当前原车接口已CLOSED PASS，10正常控制+完整2200停车、2210自身重放、最大fullstate/ctrl/mocap误差0/contactmismatch0，原独审PASS/最小实际净空0.310208074m。原V2073技术失败保留；V2080锁文件遗漏在once/child/factory前退出0models，原失败父记录保留。新source16907/sole2cd1e3fc及runtime140members6619513B均实际远端逐项SHA核验和精确运输清理闭。该接口测试不构成全任务到达，正式SVG仍0/12。

持续输入通道V2083已完成真实OutputBoundary/实际child软件字节验证与pending、ACK、size、count、owner等拒例，0新solver/model/physics。原12个SVG任务已绑定为草案，下一步需完成持久优化器、连续实测控制和全任务审核/存储资格，不能逐步重建优化器改变RNG或warmstart，也不能把当前接口成功当正式12项准入。当前没有后台Phase数值运行。

原账核查快照：2026-11-26T15:09:27.984293+08:00。本报告来自保存的原始结果和逐文件SHA，0模型、0优化、0物理、0重放；不替代独立安全审核。

最新闭轮补充：2026-11-26T15:16:37.046388+08:00。MPPI最后一项已完成全部审核、远端核验和最终存储收尾，现有5种方法各12/12 closed，共60closed/120原分母，完整到达合计7。MPPI结果0whole/11有效有限拒绝/1技术故障。原15:09快照保留，最终补充见FINAL_MPPI_SUPPLEMENT.json。

SVG V2073自动接续后在创建stdin匿名可写管道时触发原输出边界UNBOUND_WRITABLE_DESCRIPTOR：200actual/200replay均为安全收尾、normal0，整车组件未通过。旧失败、200步独审和远端runtime/barrier已闭，不能算算法性能拒绝或正式任务。此前管道测试漏测实际OutputBoundary环境；V2078已补原环境红复现及正规配额输入文件只读stdin绿检查，原越界/rawdescriptor保护保持。修复仅software通过，尚未进入新source/车辆验收，当前无后台Phase数值运行。

## 一、对照公平性：已核实的内容与必须披露的差异

60个已注册任务的17个科学字段与原锁定任务表一致，包括课程、相位、seed、起终点、原生步上限和2200停车尾段。保存的同任务live-scene身份未发现冲突。该结论不等于所有适配和计算预算完全公平。

| 方法 | 论文中应使用的实际身份 | 已确认的适配/限制 |
|---|---|---|
| DWA | 固定PythonRobotics参考实现 + Phase Ackermann动作筛选 | forward限制0.08；public静态点和当前32ray；原完整停车门 |
| TEB | 固定原HCP核心 + 已披露车辆/后轴/点图接口 | forward限制0.08；原饱和移植；不以额外曲率裁剪救命令 |
| RPP | 固定Nav2核心的ExecutableRPP工程适配 | 速度±0.1、低速deadband、角速度投影与1.5s碰撞复核；实际lookahead 0.6/0.3/0.9 |
| MPPI | 固定Nav2核心的coherent/deadband工程适配 | batch1000、56步×0.05s、iteration1、速度±0.1、Ackermann1.32；共享公共路径/因果costmap |

上述不是“各原论文算法未修改复现”的比较。共同任务字段相同不代表相同方法车速或相同搜索预算；原task.speed字段也不能代替控制器速度配置。完整modelwork/internalfactory未知，不声明equalwork、实时性或CPU/GPU整体加速优势。初始冻结registry中的历史简写不能替代实际已资格源码/二进制/参数SHA；原字节保留，论文另列实际身份。

技术/证据故障单列，原120分母与全部失败保留。RPP有10个gear首错，其中只有9项达到有效有限拒绝分类；不能只按首错字符串将第10项也算有效算法负结果。未执行SCCR/PSF/PCBF等不能写0%成功率。

## 二、RP-CCR为什么成功、在哪里失败

| 课程方向 | 完整到达 | 有效有限拒绝 | 技术/证据故障 |
|---|---:|---:|---:|
| WEST_EAST | 2 | 1 | 1 |
| NORTH_SOUTH | 3 | 0 | 1 |
| EAST_WEST | 2 | 1 | 1 |

| 案例 | 分类 | 最终目标距离m | 观察到的边界 |
|---|---|---:|---|
| common_01 | VALID_FINITE_REFUSAL | 3.035434 | AssertionError('NO_CURRENT_WHOLE_GOAL_SOURCE') |
| common_02 | TECHNICAL_CENSOR | 未知 | FileNotFoundError(2, 'No such file or directory') |
| common_03 | WHOLE_ARRIVAL | 0.269328 | 原目标、停车和独立审核完成 |
| common_04 | WHOLE_ARRIVAL | 0.246003 | 原目标、停车和独立审核完成 |
| common_05 | TECHNICAL_CENSOR | 3.229532 | AssertionError('BASELINE_DID_NOT_EXHAUST_FIXED_WORK_NO_FALLBACK') |
| common_06 | WHOLE_ARRIVAL | 0.138239 | 原目标、停车和独立审核完成 |
| common_07 | WHOLE_ARRIVAL | 0.259392 | 原目标、停车和独立审核完成 |
| common_08 | WHOLE_ARRIVAL | 0.118363 | 原目标、停车和独立审核完成 |
| common_09 | TECHNICAL_CENSOR | 0.044368 | AssertionError('BYTE_GRANT_EXHAUSTED') |
| common_10 | WHOLE_ARRIVAL | 0.052870 | 原目标、停车和独立审核完成 |
| common_11 | VALID_FINITE_REFUSAL | 3.720710 | AssertionError('FIRST_DISCOVERY_NOT_NORMAL_DRIVING') |
| common_12 | WHOLE_ARRIVAL | 0.038949 | 原目标、停车和独立审核完成 |

保存的成功分支可描述为：WE03/04先refuge_onward再direct；NS06/07/08走当前状态保留平衡候选fallback；EW10/12记录了有效feedback-goal完成。它们证明这些冻结系统分支在对应相位完成任务，不能单独证明onward预检或时间选择带来增益。

两个科学拒绝分别是common01有限搜索没有找到当前全目标source，及common11首次发现不处于原要求的normal-driving阶段。它们既不是碰撞证据，也不是全局无解证明。common09虽距目标0.044m，仍有BYTE_GRANT_EXHAUSTED证据故障，保持非成功；near-goal不能代替完整到达与审核。

## 三、可靠性和机制收益：缺口与执行次序

目前可靠性未建立：原12共同任务有7次合格到达、2次有效功能拒绝、3次技术/证据故障。不得把后两类删掉而改写成功率。现有结果仅涵盖已知课程新相位、单actor与固定运动类。

独立20项消融已经闭账：8次合格到达，12次非成功；有一项原步数未知。完整成功且可干净比较的WE04和EW12对照轨迹相同；EW12没有进入时间窗选择分支。尚未观察到机制收益，不将“机制没激活”解释成一般无用。

接下来按以下顺序推进：

1. MPPI末项全部闭轮已完成。SVG V2073原车组件技术失败和完整证据已闭；V2078软件修复已验证，后续需单独新source与资源准入，再做新的接口验收，旧失败不覆写或当作方法拒绝。组件通过后才准备完整12项资格与冻结。PRIEST继续fresh-current求解与完整5+2200车辆响应。
2. 为每个新方法逐一完成输入权限、车辆接口、参数身份和整车安全验收，固定后执行原未运行slot；SCCR原深度输入不兼容、PSF/PCBF终端模型缺口保持显式，不能用伪造输入或线性夹具替代。
3. 对RP-CCR两个真实功能边界先做保存决策链分析，提出有限开发假设；如需新候选，另立版本和开发协议，不修改或重跑旧冻结案例。
4. 最终方法与参数稳定后，先登记新的确认队列及工程验收指标，再冻结、恢复源码和运行；新确认与旧开发、共同12项、消融20项分别计数。该报告没有启动或挑选新确认seed。
5. 机制实验先固定激活定义、记录字段及合格配对条件；需要“实际激活且完整证据可比”，再判断是否有差异。新相位设计不得根据成功结果筛选；不为了阳性重跑旧失败或调安全门。

论文可先撰写问题定义、冻结系统、接口适配、合同、共同任务方法、结果分层和失败边界；可靠性、机制收益与泛化结论暂不写成已证实。

证据：`runs/v2077_paper_evidence_review/RESULT.json` 与 `BRANCH_AND_ADAPTATION_REVIEW.json`。初次报表method-list字段类型错误保留为READOUT_INITIAL_ERROR.json，修正仅报表解析，0模型/正式任务。晚补文档和代码在606e70aa及已闭SVG sourcearchive之后，不能声称已由旧Release/Git覆盖。
