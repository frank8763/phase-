# V860 名义速度预测候选：启动接口异常，算法效果未检验

2026-11-07，本用户轮最后一个独立开发支线，只将官方Nav2 MPPI `FollowPath.open_loop`从缺省False设为True，恢复原V858已真实资格通过的Adapter，未叠加V859改动。原V858和V859失败保留，同一20:00根截止，不延长。

官方源码仅将优化预测初始速度从当前robot_speed切为上一条命令last_command_vel，实际robot_pose反馈仍保留；本候选试图区分有限时域名义速度初态与有相位滞后的实际转向响应，尚不是已成立改进。[Nav2 1.3.13 optimizer.cpp](https://raw.githubusercontent.com/ros-navigation/navigation2/1.3.13/nav2_mppi_controller/src/optimizer.cpp)

## 实际停止原因

首次静态WE环境成功初始化，但Nav2 lifecycle_manager在配置bt_navigator时，对`bt_navigator/get_state`的async_send_request失败，终止整个bringup。ROS桥在预设35秒未激活门超时退出。日志没有plan消息或cmd_vel，动作没有发出；不能把这一操作失败归因于open_loop控制效果，也不能宣称该候选有效或无效。

物理后端在等待期间100Hz实际积分3327步/33.27秒，所有命令陈旧或不可用，因此全程原制动控制。末目标8.000392604m、平移速度.000010544m/s，最低净空.314989182m，自体余量.009944852m，坏障碍/未知/自接触0；3327完整控制状态重放误差0/接触不匹配0。最大墙钟滞后6.809ms。

原17审核的16项物理保存/控制/模型/重放门通过，`genuine_ros_observations`因cmd_vel计数0而失败，原审核结论保持evidence_passed=false。此处终审只是如实核对失败证据，不追认验收门通过。原2静态/3动态/3重复/24新确认/3确认重复全部未执行，无确认分母率。

首次接口异常即停止，无本版接续、无下一科学候选、无deadline重置。所有模型/ROS退出、REVIEW_PENDING原字节恢复、执行锁空闲。训练/SAC/实机/Stage0。必要记录归档/远端SHA回读后清本地。

## 下一阶段必须先解决的工程门

生命周期就绪检查要与物理导航分离，先只启动真实Nav2服务器并证明冷启动服务可用、完整configure/activate/cleanup稳定，再将物理车接入；不能通过延长本批35秒超时追认成功。对转向响应，需独立曲线闭环资格来区分名义模型和实际执行器，原V859固定输入负结果已经说明简单去内层反馈不足。当前未再启动这些实验。
