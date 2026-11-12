# MK-mini Phase · RP-CCR

本仓库是Phase导航研究的唯一工作区，目标期刊为Robotics and Autonomous Systems；与Stage完全隔离。

**当前：V1082已失败封账，物理后台关闭，完整动态验收未完成。**

- [当前控制链与下一工作面](docs/PHASE_NAVIGATION_CURRENT.md)
- [从静态成功到当前失败的完整复盘](docs/PHASE_NAVIGATION_FULL_REVIEW_20261112.md)
- [精简机器状态](CURRENT_EXPERIMENT.json)
- [逐版本历史状态](RESEARCH_STATUS.md)

旧静态V657确认23/24、旧动态V827三路线开发、V828已执行8项中6成功、Nav2 V884–885同版本三路线静态、V1056原西东单主成功分别保留各自合同，不能拼接成当前版本的动态验收率。

当前最近的3555步续行使用保存的完整输入请求和单一轮控执行者；没有运行Nav2 ROS动作，也没有用SAC决定该完整路线。最新失败为新增单步速度限幅和执行器速率约束失去可行交集；原超速失败和全部历史证据保留。

## 使用与记录

唯一仓库：`/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-`；远端：[frank8763/phase-](https://github.com/frank8763/phase-.git)。

`./run_phase.sh`无参数只执行离线只读准备检查，0仿真/0训练。实际模型入口受冻结协议、独立窗口、单实例锁和REVIEW_PENDING保护；当前不自动启动物理。

必要源码/报告/索引存Git，必要原生证据存同仓Release，远端SHA与解压回读通过后才清理；[记录存储规则](docs/STORAGE_POLICY.md)。旧源码的硬编码依赖仍保留用于复现，不作为并行活动分支。

完整旧首页无损保存在[历史首页](docs/history/README_BEFORE_NAVIGATION_REVIEW_20261112.md)；原433KB机器状态无损保存在[历史状态](records/navigation_review_20261112/CURRENT_EXPERIMENT_HISTORY.json)。
