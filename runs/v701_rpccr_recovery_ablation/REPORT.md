# V701 RP-CCR恢复续接机制诊断

收尾2026-11-02T17:03:57.973340+08:00，证据终审状态 **MECHANISM_DIAGNOSTIC_EVIDENCE_COMPLETE**；这是诊断完整性，不能读作机制优越PASS。原V700原清单24/24有限课程结果与原V698 NOT_PASSED均保持。

选择原24项中最先实际触发中途续接的两个旧案例slot14/20，FULL与COMPLETE_TAIL成对，另重复COMPLETE_TAIL各一次。最多6执行，未执行[]。0新独立确认任务、0训练；车辆/传感/噪声/安全不变，实际计算分别记录。FULL额外续接预测工作不能隐藏或当作同实际计算收益。不是完整RP-CCR净收益或泛化证明。

| 执行 | 模式 | 结果 | 公开步 | 后备步 | 路径m | 目标退步累计m | 私有积分 | 全部物理证据 |
|---|---|---|---|---|---|---|---|---|
| full14 | FULL | GOAL | 811 | 12 | 9.860587804013536 | 0.18382020407389277 | 3750512 | True |
| tail14 | COMPLETE_TAIL | NO_SAFE_PROGRESS_PATH_WITHOUT_RETAINED_RECOVERY | 335 | 40 | 3.4095961170926623 | 0.18423348196106204 | 1270144 | True |
| full20 | FULL | GOAL | 809 | 24 | 9.838803767901808 | 0.13690231562742117 | 3663616 | True |
| tail20 | COMPLETE_TAIL | NO_SAFE_PROGRESS_PATH_WITHOUT_RETAINED_RECOVERY | 355 | 40 | 3.5919920132617076 | 0.13730138711897055 | 1343680 | True |
| tail14_repeat | COMPLETE_TAIL | NO_SAFE_PROGRESS_PATH_WITHOUT_RETAINED_RECOVERY | 335 | 40 | 3.4095961170926623 | 0.18423348196106204 | 1270144 | True |
| tail20_repeat | COMPLETE_TAIL | NO_SAFE_PROGRESS_PATH_WITHOUT_RETAINED_RECOVERY | 355 | 40 | 3.5919920132617076 | 0.13730138711897055 | 1343680 | True |

## 成对差异

slot14：COMPLETE_TAIL − FULL：公开步-476、路径-6.450992m、目标退步累计0.000413m、后备步28、私有积分-2480368；首次物理差异307，FULL首次成功续接307，之前前缀一致True。
slot20：COMPLETE_TAIL − FULL：公开步-454、路径-6.246812m、目标退步累计0.000399m、后备步16、私有积分-2319936；首次物理差异339，FULL首次成功续接339，之前前缀一致True。

所有原生安全/控制/自体/因果覆盖/发现停车/状态重放/尾证书门及前缀与完整重复结果见[独立终审](../runs/v701_rpccr_recovery_ablation/FINAL_INDEPENDENT_AUDIT.json)。候选更差/相同/不达均保留，不调参救回。两FULL应与原V700基准完全一致；两消融重复功能结果和完整状态/控制/接触必须一致，否则诊断不完整。

导航原生24000、重放24000、私有12641776为已知账目；精确性分别True/True/True，未知不填0。窗口1298.409s，上限7200s，不重置。全部原始证据保留，收尾新增积分0。

局限：已观察机制活跃的两个旧任务、固定空白8m/单慢速actor/公共3m起步先验；需独立新任务、计算预算控制和强基线，才评价方法收益。未证明任意遮挡突入、复杂场地、概率校准、实时性、递归可行或无限安全。协议[PROTOCOL](../experiments/v701_rpccr_recovery_ablation/PROTOCOL.md)，[全证据](../evidence/rpccr_recovery_ablation_v701_20261102/README.md)。闭批停止并待用户审阅，不自动再跑新机制或更长距离。
