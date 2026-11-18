# MK-mini Phase · RP-CCR

本仓库是Phase导航研究的唯一工作区，目标期刊为Robotics and Autonomous Systems；与Stage完全隔离。

**当前：V1281已完成固定课程动态验收，24/24主任务及3次完整重复全门通过，后台已关闭。**

- [本轮完整验收报告](docs/RPCCR_CAUSAL_TIME_WINDOW_FIXED24_V1281_REPORT.md)
- [GitHub证据备份与按需恢复](records/v1281_backup_20261118/README.md)

该24项池已经暴露，结果不代表未见泛化、实时或实机验证；正式多算法对照与消融尚未完成。V1286软件后续因写入守卫误拒/dev/null停止，原错误保留。

- [当前控制链与下一工作面](docs/PHASE_NAVIGATION_CURRENT.md)
- [从静态成功到当前失败的完整复盘](docs/PHASE_NAVIGATION_FULL_REVIEW_20261112.md)
- [精简机器状态](CURRENT_EXPERIMENT.json)
- [逐版本历史状态](RESEARCH_STATUS.md)

旧静态V657确认23/24、旧动态V827三路线开发、V828已执行8项中6成功、Nav2 V884–885同版本三路线静态、V1056原西东单主成功分别保留各自合同，不能拼接成当前版本的动态验收率。

V1281使用实际传感发现、实测停稳后的安全恢复入口、完整后续路线准入及因果等待窗，保留单一物理控制执行者。冻结SAC未用于本批完整路线决策，训练更新为0；本批不构成Nav2 ROS基线对照。V1082等原速度/控制失败与全部历史结论保留。

## 使用与记录

唯一仓库：`/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-`；远端：[frank8763/phase-](https://github.com/frank8763/phase-.git)。

`./run_phase.sh`无参数只执行离线只读准备检查，0仿真/0训练。实际模型入口受冻结协议、独立窗口、单实例锁和REVIEW_PENDING保护；当前不自动启动物理。

必要源码/报告/索引存Git，必要原生证据存同仓Release，远端SHA与解压回读通过后才清理；[记录存储规则](docs/STORAGE_POLICY.md)。旧源码的硬编码依赖仍保留用于复现，不作为并行活动分支。

完整旧首页无损保存在[历史首页](docs/history/README_BEFORE_NAVIGATION_REVIEW_20261112.md)；原433KB机器状态无损保存在[历史状态](records/navigation_review_20261112/CURRENT_EXPERIMENT_HISTORY.json)。
