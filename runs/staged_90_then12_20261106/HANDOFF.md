# V842预算接续：90分钟先导，通过后条件12小时

用户明确“90分钟的开始；通过之后再开启12小时的”。解释已在当前聊天说明：第一阶段原10060002的一次完整主导航，90分钟为独立模型硬窗，预检/重放/MJB元数据也计入，取消旧20分钟子上限；具体导航软上限为窗口扣除尾审核和退出余量后的约85分钟。其后允许有界零模型收尾，只有完整链、17审核、全部状态控制重放、完整来源/解压SHA和大blob32MiB无损回读FINALIZED才新开12小时。

条件12小时仅先导完整重复→原10060008主→成功后该任务完整重复，最多3新导航，固定相位/场地/种子，不替补。12小时只在先导通过后一次锁定自己的绝对模型截止，不重开/延长旧窗口；单导航90分钟软/95分钟硬/95分5秒外且不越根截止。失败即停，不冻后修补、重跑、克隆或新候选。不是新24确认或三路线验收，不启动剩16/新24/对照/训练。

算法精确V841，0科学修订；只预算、命名空间、分项计时和按任务注册审核变化。新实际10060002必须完整核对V841原389公开/3112原生qpos/qvel/ctrl/mocap<=1e-8；10060008用自身原相位配对。原.155/.15/完整328+新增8/329执行657规划/完整自体ctrl/因果感知/零坏接触/无积分外根写/固定静态体及全部重放门不变。私有每导航100000000事前资源上限，不增候选库/动作/训练。Stage/子代理/新聊天/外部消息/网络/SAC/实机0，runtime/current/冻结网络不改。

唯一campaign为experiments/staged_90_then12_20261106/campaign.py，冻结后launch.py只一次claim；不能再次启动。模型只能run_phase隔离、单CPU单实例执行锁。后台不依赖助手在线或网络。运行只读ROOT ROUND_WINDOW/LEDGER及runs/v842_staged_long_navigation各阶段pilot90/development12的ROUND_WINDOW/ACTIVE/PREFLIGHTS/RESULTS/COMPLETION/ERROR/FINALIZED与当前partial_progress。实际导航输出在pilot_main02、long_repeat02、long_main08、long_repeat08。若driver消失先诊断保留原记录，禁止重启或延时。

独立模型时钟：先导首模型前根AUTH固定；条件12小时由ROOT/DEVELOPMENT12_WINDOW_CLAIM.json一次写入且绑定先导FINALIZED和PILOT_REFERENCE_FREEZE，后续模型每次核验已通过基线。若先导未通过，该文件不得存在。截止后仅零模型收尾。数据/计数未知写null不填0；所有原始证据保留，不覆盖原归档或重试旧同步。

各阶段自动独立终审/归档/大blob分块，finally恢复REVIEW_PENDING原字节。闭批报告docs/RPCCR_STAGED_90_THEN12_20261106_REPORT.md与各阶段报告。结果本地保留等待审阅提交，不作网络push；已有大blob只提交已验证32MiB块，原件保留。模型前17保存接口、按任务预检、缺依赖、缺项、阶段切换及预算负例已0模型通过；canonical metadata proxy仅导入演练，不能冒称新MJB审核，实际MJB元数据须在模型窗内完成。
