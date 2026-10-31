# V650 静态验收窗口

用户已要求静态稳定并验收，动态必须等用户查看成功并明确继续。读PROTOCOL.md和POOL_EXTENSION_PREREG.md；不自动运行本目录已有计划。

- 在线决策继承V649修订27，13个决定地图/规划/预测/控制的模块字节一致。runner独立目录并增强全障碍静态检查和实际转角元数据。
- task_preflight.py仅为t0离线真值任务筛选，在线导航不读TASK_FEASIBILITY或参考路径。
- execute_acceptance.py是原60种子窗口，execute_extended_acceptance.py仅在原池数量不足且导航0时运行补充，二者共用原4小时总预算。
- 正式任务先锁定SELECTION_FREEZE再导航；不能按导航结局重新选择。
- 本轮不修改算法、阈值或SAC模型以挽救确认结果。2次未成功后23/24已不可能，停止并如实记验收不通过；若继续开发须放弃此池确认身份。

输出只在runs/v650_static_acceptance。原始/中断/未解决项保留，预检不算导航成功。
