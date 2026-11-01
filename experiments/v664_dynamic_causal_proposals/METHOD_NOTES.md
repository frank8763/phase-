# 动态路线与原始文献

[SIPP, Phillips & Likhachev, ICRA2011](https://publications.ri.cmu.edu/sipp-safe-interval-path-planning-for-dynamic-environments)说明时间维度和安全时间段能表达等待让行，静态化重规划会丢失这类解。本轮借鉴时刻一致的碰撞检查，不声称已实现完整SIPP。

[Ali & Yakovlev, 2023](https://arxiv.org/abs/2302.00776)指出原SIPP瞬时停止假设不适用于有加减速约束的机器人。本车继续保留原生动力学预测和速率受限制动尾，不能仅给路径加时间戳就宣称可执行。

[ORCA原作者项目](https://gamma-web.iacs.umd.edu/ORCA/)的互惠模型由双方分担避让责任。本轮脚本障碍不主动避让，不能依赖它让路或直接移植互惠保证；完整Ackermann车体/执行迟滞亦需自己的准入。

[MuJoCo官方仿真文档](https://mujoco.readthedocs.io/en/stable/programming/simulation.html)将mocap_pos/mocap_quat定义为外部运动学输入。本轮采用该公开接口并逐物理步记录，仅机器人根状态禁止积分外改写；这不是受力驱动的行人模型。

论文证据顺序：先证明运动场景合格且不堵口，审计运动/传感器/接触/完整自体；再用相同观测与计算预算比较瞬时占据和因果运动预测，记录碰撞、严格到达、等待、恢复和延时；之后才做速度/相位/遮挡新池确认与组件消融。已有静态负例继续保留。小障碍和宽通路是用户规定的第一轮任务边界，不是性能提升证据。
