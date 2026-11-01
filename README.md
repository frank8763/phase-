# MK-mini Phase

Phase 导航研究的唯一整理版，独立于 Stage，目标期刊为RAS。**V657预注册有限静态基准工程验收已通过**：新冻结24项23严格到达（单12/12、双11/12），三场景完整重复误差0，27项物理审计与独立重算通过。1项HORIZON失败明确保留，旧失败不改写。用户已审阅并授权动态开发；动态仍未稳定验收，SAC训练更新0。

[迁移完成报告](MIGRATION_REPORT.md)列出了保留内容、实际清理量、校验结果和未清理的环境文件。

本仓库将最完整的历史基线证据、冻结控制器和当前研究接力状态合成一份可检查的成果包。没有证据支持把 V647 或某个单场景成功版本认定为通用最优算法。

| 入口 | 内容 |
|---|---|
| [最新动态验证：V683–V685](docs/DYNAMIC_INFO_VALIDATION_V683_REPORT.md) | 准确当前信息仍未到达；候选修正未过前置；末端18拒绝全部来自动态外覆盖 |
| [动态根因彻底复核：V682](docs/DYNAMIC_ROOT_CAUSE_V682.md) | 804帧零积分重查：运动假设、估计保守性、局部倒车进展和墙钟停止 |
| [最新动态实验：V679–V681](docs/DYNAMIC_FORWARD_RESERVE_V679_REPORT.md) | 前进有限尾有局部增量，804步仍未到达；短时空间提案前置失败未导航 |
| [下一时序内核规格](docs/DYNAMIC_TEMPORAL_KERNEL_DESIGN.md) | 完整状态、绝对时间、合法命令与保留尾段；尚未实现/运行 |
| [V676–V678命令与场景分解](docs/DYNAMIC_COMMAND_SCENE_V676_REPORT.md) | 命令修复、两因果未到达、同场景特权474步到达见证，分母明确 |
| [算法还是场景：原文核对](docs/DYNAMIC_ALGORITHM_VS_SCENE_V676.md) | 有限观测与时序规划、SIPP-IP/不确定性学习原文及适用边界 |
| [V674–V675续接实验与审计](docs/DYNAMIC_RENEWABLE_BACKUP_V674_REPORT.md) | V674/V675两未到达、次优漏选实证、实际命令契约失败与全账目 |
| [后备相关工作与创新边界](docs/DYNAMIC_BACKUP_RELATED_WORK_V674.md) | gatekeeper直接重叠、适用假设及尚缺的论文增量 |
| [下一阶段规格](docs/DYNAMIC_TEMPORAL_EXECUTION_NEXT.md) | 先统一执行器命令并在线核验，再研究时序/真实动力学一致性；未执行 |
| [V671–V673动态结构实验报告](docs/DYNAMIC_STRUCTURE_V673_REPORT.md) | V671原因分解、V672/V673两未到达、有限后备末端缺口与真实积分审计 |
| [扩展原论文核对](docs/DYNAMIC_LITERATURE_FAILURE_ANALYSIS_V671.md) | 部分闭环观测、时序等待、路线一致性与预测安全策略；读取范围明确 |
| [V670动态开发报告](docs/DYNAMIC_EMPTY_SAMPLES_V670_REPORT.md) | V670未命中连续约束、843步超时未到达、完整前缀核验与信息表示诊断 |
| [公平验证设计](docs/DYNAMIC_EVALUATION_DESIGN.md) | 未执行的强基线、机制消融、新池与计算预算要求 |
| [V669动态恢复报告](docs/DYNAMIC_RECOVERY_V669_REPORT.md) | 三候选未到达、首次命中消融、实际有限倒车制动与信息退化 |
| [动态相关工作与设计](docs/DYNAMIC_LITERATURE_DESIGN.md) | 原始文献、增量边界、下一研究问题 |
| [方法草稿](docs/PHASE_DYNAMIC_METHOD_DRAFT.md) | 实际实现、条件性分析及尚未证明的活性 |
| [动态测距集合与规划诊断](docs/DYNAMIC_INTERVAL_DEVELOPMENT_REPORT.md) | V662精确测距回放、V663观测消融与V664有界开发 |
| [RAS当前创新评估](docs/RAS_READINESS_ASSESSMENT.md) | 投稿目标、现有不足与需要验证的方法贡献 |
| [动态首轮开发报告](docs/DYNAMIC_UNKNOWN_DEVELOPMENT_REPORT.md) | 三条未到达分支、预测漏覆盖与完整失败证据 |
| [最新静态稳定验收报告](docs/STATIC_ACCEPTANCE_V657_REPORT.md) | V657新池23/24、三次完整重复、全部物理审计与原失败 |
| [固定清单完整记录](docs/STATIC_SAME_LIST_ACCEPTANCE_REPORT.md) | 23/24导航、原复现未通过、完整证据与目录诊断 |
| [静态修复报告](docs/STATIC_REPAIR_REPORT.md) | 原因分析、两个失败配对救回、困难回归与修订29边界 |
| [V650静态确认报告](docs/STATIC_ACCEPTANCE_REPORT.md) | 11到达2失败、完整物理审计与预定提前停止 |
| [静态稳定化报告](docs/STATIC_STABILITY_REPORT.md) | 当前多开发场景结果、几何审计与未通过的稳定门槛 |
| [上一轮静态未知障碍报告](docs/STATIC_UNKNOWN_REPORT.md) | 单场景成功、同状态地图消融与限制 |
| [RAS论文路线](docs/PAPER_PLAN_RAS.md) | 相关工作、主张边界与后续验证 |
| [研究状态](RESEARCH_STATUS.md) | 已完成、未通过与待验证的内容 |
| [迁移说明](MIGRATION.md) | 本地唯一目录、依赖隔离、清理边界和验证方法 |
| [精选证据](evidence/README.md) | Final300、必要对照、已复现救援、V647 实际结果 |
| [当前实验指针](CURRENT_EXPERIMENT.json) | 选定的开发候选与证据边界 |
| `current/` | 字节不变的V647历史接力与环境依赖，新实验使用上面的独立入口 |
| `runtime/` | 必需的冻结环境、控制器、模型、状态与资源 |
| `manifests/` | 原始来源、逐文件 SHA256、清理明细与验证结果 |
| [静态确认冻结协议](experiments/v657_static_fixed_work_confirmation/PROTOCOL.md) | 冻结开发配置与有界协议；实际输出仅在 `runs/` |

只读准备检查：

```bash
./run_phase.sh
```

上述入口核对文件、导入依赖及加载冻结模型，不创建环境实例、不 reset、不执行 MuJoCo step、不训练。静态验收已通过，用户已审阅并继续授权动态开发；具体运行以当前指针和独立有界协议为准，不能自动追加无界实验。

聊天接力来源：[phase继续推进10.30](https://chatgpt.com/share/6ae54f9f-2730-83e8-8ae6-10b45198db16)。仓库保留核对后的研究摘要，不复制冗长聊天和附件占位内容。

