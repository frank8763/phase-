# V701恢复续接机制诊断当前接续

用户明确继续实验，新独立窗口2026-11-02T16:41:41.632736+08:00至2026-11-02T18:41:41.632736+08:00，单一7200秒绝对积分截止1793616101，不得延长/重置。master475233，外层475232。旧V700课程24/24与原V698 NOT_PASSED及所有截止/失败保持不改。

固定顺序FULL14、COMPLETE_TAIL14、FULL20、COMPLETE_TAIL20、条件COMPLETE_TAIL14完整重复、条件COMPLETE_TAIL20完整重复，共最多6导航。原14/20是24任务中最先触发CERTIFIED_RETURN的两个已观察案例，非新独立确认。FULL须逐公开qpos/qvel/ctrl/mocap与原V700基准<=1e-8、模型/初态/真实接触/发现事件一致，否则停依赖。消融仅关闭中途try_return，仍完整执行旧安全尾、之后按原程序规划。消融非到达是有效负结果，不能调参救回；但任何安全/源/模型/真值/控制/状态/覆盖/证据异常立即停。完整重复也必须相同功能结果、轨迹长度、状态/控制/接触/模型/初态一致。

本轮只看ROUND_WINDOW.json、ablation01/ACTIVE/RESULTS/COMPLETION/ERROR、FINALIZED及当前任务partial_progress；输出均runs/v701_rpccr_recovery_ablation，控制台runs/v701_driver.console。运行中不改冻结py/md/json/任务/模型/阈值、不再启动第二实例。全部实际积分run_phase.sh单CPU顺序，训练/SAC/Stage/实机0。完全隔离Stage，不访问其任何内容或进程，不发外部消息、不建新聊天/子代理，原始证据不删。

驱动会自动finalize_ablation.py零积分收尾；FINAL_INDEPENDENT_AUDIT的MECHANISM_DIAGNOSTIC_EVIDENCE_COMPLETE只是证据完整，不是机制优越PASS。最终报告docs/RPCCR_RECOVERY_ABLATION_V701_REPORT.md，全证据evidence/rpccr_recovery_ablation_v701_20261102。若已闭批finalizer异常，先确认无同一finalizer再仅零仿真修收尾，禁止重启导航/覆盖旧COMPLETION/重复刷动作。已有归档只能核验不覆盖。硬截止之后仅零积分收尾。

最终明确已执行/未执行/成功/非到达/未知积分，FULL精确参照、消融完整重复和首次分叉不早于首成功续接；报告两边实际私有积分/墙钟，不能把FULL更多预测隐藏为同实际计算优势。闭批恢复REVIEW_PENDING；审阅本仓库差异、提交必要报告/代码/全证据，最多一次30秒push及5秒只读核验，不循环。成功/失败/截止收尾后删除该临时接续，不追加新机制/距离/池/训练。例行健康进度保持安静，仅完成、有意义失败/异常或需要用户操作时通知。

## FINAL CLOSED
六执行和独立审计/全部归档回读完成；两FULL到达，两消融完整尾后停止、完整重复误差0。仅局部机制诊断，非全面优越PASS。REVIEW_PENDING已恢复，phase-v701已删除，不再启动模拟。最终人工解释见docs/RPCCR_RECOVERY_ABLATION_V701_REPORT.md与RPCCR_RECOVERY_ABLATION_CLOSED_20261102.json。
