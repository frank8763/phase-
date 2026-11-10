# V979：冻结V977的有界物理验证

结果：**NOT_PASSED**。原V974失败及旧窗口保持，不是三路线/新24验收。

顺序为两个原保存状态恢复组件，全通过才原西向东主与条件完整重复。任一功能/安全/证据异常即停；唯一90分钟模型截止不延长。
历史前缀通过原body commands真实积分恢复，并逐原生比对完整状态/控制；与新分支、完整自身控制重放分账。未知不填0。

| 任务 | 尝试 | 通过 | 历史恢复积分 | 新分支积分 | 完整轨迹重放 |
|---|---:|---:|---:|---:|---:|
| component_0 | True | False | None | None | None |
| component_1 | False | False | 0 | 0 | 0 |
| main_we | False | False | 0 | 0 | 0 |
| repeat_we | False | False | 0 | 0 | 0 |

停止原因：`{'error': "AssertionError('FIRST_FUNCTION_SAFETY_SOURCE_STATE_CONTROL_OR_EVIDENCE_FAILURE component_0')", 'traceback': 'Traceback (most recent call last):\n  File "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v979_state_recovery_physical/campaign.py", line 33, in main\n    assert row[\'passed\'],\'FIRST_FUNCTION_SAFETY_SOURCE_STATE_CONTROL_OR_EVIDENCE_FAILURE \'+task[\'task_id\']\nAssertionError: FIRST_FUNCTION_SAFETY_SOURCE_STATE_CONTROL_OR_EVIDENCE_FAILURE component_0\n'}`

全部训练/SAC/实体机0，Stage隔离；current/runtime/冻结网络不改。组件的ARM起点明确为原全局native/time，不冒称全局t0；没有车身根或时钟改写。完整动态链只由整路实际发现、实际续行>=1m、目标<=.45与停稳/全来源独立审核判定。
重复沿原Nav2合同：同规范物理模型/初态与配置、两个完整链均过、各自全状态控制重放<=1e-8；异步完整轨迹可能不同，不能声称逐轨迹确定性。
新保存态入口准备期同步构造阻塞观测、恢复历史缺初始发布时钟两项零模型错误保留，均在物理前修复；V977科学源字节不变。
闭批恢复REVIEW_PENDING、模型授权关闭；没有自动三路线/24/通宵/新候选。必要证据远端SHA回读前保留，单次push/5秒远端核验失败不重试。

## 闭批后零模型补核（原失败不改判）

原6083步历史恢复逐状态/控制误差0已由PREFIX_RESTORE证明。新恢复至少116原生步，精确总数与完整自身控制重放数未知；完整NATIVE_TRACE/BODY_COMMANDS/CONTACTS/REPLAY未落盘，不能声称全程接触或安全审核通过。原最终表的null保留，独立补核见POSTMORTEM_ACCOUNTING.json。

首次实际错误为ONLINE_RECOVERY_HEADING_ENVELOPE_FAILED：故障位置样本最近粗参考航向差0.030355rad，加原在线0.004742采样余量=0.035097449>0.035；同保存曲线0.5mm重建后，故障位置航向差0.031439rad+0.000190余量=0.031629<0.035。该采样余量可解释本次保守拒绝，不能据此声称实际已超2度，也不能从一个故障位置推断完整后续可通过。

25个发令决策均无备选运动替换；记录还显示修正角速度已正、实测车身角速度仍约−0.05rad/s，存在实际转向响应滞后，单点数据不足以隔离机械/纵向差动/跟踪各自贡献。下一应先核验相同误差门下的密采样判定和实际转向瞬态，不能只缩采样余量后盲跑整路。

另有独立执行流程问题：ROS首次失败后父进程终止整个native进程组，isolate/bwrap的die-with-parent使原生finally未完整落盘。后续入口必须先让停止/证据序列在原截止内闭合，未知计数如实保留。冻结V979不修补、不重跑、不延时；V980仅保存资料分析，新增模型积分0。
