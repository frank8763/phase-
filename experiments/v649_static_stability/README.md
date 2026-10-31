# V649 静态未知障碍稳定化

本目录是Phase当前静态开发代码，Stage完全隔离。先读[协议](PROTOCOL.md)、[方法边界](METHOD_NOTES.md)和[研究状态](../../RESEARCH_STATUS.md)。上一轮V648证据冻结保留。

当前开发配置以[CANDIDATE_FREEZE.json](CANDIDATE_FREEZE.json)的逐文件哈希为准；`geometry_memory`仍不是已通过稳定性验收的算法。不启动动态，不训练SAC。

- `run_static.py`：静态场景、因果感知、路径与轮控、原生接触与自体几何审计；每次必须给新的`--name`。
- `range_circle_memory.py`：量化射线/截断噪声下的局部有限圆柱假设，未校准连续参数覆盖。
- `geometry_predictor.py`、`self_geometry.py`：与实际关节限位一致的原生预测；每个预测状态包住所有自体几何，实际每个原生步检查覆盖。
- `planner.py`、`tracking.py`：正反向规划，优先/准入余量分离，停稳换挡。
- `run_batch.py`：主机有界顺序调度器；模拟器仍只通过`run_phase.sh`运行。不要与另一个批次并发执行。
- `check_*`：数值/几何/感知/换挡检查，不计独立导航结果。
- `audit_*`、`evaluate_*`、`crosscut_audit.py`：离线评价。带真值的输出禁止进入在线规划。
- `replay_native_audit.py`：离线控制日志物理重放，只有完整公开状态匹配后才接受重建净空；重放积分单独计数，不增加试验样本。
- `curate.py`、`verify_curated.py`：保留完整尝试账本、去重源码与精选证据。

只读准备检查：在仓库根目录执行`./run_phase.sh`。它不reset、不步进、不训练。

后续有界试验示例（执行前核对本窗口剩余预算及归档中未使用过的名称）：

```bash
./run_phase.sh experiments/v649_static_stability/run_static.py \
  --name UNIQUE_NEW_RUN_NAME --seed 91000002 --scene single_event \
  --conditions geometry_memory --wall-seconds 900
```

上面的命令会真实运行模拟器，不是准备检查。`DEVELOPMENT_NAVIGATION_*.json`是已经执行/中止过的计划记录，不能直接重跑覆盖。正式确认池93000001–93000060尚未执行；发现部分任务在当前包络约束下被几何封闭后，必须在查看确认导航结果前补好任务可行性定义，不能事后删除失败。
