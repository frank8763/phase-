# RPP 控制输出与正式对照启动排期（2026-11-25）

原 RPP 控制输出组件已通过。V1963 在原参数、原 V1943 编译二进制、原空地图直线夹具下，实际创建/激活1次控制器，求解1次，返回 v=0.1m/s、w=0。原ExecutableRPP日志同时记录raw_v=.1/raw_w=0与投影后相同，原投影碰撞复查执行。重复native tick请求返回-3，被拒绝并poison，未执行第二次控制求解。1DLL、1constructor、1nonnull handle、1valid solve、1destroy；墙钟6.771371932s。模拟车辆/物理步/重放0，内部原生工作总量unknown。直线输出资格不等于导航、因果动态地图、车辆响应或安全合同完整资格。

依赖闭环：原24个constructor type-support ELF逐路径/SHA补齐。原V1957入口先后次序失败(0RPPDLL)与V1960非ELF DDS映射分类拒绝(1constructor/0solve)均保留。V1963严格先检查ELFmagic/精确SHA，再将有限命名格式的FastDDS共享数据单独验证为不可执行共享映射、当前uid、regular/nonsymlink、大小<=16MiB；原ELF门不放宽。构造后与求解后maps均验证。15753冻结源在child退出后逐SHA相同，REVIEW原SHA恢复、双锁闲。

本次46members/568041B runtime证据已在原sourceRelease中全actualremote block/member/whole/indexSHA回读并做精确运输重复清理，存储barrier闭。solebd245588 source证明复用，无第二push/ref/封传。原raw结果、失败、原源与输入均留；晚helper由runtime成员SHA覆盖而不称旧Git已含它。archive index沿用source说明模板，其中关于zero-source-numerics的scope只描述先前SOURCE，不描述本次runtime；本次实际计数与科学范围以归档内RESULT/RUNTIME_CLOSED_REVIEW为准，不改原archive。

统一对照仍36closed/7whole/84未执行；RPP12项全部未claim。DWA12前驱闭环无缺，生产方法owner/资格尚未创建，真实preflight ready=false。现allruns14953635840B，单worker完整peak16017940480B<16106127360B，只表明此次测得单worker空间门可过，不是未来空间保证或并行资格。

预计到首项正式RPP对照还需3–6小时，属于按工作分解的条件工程排期，尚无完成这些剩余步骤的实测时长，不能作为保证或12项全跑完时间。条件为原参数下接下来的因果地图与响应验收均正常，网络及存储闭环正常：

| 剩余关卡 | 预留时间 | 通过依据 |
|---|---:|---|
| 当前因果观测/公开静态地图/原inflation/TF与时钟接入 | 约1–2小时 | 精确source receipt、32ray允许域、rear/center约定、原地图栅格与膨胀参数、无actor真值混入；实际原RPP请求返回通过 |
| 原车辆响应、全状态控制记忆、完整2200尾/200minimum | 约1–2小时 | 原4cm/.035rad/.015steer/.15实际/原保守预测储备/自体接触门不改，CPU2锁下实际响应与保留尾通过 |
| 捕获重放独审、正式owner/source闭环及首任务准入 | 约1–2小时 | 全Nplus1/capture/ownreplay/state-ctrl-mocap1e-8/contact/source审核、真实工作与存储预算、原12任务原种子原相位不变 |

若下一步功能拒绝或证据问题未通过，应据实更新排期，不将组件成功转写为正式导航ready。3–6小时从本次输出验证结束后的剩余工作起算，不是后台已经跑的计时。当前没有后台正式导航。下一步实现并验证因果地图/当前请求与原车辆响应的接口，保持旧失败及原120分母。

证据：runs/v1963_rpp_nonexecuting_shm_scope/RESULT.json、RUNTIME_CLOSED_REVIEW.json、AFTER_CONSTRUCTOR_MAPS.json、AFTER_QUERY_MAPS.json、native.console、COMPONENT_POST_STORAGE_BARRIER.json；远端runs/v1965_rpp_control_output_runtime_recovery/FULL_REMOTE_VERIFIED.json。
