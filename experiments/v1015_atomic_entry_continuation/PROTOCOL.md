# 原子停车交接真实入口修复与通宵安排 · 2026-11-10

本次只修真实入口绑定和事前固定的运行调度，不再次更换已取得实际组件资格的控制器。V1014失败永久保持：1导航模型、7930新增原生、7930自身完整控制重放、私有模型积分0；最低实际净空.273376638m、坏接触0、重放误差0，目标剩3.222200m，HANDOFF_ZERO_ACK_MISSING。这不是动态成功。

## 一手资料与判断

- Python官方说明普通导入依赖模块搜索机制，并给出用`spec_from_file_location`从明确文件加载模块的方法。[Python importlib](https://docs.python.org/3.10/library/importlib.html#importing-a-source-file-directly)。本仓旧native_loop会前插V1004目录；真实worker随后无限定地导入native_contract，实际绑定旧类。本次按明确文件路径绑定接收器和观测投影函数，启动时断言实际接收方法来源/SHA；不依赖目录优先级猜测。这是本仓实测因果，不是官方文档声称本仓一定存在该故障。
- Jazzy官方`IsPathValid`节点调用`is_path_valid`服务，服务成功且is_valid才返回SUCCESS，否则FAILURE。[Jazzy源码](https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_behavior_tree/plugins/condition/is_path_valid_condition.cpp)。继续使用已软件全程成功的V1010有效当前路径保持BT及明确goal_checker；不为本轮再次换规划器。路径有效性检查不是本实验完整足迹/动态安全门的替代。
- Nav2官方行为树把规划/跟随与恢复组织为明确的成功、失败和重试分支。[Nav2官方说明](https://docs.nav2.org/rolling/getting_started/nav2_behavior_trees/trees/nav_to_pose_with_consistent_replanning_and_if_path_becomes_invalid/)。该文为rolling，仅借鉴调度原则，不将新接口假称安装的Jazzy已支持。本次成熟Nav2骨架、RP-CCR原因果恢复、原生控制单一所有权保持；安全失败不作为可重试普通功能失败。

## 实际反馈环

`python -B experiments/v1015_atomic_entry_continuation/qualify_backend.py`在独立新进程加载实际native_worker，不直接挑选待测类：旧入口红：仅PROFILE_RELEASED、wire_ack=null；修后绿：PROFILE_RELEASED和ACCEPTED、wire_ack=101。通过原实际观测投影和JSON编码/解码确认回执保留；缺许可、运动、外来任务、过期观测四负例均在放弃停车所有权前拒绝。模型/积分0，适配器硬件构造替换为元数据夹具，不能冒称实际车已交接通过。原53.44ms回调和两保存停车态的软件资格仍保留。

## 新授权而非延长旧窗

用户最新明确“一条线失败了，多来几条线的，跑满到第二天9点”“自己查着资料，改”。新V1015根在第一次新模型前锁定，模型硬截止2026-11-11 09:00+08/1794358800；V1014原22:31:45前置/08:00总截止与失败保持闭批。先前尚未冻源/启动的V1015旧入口接续草案已被这个新授权计划替代，原ORIGINAL_WINDOW留作旧证据，绝不作为新模型授权。

事前固定三个路线分支：WE主→仅成功才WE完整重复；NS主→仅成功才NS完整重复；EW主→仅成功才EW完整重复。纯功能未到达且所有安全/来源/控制/重放证据通过时保留该失败，跳过它的条件重复，继续其他路线；首安全/证据/接口异常停止全夜。不是任意更换种子/地图或失败后挑选算法。没有未取得软件资格的科学候选被自动启动。

只有三路线6整路全门过才进入原未执行10110001–24固定清单；相位/顺序/路线/方向不变，24真实t0后24主；23/24、每路线7/8、方向11/12后固定1/9/17重复。第二纯功能失败停止，首安全/证据异常停止。完整队列提前完成就结束，不为填满时间制造重复样本；时间与存储预算不足也停，不能保证通宵一定验收成功。

每导航180秒+完整2秒停车，340秒任务外层/365秒完整余时，原子交接和最多8完整恢复段沿V1014冻结科学；实际净空.15、完整自体/接触/控制与全状态重放1e-8不降。单模型CPU顺序执行，全部模型仅run_phase.sh。后台本地进程不依赖网络/chat，防休眠锁与绝对模型闹钟保留。2GiB临时缓存上限，离线无法核验清理时停止新增大证据；不擅自扩大磁盘预算。训练/实机/Stage0，有限课程不代表任意场景/实时/递归安全/RAS保证。
