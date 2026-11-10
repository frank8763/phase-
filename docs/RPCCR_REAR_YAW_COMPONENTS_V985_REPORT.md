# V985：冻结V984后轮偏航反馈的两状态物理验证

结果：**NOT_PASSED**。原V974失败及旧窗口保持，不是三路线/新24验收。

只验证两个原保存状态恢复组件，不启动整路或重复。任一功能/安全/证据异常即停；唯一90分钟模型截止不延长。
历史前缀通过原body commands真实积分恢复，并逐原生比对完整状态/控制；与新分支、完整自身控制重放分账。未知不填0。

| 任务 | 尝试 | 通过 | 历史恢复积分 | 新分支积分 | 完整轨迹重放 |
|---|---:|---:|---:|---:|---:|
| component_0 | True | False | 6083 | 0 | 6083 |
| component_1 | False | False | 0 | 0 | 0 |

停止原因：`{'error': "AssertionError('FIRST_FUNCTION_SAFETY_SOURCE_STATE_CONTROL_OR_EVIDENCE_FAILURE component_0')", 'traceback': 'Traceback (most recent call last):\n  File "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v985_rear_yaw_components/campaign.py", line 33, in main\n    assert row[\'passed\'],\'FIRST_FUNCTION_SAFETY_SOURCE_STATE_CONTROL_OR_EVIDENCE_FAILURE \'+task[\'task_id\']\nAssertionError: FIRST_FUNCTION_SAFETY_SOURCE_STATE_CONTROL_OR_EVIDENCE_FAILURE component_0\n'}`

全部训练/SAC/实体机0，Stage隔离；current/runtime/冻结网络不改。组件的ARM起点明确为原全局native/time，不冒称全局t0；没有车身根或时钟改写。完整动态链只由整路实际发现、实际续行>=1m、目标<=.45与停稳/全来源独立审核判定。
本批只有两个固定恢复组件，不包含完整导航、导航重复或独立确认样本；即使两组件通过也不称动态整路验收。
V981精细在线检查和独立终审使用原参考/原门限；旧V982准备期authority导入顺序错误仍保留；V985本次直接停止原因为启动恢复超时；V977参考与准入保持；历史恢复用原V958，原保存起点才切换V984后轮反馈，新增独立混合控制重建与完整历史比对。
闭批恢复REVIEW_PENDING、模型授权关闭；没有自动三路线/24/通宵/新候选。必要证据远端SHA回读前保留，单次push/5秒远端核验失败不重试。

## 2026-11-10保存证据补充诊断

父进程在120秒恢复等待上限发出`CANONICAL_STATE_RESTORE_TIMEOUT`；实际工厂初始化和6083步原历史恢复共129.176秒，原生READY晚于STOP9.547秒。控制器切换成功，但ARM未发生、ROS未启动、新反馈控制积分为0。原错误/NOT_PASSED保持，缺少ROS结果及零新行数审核错误为后续现象，不能据此评判V984反馈效果。原历史状态/控制与完整重放误差均0。下一轮先统一各层启动与收尾预算，并覆盖慢恢复与根截止负例，再按新有界授权测试同两状态；不修改算法或物理安全门。本次补核模型/积分0，详见[启动诊断与下一实验](RPCCR_V985_DIAGNOSIS_AND_NEXT_PLAN.md)。
