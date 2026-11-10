# V1010既有有效路径的软件完整动作检验

最新用户明确继续。本轮只零车辆模型、零物理积分。V1008原错误复现通过：10空检查器错误/0前进；显式检查器使软件peer走7.9232m却在原目标前.602924m停，72次全局成功后78次失败，首失败208，FollowPath被取消。V1008整链NOT_PASSED及原软件数据保持，不延其限时。

唯一追加软件候选：原V1008显式goal_checker不动，在原1Hz规划RecoveryNode内使用实际安装Nav2官方BT相同结构——GlobalUpdatedGoal未变化且IsPathValid服务确认当前路径有效时保留它，否则原ComputePathToPose。无地图清空、不转圈、不倒车；原全局规划器/控制器/停止/安全和所有参数不改。路径只是引导，实际控制仍受原完整有限tube准入，不把IsPathValid当完整矩形/动态安全证书。此修改借用成熟Nav2机制，不宣称新算法创新或递归安全。

单个实际安装完整NavigateToPose软件动作，原[-4,-2,0]→[4,-2,0]，原180秒动作/240秒子进程上限，总300秒软件窗。NoModel导入阻断和非物理peer，训练/实体机/Stage0，不初始化物理模型/预测/重放。必须动作成功/非反向控制/原有限准入/记录完整和peer安全关闭，失败停止，不再追加软件候选或物理。软件通过不等于真实跟踪/发现/动态24验收，后续物理仍需新冻结资格和独立有界授权；旧截止不延长。

主要依据是本机实际Jazzy安装的navigate_w_recovery_and_replanning_only_if_path_becomes_invalid.xml，以及官方Jazzy IsPathValidCondition代码：服务失败/路径无效返回FAILURE。
