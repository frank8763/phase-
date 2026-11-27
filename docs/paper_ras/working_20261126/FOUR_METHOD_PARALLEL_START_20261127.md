# 四方法并行推进：实际启动与资格边界

用户已授权同时推进PSF、PCBF、SCCR、PRIEST。当前真正运行的是PCBF长段原车能力组件，其余三项已在独立CPU完成本轮有限接口准备；没有宣称四个正式导航同时运行。旧120项仍72closed/7whole/48unexecuted，技术和功能失败保留。

| 方法 | 本轮实际工作 | 结果与下一依赖 |
| --- | --- | --- |
| PCBF | V2141后台原车250次当前控制能力组件，CPU2物理/CPU6NLP/CPU4几何/CPU5IO | 12:50健康记录68query/340normal，partial；启动时预计5–10分钟含审核和归档；以最终机器结果和barrier为准 |
| PSF | CPU0对V2137前32cycle共256metadata做无损aggregate及每字节SHA验证 | 1219015逻辑字节/1851392原分配字节→350217B，3破坏负例拒绝；原格式2500query线性投影超224MiB，仅容量诊断，须生产writer/audit/recovery集成后才准完整路线 |
| SCCR | CPU1验证新74维camera/depth及36/32/32scan共同packet，20软件packet×10consumer | 接口及4负例通过，包括真实clear-range全1与missing-render区分；实际采集、相机绑定、完整186/两冻结策略及原车资格尚待 |
| PRIEST | CPU3固定4disc覆盖车辆矩形，512heading几何验证并检查原200个初态约束 | 覆盖数值误差1.11e-16，但仍2初态冲突、minmargin -0.0422746769m，候选不具优化器/原车准入；不按结果继续改圆数或半径 |

V2139源码运输检查残留PSF标签，在0模型/0NLP/0物理时失败；原失败源码和机器记录保留。新V2141只修正该标签/作用域及长段计数，数学与PCBF门仍V2135已声明的工程适配；不重跑旧失败，不把记录系统问题算算法性能。所有原完整停车、跟踪、实际净空、保守预测、因果来源、接触、全状态重放和独立审核门保持。

V2141源码一次资格PASS19935，sole89ab48f352beb7dc967380ea6c19bca3324f1349，Release460178547，source572members193028B全部实际远端block/member/whole/indexSHA和精确运输副本清理、继承恢复链完成后才启动。原车child1701562/start39439431，dispatcher1701542/start39438862。每轮5400秒技术窗保留，Stage8–15/24–31不触及。旧baseline和15GiB总额不扩，增加闭V2137的64MiB保守上界并把此组件archive子额64→44MiB，峰值16093634560<=旧joint16095019008<16106127360B。

三软件worker1699911所拥有的CPU0/1/3进程实际并发启动，0.20秒有限工作后均退出；检查成功不等于各算法导航成功。PCBF的原车组件是独立后台作业，无新增聊天/代理/自动心跳；本报告和健康checkpoint是源封存后本地晚材料，不冒称旧Release包含。
