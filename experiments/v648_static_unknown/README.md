# 静态未知障碍开发实验

用户授权：2026-10-31；目标期刊 RAS。完整预算及变更依据见 [PROTOCOL.md](PROTOCOL.md)。这是开发代码，不是已验收的论文算法。`current/` 和 `runtime/` 均保留原始字节。

## 任务与执行

通过仓库根目录 `./run_phase.sh experiments/v648_static_unknown/run_static.py ...` 执行。bubblewrap 隐藏 Stage 和旧工作区，仅 `runs/` 可写；CUDA 禁用，计算线程设为 1，每进程 900 秒硬限，单实例锁。Phase20/Phase6 不训练。

- `--seed`：冻结环境生成器的种子。所有已试种子均为开发数据。
- `--scene single_event`：初始时刻激活事件圆柱10；构建场景时关闭生成器原有未知圆柱9，具体变化写入协议，之后不再移动任何障碍。
- `--scene legacy_two`：保留原有未知圆柱9和事件10。前12版本之前的实验实际属于双障碍，不能与单障碍混合比较。
- `--conditions frozen_sac,memory`：固定先验路径的冻结SAC与原始因果点记忆恢复。同进程恢复全部模型、物理、Python和随机状态。
- `circle_memory,circle_repeat`：同一恢复控制器使用多帧圆柱估计，限定single_event，并明确使用单个静态圆柱形状先验。其经验表面余量未校准。
- `legacy_memory`：采用旧0.985R命中阈值；`no_memory`：只用当前观测点。未运行的条件不能写成消融结果。
- `--max-steps 1200`：96秒仿真导航上限。前10版本之前为600步，原截断结果不回填。

每次用新的 `--name`，不覆盖历史输出。例如：

```bash
./run_phase.sh experiments/v648_static_unknown/run_static.py \
  --name explicit_new_run_name --seed 91000004 --scene single_event \
  --conditions frozen_sac,circle_memory
```

此命令会实际运行仿真；执行前应核对本轮剩余预算。`./run_phase.sh` 无参数仅校验准备状态，不运行仿真。

## 数据边界

传感器后端可以读取场景几何以产生测距；规划器只拿已知先验、当前/历史测距及机器人自身状态。`scene_sensors.py` 属场景构建，不是在线感知算法。`circle_memory.py` 不知道真实圆柱的中心或半径。`robot_predictor.py` 的预测模型只有机器人和地面，没有环境障碍；实际接触检查在真实场景逐物理步进行，预测步数单独记录。

禁用旧控制链在物理积分以外的根位姿/速度辅助，每个物理步间隙及公开步返回时检查连续性。新控制器可覆盖名义SAC全部轮控；因此不能将当前配对当作“只改地图、保持SAC控制不变”的比较，也不能冒称原生SCCR-Full。

## 评价与审计

严格到达：真实目标距离≤0.45m，全程机器人—障碍接触/穿透和未知分类接触均为0。规划成功、进程退出0、停住未碰撞都不是到达。接触计数是接触记录数/物理步数，不是独立碰撞事件数。

输出包含 `STATIC_PROTOCOL.json`、`completion.json`、各分支 `result.json`、`trace.json`、逐公开步状态及逐物理步接触压缩日志。源码在运行开始前快照并记录SHA256。中止分支保留部分日志，不能作为完整任务。

`audit_results.py` 离线核对配对初始状态、接触哈希、8物理步/公开步计数及成功条件。`check_perception_contract.py` 检查冻结噪声模型下的删失判定；`check_exact_footprint.py` 用独立多边形距离参考校验精确几何模块。`exact_footprint.py` 目前仅用于离线诊断，未接入在线控制。`check_circle_memory.py` 仅为合成测量测试，不是校准集。

所有 `*probe.py`、`feasibility_audit.py`、绘图脚本及 `curate.py` 为诊断或离线评价。`truth_connectivity_probe.py` 明确使用评价真值，绝不作为规划器输入；粗网格上的连通也不证明连续SE(2)或动力学可达。

## 当前恢复控制器的特殊限制

21版候选在只有机器人与地面的预测模型中保持命令80物理步，再速率受限制动至240物理步；末速度≤0.025m/s、全程观测地图足迹净空满足门槛才准入。模型与实际模拟器高度匹配且直接使用自身qpos/qvel，不等于实机可用的状态估计精度。正常准入0.155m，后备可使用既定0.15m硬下限；模型预测和经验地图都可能误差，不能据此宣布形式化闭环安全。

圆柱地图使用NumPy稳健迭代拟合，不新增运行依赖。它在至少12帧且角覆盖合格时替代原始点集，失败时仍回退原始点；因此原始回波删失性质与圆柱包络校准是两项不同问题。此次经验包络尚未获得独立覆盖保证。

21版在线决策源码的内容哈希已记录在 `DECISION_FREEZE.json`，与21/22运行前快照逐一比对。22是相同控制器下的地图消融；21的circle_repeat为同状态重复，二者均不能被当作新独立场景。`account_round.py` 在运行结束后核验完整分支、冻结源码和有界计算记账；`curate.py` 生成精选原始日志、全部运行账本和按内容去重的历史源码证据。
