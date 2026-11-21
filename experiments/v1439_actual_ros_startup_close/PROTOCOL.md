# V1439 原route ROS在零wire下的启动关闭准备

V1437共享phase门一次0模型资格和V1438真实PlanningJob→CPU4原FFI→新PLANNER写入计数一次资格均已闭，旧源只读，不重刷。当前仍无实际canonical initializer/完整actual lifecycle/车辆准入。

剩余外部writer路径应实际核当前actual route ROS的启动/原controller standby/零wire/关闭/持久化，而不重复V1436 modeled RPP callback。新入口限定--startup-close-qualification，显式独立modelsfalse/coveragefalse authority、原WE10060001/原RPP参数和公共map、独立ROS namespace、CPU3、nice19/thread1；不接受任何wire、不发送scan/odom/命令、不调用FollowPath、不构造模型或车辆，最多60s并受周一根截止。startup gate独立于production complete admission，不创建完整准入或ROUND_WINDOW/LAUNCH，不把本资格当actual callback/物理/全lifecycle PASS。普通生产CLI仍要求全原准入。

生产main真实启动Nav2 controller进程，保存current source/CPU/netnamespace/standby READY后只等待同一PEER_STOP_REQUEST，经原PeerClosure/finally保存所有现有空前缀、controller完整退出/ROS closed和writer实际计数；任何意外输入或scan/命令/actor truth/未完全关闭均失败并一次关批。不得拿旧保存packet当当前wire。明确记录server未配置/未激活，无实际action/RPP callback资格；该已测callback沿V1436原SHA复用。

此新source当前仅AST、未资格/未冻结，可在一次必要实际startup/close资格前复核。资格前实际allruns10GiB/evidence224MiB/archive224MiB/download32MiB/root512MiB峰值、源SHA/父idle/锁闲/原review SHA必须核；限定软件启动关闭计数，不增车辆/解析积分/物理或replay。科学修订5和全部200ms/原安全/固定参考/200尾/全程严格门不变。
