# 静态未知障碍开发证据 · 2026-10-31

当前报告：[STATIC_UNKNOWN_REPORT.md](../../docs/STATIC_UNKNOWN_REPORT.md)。在线候选源码已按 [DECISION_FREEZE.json](../../experiments/v648_static_unknown/DECISION_FREEZE.json) 冻结；仍属开发原型。

- `trial_ledger.json` 包含所有开发运行目录、结果/协议、初始化拒绝、主动中止、外部中断、探针和源码映射。不同版本、重复和场景不能合并为独立成功率。
- `selected/` 保留首个成功/重复及固定配置地图消融的完整接触、物理步摘要、公开状态、轨迹和规划输入输出，同时保留必要的失败对照。JSON/JSONL压缩后内容不改，接触日志原始压缩文件直接保存。
- `source_blobs/<sha256>.py` 对每次运行的源码快照去重；按该运行 `source_hashes` 的文件名和哈希可重建源目录。它们是历史证据，不是多个活动实验入口。
- `diagnostics/` 与 `figures/` 保存因果观测地图/评价真值的离线连通诊断，以及仅含机器人和地面的转向/制动响应探针。正连通不是连续SE(2)或动力学可达证明，评价真值不进入控制器。
- `map_counterexamples/` 保存旧点云积累的必要反例；新回波删失性质由独立合成测量检查支持，不把同期多项代码变化当单机制消融。
- `MANIFEST.json` 记录本包各文件的SHA256。原始迁移文件的旧哈希清单保持不变。

`initial_scene.xml` 为reset生成的XML；t0物体激活/关闭/位置以同运行的STATIC_PROTOCOL与sensor_geometry_sync为准。仅凭XML不能重建运行期模型状态。

同状态重复只验证可重复性；多帧圆柱经验包络尚未校准，不能写成形式化风险保证。所有SAC训练更新为0，Stage从未进入本轮运行的隔离空间。
