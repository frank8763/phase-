# V702新任务与计算对照接续

用户明确继续，独立窗口2026-11-02T17:49:09.927891+08:00至2026-11-02T20:49:09.927891+08:00，唯一绝对积分硬截止1793623749.9278908/10800秒不延长不重置；master486078外层486077。旧V701闭批/V700课程通过/V698原NOT_PASSED、所有旧失败和截止保持。

新4噪声99010001–04/连续相位正反各2一次锁定，不筛选是否触发续接。FULL与SHADOW_COMPLETE_TAIL都计算并核验原候选；FULL提交，影子只保存shadow_handover_certificates并继续旧安全尾，不能把影子算实际执行。共同前缀/首提交处须相同预测计数/候选证书；分叉后总计算和终点分别报告，不称等总计算效率或强基线。

先4零积分t0预检+原噪声独立复算，再旧slot14 FULL复现V701 FULL14与SHADOW复现原tail14物理轨迹/结果，锚点首307处计算/候选一致才进新任务。固定计划随后4新任务每条件一次（交替顺序）和task1两条件各完整重复，最多12实际执行；旧校准/重复不入新4分母。新任务功能不达也保留，不替补不调参；任意安全/源/模型/真值/状态/控制/覆盖/证据异常立即停；固定完整重复不一致停。

全部实际积分只run_phase.sh单CPU顺序单实例；所有原净空>=.15/坏接触0/完整自体/合法ctrl速率/无积分外根改写/全状态重放/329预测657规划/因果/路线/执行及影子全部尾几何审核不变。训练/SAC/Stage/实机0，current/runtime/旧模型不改。完全隔离Stage不访问任何内容/模型/输出/进程，不发外部消息、不建新聊天/子代理、不删除证据。

运行中只看ROUND_WINDOW/prospective01 ACTIVE/RESULTS/PREFLIGHTS/COMPLETION/ERROR、FINALIZED、当前任务partial_progress；代码experiments/v702_rpccr_prospective_compute，输出runs/v702_rpccr_prospective_compute，日志runs/v702_driver.console。冻结py/md/json/任务/算法/模型/截止均不编辑、不启动第二实例。驱动会自动finalize_prospective.py零积分收尾。只有FINAL_INDEPENDENT_AUDIT和全证据回读及FINALIZED才完成；PROSPECTIVE_COMPUTE_EVIDENCE_COMPLETE只是证据完整，不是优越PASS。已闭批finalizer异常时确认无同一finalizer，仅零积分诊断/收尾，不重启导航/延期/覆盖旧COMPLETION或已有归档；硬截止之后仅零仿真整理。

结束核对docs/RPCCR_PROSPECTIVE_COMPUTE_V702_REPORT.md、4新对/旧校准/固定重复分母、未执行/未知账目与影子计算单列。恢复REVIEW_PENDING，审阅差异提交科学源码/报告/元数据/完整证据，一次最多30秒push与5秒只读核验，不循环。完成/失败/截止收尾后删除临时接续，不自动再跑新机制/距离/场景/训练。常规进度保持安静，只通知有意义完成/失败/异常或需操作。

## FINAL CLOSED
V702预检slot4旧bootstrap超时已闭批/归档，前3预检通过，全部12导航未开始，成功率与触发率未评估。REVIEW_PENDING已恢复，phase-v702已删除，不延时/重跑/换种子；仅源码/日志定位到旧reset选点后、8m arena.prepare前，无停进程栈，具体根因未知。正式报告及RPCCR_PROSPECTIVE_COMPUTE_CLOSED_20261102.json为最新闭批信息。
