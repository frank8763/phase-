# MK-mini Phase

Phase 导航研究的唯一整理版，独立于 Stage。用户已审阅迁移并授权静态未知障碍开发，目标期刊为RAS。V650独立确认13项11到达2未到达，按预定规则停止、未通过。修订29已救回两个失败任务并保留困难场景到达能力，三项开发审计通过；正在转入新池V652确认，静态稳定性仍未验收，动态未开始。完整结果、失败与边界以报告为准。

[迁移完成报告](MIGRATION_REPORT.md)列出了保留内容、实际清理量、校验结果和未清理的环境文件。

本仓库将最完整的历史基线证据、冻结控制器和当前研究接力状态合成一份可检查的成果包。没有证据支持把 V647 或某个单场景成功版本认定为通用最优算法。

| 入口 | 内容 |
|---|---|
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
| [当前确认协议](experiments/v652_static_confirmation/PROTOCOL.md) | 冻结开发配置与有界协议；实际输出仅在 `runs/` |

只读准备检查：

```bash
./run_phase.sh
```

上述入口核对文件、导入依赖及加载冻结模型，不创建环境实例、不 reset、不执行 MuJoCo step、不训练。用户授权后已移除本轮 `REVIEW_PENDING`；实际仿真必须通过隔离入口并遵守实验协议。

聊天接力来源：[phase继续推进10.30](https://chatgpt.com/share/6ae54f9f-2730-83e8-8ae6-10b45198db16)。仓库保留核对后的研究摘要，不复制冗长聊天和附件占位内容。

