# 2026-11-06保存证据诊断

本目录仅分析已经保存的轨迹、估计外集合和决策记录。两个脚本均禁止导入MuJoCo，不创建模型、不积分、不启动导航、不改旧科学源或归档。

- `analyze.py`：重建490完整328证书、495/527旧证书剩余段与新估计下界，分解静态/当前占据/未来下界，提取失证前决策与全局规划时间线。
- `classify_tails.py`：对V833新增2610条尾轨迹全部328保存姿态独立计算已知静态足迹下界，将已有混合`TIME_CLEARANCE`拒绝分成“静态门已不满足”和“静态通过但时域门未过”。二者互斥，不是两个独立实验分母。

运行位置为Phase仓库根目录：

```bash
python3 -B experiments/failure_analysis_20261106/analyze.py
python3 -B experiments/failure_analysis_20261106/classify_tails.py
```

输出在`runs/failure_analysis_20261106/`。`analyze.console`保留首次诊断脚本SyntaxError，修正只发生在本新诊断目录，未涉及模型或旧冻结科学源；成功输出为`analyze_ready02.console`。本目录不是新的算法候选或物理运行协议。

旧库拒绝的快速复现：

```bash
python3 -B experiments/v833_timed_escape_qualification/reproduce_old_rejection.py --require-certified
```

该命令应以非零退出，复现旧两保存状态没有合格原前进尾；它不是新恢复控制器的完整回归验收入口。新控制序列是否能获证、真实执行和持续到达，必须另行经事前冻结、有界的原生资格验证，本次没有这些绿色结果。

完整解释及论文缺口见`docs/RPCCR_FAILURE_CAUSE_AND_PAPER_GAPS_20261106.md`。
