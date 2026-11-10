# V987：冻结V984后轮偏航反馈的两状态物理验证

结果：**NOT_PASSED**。原V974失败及旧窗口保持，不是三路线/新24验收。

只验证两个原保存状态恢复组件，不启动整路或重复。任一功能/安全/证据异常即停；唯一90分钟模型截止不延长。
历史前缀通过原body commands真实积分恢复，并逐原生比对完整状态/控制；与新分支、完整自身控制重放分账。未知不填0。

| 任务 | 尝试 | 通过 | 历史恢复积分 | 新分支积分 | 完整轨迹重放 |
|---|---:|---:|---:|---:|---:|
| component_0 | True | False | 6083 | 348 | 6431 |
| component_1 | False | False | 0 | 0 | 0 |

停止原因：`{'error': "AssertionError('FIRST_FUNCTION_SAFETY_SOURCE_STATE_CONTROL_OR_EVIDENCE_FAILURE component_0')", 'traceback': 'Traceback (most recent call last):\n  File "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v987_bounded_startup_components/campaign.py", line 38, in main\n    assert row[\'passed\'],\'FIRST_FUNCTION_SAFETY_SOURCE_STATE_CONTROL_OR_EVIDENCE_FAILURE \'+task[\'task_id\']\nAssertionError: FIRST_FUNCTION_SAFETY_SOURCE_STATE_CONTROL_OR_EVIDENCE_FAILURE component_0\n'}`

全部训练/SAC/实体机0，Stage隔离；current/runtime/冻结网络不改。组件的ARM起点明确为原全局native/time，不冒称全局t0；没有车身根或时钟改写。完整动态链只由整路实际发现、实际续行>=1m、目标<=.45与停稳/全来源独立审核判定。
本批只有两个固定恢复组件，不包含完整导航、导航重复或独立确认样本；即使两组件通过也不称动态整路验收。
V981精细在线检查和独立终审使用原参考/原门限；V987准备期旧authority导入顺序错误在模型前保留并修正；V977参考与准入保持；历史恢复用原V958，原保存起点才切换V984后轮反馈，新增独立混合控制重建与完整历史比对。
闭批恢复REVIEW_PENDING、模型授权关闭；没有自动三路线/24/通宵/新候选。必要证据远端SHA回读前保留，单次push/5秒远端核验失败不重试。

## 原生保存响应补核

本轮13:35:22启动、13:36:34首项停止，第二项未执行。启动与历史恢复61.032秒后正常ARM，实际新控制348步。直接错误为`ONLINE_RECOVERY_HEADING_ENVELOPE_FAILED`，不是本轮启动超时。故障在原生6229（新分支146）；完整新轨迹含停车尾独立最大航向误差.041172rad，超过原.035；位置误差.002658m，实际走.047866m。原最低净空.273037m/坏接触0。

新增电机控制独立重建误差2.22e-16、117步偏航反馈实际启用、6083历史状态与6431完整控制重放误差均0。运行最大墙钟滞后.003294秒、最大观测龄.038504秒，原门通过；备选运动控制接管0。说明新反馈确已正确下发，但单独后轮反馈仍不足以通过此状态的航向与完整停车跟踪合同。缺少CLOSED_HANDOFF是提前失败后的不完整功能证据，不能将部分控制/安全审核通过冒充组件通过。V987保持NOT_PASSED，无冻结后修补、无重启或追加模型。补核为0模型/0积分，原轨迹保留于同仓库Release。
