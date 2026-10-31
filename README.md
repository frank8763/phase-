# MK-mini Phase

Phase 导航研究的唯一整理版，独立于 Stage，目标期刊为RAS。**V657预注册有限静态基准工程验收已通过**：新冻结24项23严格到达（单12/12、双11/12），三场景完整重复误差0，27项物理审计与独立重算通过。1项HORIZON失败明确保留，旧失败不改写。实验已停止，等待用户审阅；动态与训练未开始。

[迁移完成报告](MIGRATION_REPORT.md)列出了保留内容、实际清理量、校验结果和未清理的环境文件。

本仓库将最完整的历史基线证据、冻结控制器和当前研究接力状态合成一份可检查的成果包。没有证据支持把 V647 或某个单场景成功版本认定为通用最优算法。

| 入口 | 内容 |
|---|---|
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
| [当前确认协议](experiments/v657_static_fixed_work_confirmation/PROTOCOL.md) | 冻结开发配置与有界协议；实际输出仅在 `runs/` |

只读准备检查：

```bash
./run_phase.sh
```

上述入口核对文件、导入依赖及加载冻结模型，不创建环境实例、不 reset、不执行 MuJoCo step、不训练。静态验收已通过，`REVIEW_PENDING` 已恢复以等待用户审阅；零步只读检查照常可用，下一步实际仿真需用户明确继续。

聊天接力来源：[phase继续推进10.30](https://chatgpt.com/share/6ae54f9f-2730-83e8-8ae6-10b45198db16)。仓库保留核对后的研究摘要，不复制冗长聊天和附件占位内容。

