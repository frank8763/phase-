# 完整路线与实际运动模型

Nav2官方Smac Hybrid文档要求设置车辆最小转弯半径：[官方参数说明](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/planners_plugins/smac/smac_hybrid/configuring_smac_hybrid/)。本仓旧参数1.32m；现有实测标定模型的稳态半径约1.6351m，且还有转向反作用/瞬态。仅把几何路径延长不能保证原控制输入产生同一路线，因此本版直接搜索原控制器低阶预测器的状态，再用未改Python预测器完整重建准入。该对齐是本仓实现推论，不是Nav2文档对本车的实验证明。

SIPP原论文引入安全时间区间处理动态障碍，说明空间占据并集会失去可等待通过的机会：[CMU论文页](https://publications.ri.cmu.edu/sipp-safe-interval-path-planning-for-dynamic-environments)，[ICRA2011原文](https://www.cs.cmu.edu/~maxim/files/sipp_icra11.pdf)。本版执行候选仍用原因果整周期并集，保持保守；时间搜索诊断未通过且没有原生时钟接收资格，不能称SIPP实现或宣称其完备性。

`probe_timed.py`与`probe_reversible.py`仅保存诊断：时间对齐与倒车均未获得执行权限。当前前进联合控制器明确拒绝倒车，不能拿几何倒车候选当可执行改进。旧末失败状态的有界搜索未找到整路，不等于所有规划方法均无解。
