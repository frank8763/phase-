# 精选证据

这是一个整理后的成果包。每个原始保留文件的来源、字节数和 SHA256 位于 `../manifests/source_provenance.json`。

| 内容 | 用途与边界 |
|---|---|
| `phase22_formal/Final300/` | 最完整的早期正式基线；完整分母与失败结果保留，原验收门槛未全通过 |
| `phase22_formal/G2A`–`G4C` | 泛化、长路线、多场景、DWA 对照；评价口径保持原样 |
| `best_verified_rescue/` | 一个有重复核验记录的历史救援锚点；不能代表普遍成功 |
| `harm_counterexample/` | 同一研究线的损害反例，防止只保留正例导致误导 |
| `current_v647/` | 最新单场景的两分支实际结果和必要轨迹；未到达 |
| `milestones/` | V334 完整批次状态、V529/V646 负结果、V647 原始清单 |
| `outcome_ledger.json` | 898 份历史 V2 汇总的压缩接力记录，含重复和开发案例，不能合并为独立样本 |

未保留所有失败运行的原始大日志、重复快照和旧检查点。清理明细只是删除凭据，不是完整历史备份，也不能据此重新生成已删除的原始数据。


## 2026-10-31 新增纯物理静态未知障碍开发证据

[static_unknown_20261031/](static_unknown_20261031/README.md)保存首个单未知圆柱开发场景的严格到达、同状态重复、固定控制器地图消融、必要负例和完整开发运行账本。该新协议禁用积分外根状态辅助，不能与上表历史成功率直接混合。当前结果及限制见[实验报告](../docs/STATIC_UNKNOWN_REPORT.md)。

## 2026-10-31 静态稳定化开发

[static_stability_20261031/](static_stability_20261031/README.md)保存V649完整尝试账本、4个不同开发任务的严格到达、必要失败对照、自体几何验证和控制日志重放审计。确认导航仍0、预定重复未执行，不能称静态稳定性已通过；见[当前报告](../docs/STATIC_STABILITY_REPORT.md)。

## V650独立确认与V651开发修复

[static_acceptance_v650_20261031/](static_acceptance_v650_20261031/README.md)保存全部13项确认的11个到达和2个失败、完整任务选择账本及原生控制重放，未执行项明确不计结果，确认未通过。

[static_progress_repair_v651_20261031/](static_progress_repair_v651_20261031/README.md)保存4次开发运行的全证据。最终修订29在两个原失败与一个困难回归中严格到达、完整审计通过；修订28虽到达但换向审计未通过，仍保留。版本/重复不混成独立确认样本。

## V652 原批次中断与V653日志续验

[static_confirmation_v652_interrupted_20261031/](static_confirmation_v652_interrupted_20261031/README.md)保留286项预检、原清单和4个完整成功分支及第5项19步日志中断；原批次不通过，原失败不改写。

[static_logging_continuation_v653_preregistration/](static_logging_continuation_v653_preregistration/README.md)记录仅诊断字典拷贝的修复证明、仍保留一次未成功且不重置截止时间的续验协议；实际后续结果尚待完成，不能将预注册当作通过。

[static_same_list_v653_20261031/](static_same_list_v653_20261031/README.md)保存19项续验导航与首重复的完整证据、组合24项账本和原失败：导航23/24，但接触摘要含输出目录导致原复现未通过，整轮未通过。停止后的离线诊断不回填旧验收；后续V654核验修复开发与V655新池单列。

[static_validator_development_v654_20261031/](static_validator_development_v654_20261031/README.md)保留两项实际到达及全部接触/重放证据：93000045完整复现，91000002因墙钟搜索路径不同而未复现，开发未通过，V655从未执行。V656固定在线工作量开发与V657新池确认事前冻结分别见static_fixed_work_v656_preregistration与static_fixed_work_confirmation_v657_preregistration，预注册不是通过证明。

[static_fixed_work_development_v656_20261101/](static_fixed_work_development_v656_20261101/README.md)保存3个修订30困难基准和3次完整同版本重复、独立物理/接触/状态审计与32倍时钟速率零仿真探针。开发通过但不是独立确认率，V657全新池确认另行记账。

## 最新静态工程验收（用户审阅入口）

[static_acceptance_v657_20261101/](static_acceptance_v657_20261101/README.md)：全新24项23严格到达（单12/12、双11/12），1HORIZON失败保留；3同版本完整重复误差0、27物理审计与独立重算通过。160112原生步审计、导航最小净空0.192639338m、含困难重复0.181062072m。1461清单文件校验通过，完整保留全部310预检、24导航与3重复来源和必要XML字节。仅有限筛选静态基准工程验收；动态未开始，后续等待用户审阅。[最终报告](../docs/STATIC_ACCEPTANCE_V657_REPORT.md)。

## 用户授权后的动态首轮 · V658–V661

四包dynamic_scene_v658_20261101、dynamic_scene_repair_v659_20261101、dynamic_time_gate_v660_20261101、dynamic_forecast_route_v661_20261101完整保留场景预检、导入错误、补充核验及三个未到达分支。仅一个开发任务，动态确认0；7728导航原生步物理审计通过不等于动态验收通过。293清单文件及248来源引用核验通过。[动态开发报告](../docs/DYNAMIC_UNKNOWN_DEVELOPMENT_REPORT.md)和[研究路线](../docs/DYNAMIC_RESEARCH_PLAN.md)为当前入口；静态V657原结果保持通过。

## 动态测距集合与起点观测消融 · V662–V663

[dynamic_sensor_diagnosis_v662_20261101/](dynamic_sensor_diagnosis_v662_20261101/README.md)保留原264控制精确回放和实际测距包；不是新导航。

[dynamic_interval_tracking_v663_20261101/](dynamic_interval_tracking_v663_20261101/README.md)保留同源码32/0步起点观测两条未到达轨迹；3832导航原生步和完整重放通过，481帧各121个未来时刻有限集合覆盖通过。两包175清单文件、95来源引用校验通过，不能把证据PASS叫动态验收。详见[当前诊断报告](../docs/DYNAMIC_INTERVAL_DEVELOPMENT_REPORT.md)。

[dynamic_causal_proposal_v664_20261101/](dynamic_causal_proposal_v664_20261101/README.md)保存最新一次285步未到达及2280原生步完整核验；[dynamic_dense_edge_diagnosis_v665_20261101/](dynamic_dense_edge_diagnosis_v665_20261101/README.md)只保存两个锁定输入的零积分密集边段候选核验，不是导航成功。V662–V665四包266清单文件/130来源引用均通过，另dynamic_interval_round_account_20261101保存累计分账。

## 动态测距一致性与有限恢复 · V666–V669

[dynamic_dense_navigation_v666_20261101/](dynamic_dense_navigation_v666_20261101/README.md)、[dynamic_first_hit_v667_20261101/](dynamic_first_hit_v667_20261101/README.md)、[dynamic_recovery_probe_v668_20261101/](dynamic_recovery_probe_v668_20261101/README.md)、[dynamic_reserved_recovery_v669_20261101/](dynamic_reserved_recovery_v669_20261101/README.md)保留全3未到达导航、同测距估计消融、405固定输入诊断和实际40公开步反向制动尾。9592新导航原生/完整重放核验通过，有限后备成功未转化为到达。四包289清单文件/173来源引用与原始接触SHA通过；原日志目录中断及重试源/步数完整保留。[当前报告](../docs/DYNAMIC_RECOVERY_V669_REPORT.md)给出预算、未执行项、机制边界和论文草稿入口。

## V670连续未命中约束开发

[dynamic_empty_samples_v670_20261101/](dynamic_empty_samples_v670_20261101/README.md)保留一次843公开/6744原生步的900秒超时未到达、原始失败与完整前缀重放、5000几何/701旧包验证和844实际包同输入估计消融。119清单文件/69来源引用校验通过，另核对打包原始接触74981条及SHA；原完整验收FAIL不改。实际面积缩小28.13%仍无持续通行，不能将前缀核验PASS称动态通过。[最新报告](../docs/DYNAMIC_EMPTY_SAMPLES_V670_REPORT.md)。

## V671–V673失败分解与结构验证

[dynamic_structure_diagnosis_v671_20261101/](dynamic_structure_diagnosis_v671_20261101/README.md)、[dynamic_minimal_backup_v672_20261101/](dynamic_minimal_backup_v672_20261101/README.md)、[dynamic_joint_forecast_v673_20261101/](dynamic_joint_forecast_v673_20261101/README.md)三包247清单文件/123来源引用通过。两个同开发任务分支929/940公开步均未到达；14952导航/14952控制重放完整公开状态误差0、障碍/穿透/未知0、最低实际净空0.247080403m。固定5200诊断重放、100私有控制和32零机器人积分LP分别计账；初始JSON及缺依赖错误保留，安装树仅runs可重建。无重复/新池/训练/实机/Stage访问，不把证据核验PASS当成通行通过。[最终分析](../docs/DYNAMIC_STRUCTURE_V673_REPORT.md)。


## V674–V675有界续接开发：未通过
[dynamic_renewable_backup_v674_round_20261101/](dynamic_renewable_backup_v674_round_20261101/README.md)保存本轮全部两未到达导航、固定同状态诊断、原失败/源/模型/接触/控制与完整账目。14304导航原生/完整重放状态误差0，最低实际净空0.252712875m、障碍/穿透/未知0；两版各10步原始证书命令与实际ctrl因执行器裁剪而不同，完整命令契约未通过。V675原FAIL、V674原较窄检查PASS、扩大命令核验及原COMPLETION均保留，不能用裁剪等效回填验收通过。0重复/新几何/确认/训练/实机/Stage访问，无第三候选，原始runs保留。[最终报告](../docs/DYNAMIC_RENEWABLE_BACKUP_V674_REPORT.md)。

本包320份原始文件、253份清单文件全部逐字节解压/哈希回读通过，压缩后27,725,391字节；所有原始runs保留。


## V676–V678命令一致性与算法/场景分解
[dynamic_command_scene_v676_round_20261101/](dynamic_command_scene_v676_round_20261101/README.md)记录两因果未到达与单独特权474步到达见证。全部14800原生/控制重放与原始ctrl、全状态、安全、源模型审计PASS；因果11008与特权3792原生分开，0未知动态到达/确认。额外扫掠信息下同物理场景可安全通行，但不证明有限信息必可解。474成功帧中49帧未来位姿样本在因果外覆盖下不获证，评价器反事实0积分，不给在线控制未来。所有原始失败、冻结源、模型、分账和原始runs保留，[最终报告](../docs/DYNAMIC_COMMAND_SCENE_V676_REPORT.md)。

归档核验：490份原始文件的归档时字节快照、283份清单文件逐字节/哈希解压回读通过，存储25,029,175字节；原始runs保留。只读准备检查READY，0环境/仿真/训练且Stage不可见，三版本冻结源/协议哈希未变。


## V679–V681前进后备与拒绝的空间提案
[dynamic_forward_reserve_v679_round_20261101/](dynamic_forward_reserve_v679_round_20261101/README.md)完整保留3锁定状态诊断、V680唯一804公开/6432原生未到达及全控制/状态重放、V681第49输入路线前置失败（0导航）。一项私有前进尾可证只允许686一次普通首输入，0前进尾实际接管；不能称动态救回。固定16488旧控制重放/58656私有，导航4492352私有另记。141原文件/141清单文件逐字节解压/哈希回读通过，原始runs保留。原静态V657不变，0新几何/独立确认/重复/训练/实机/Stage。[最终报告](../docs/DYNAMIC_FORWARD_RESERVE_V679_REPORT.md)。


## V682动态根因复核（0机器人积分）
[dynamic_root_cause_v682_20261101/](dynamic_root_cause_v682_20261101/README.md)保存804帧完整原因分解、精确当前状态/原未来界/真实未来的固定姿态几何对照、普通倒车与后备净进展、测距分辨率和冻结源码核对。当前估计不确定性与更广未来运动类、空间规划/局部弧长目标的结构缺口均有实证，但未唯一辨识各项对导航的因果贡献。原窗口闭合，0新导航/重放/私有机器人预测/训练/实机/Stage。全部输出归档解压/哈希回读通过，继承输入SHA与原V680源码冻结保持一致。[详细报告](../docs/DYNAMIC_ROOT_CAUSE_V682.md)。


## V683–V685当前信息验证与末端拒绝分量
[dynamic_current_info_v683_round_20261101/](dynamic_current_info_v683_round_20261101/README.md)完整保留一次准确当前状态特权未到达753公开/6024原生、原信息计数FAIL及独立V2逐754决策核验、V684原49/227/245目标一致性修订前置未过、V685原18条最终预测复算与全失败账目。实际最低净空0.213391、控制/状态重放0误差；18原预测重现0误差且仅动态外覆盖拒绝，后见实际未来净空不混为在线成功。0新因果导航/重复/新几何/确认/训练/实机/Stage，固定私有24664<=40000，原截止不变，原始runs保留。[完整报告](../docs/DYNAMIC_INFO_VALIDATION_V683_REPORT.md)。


## V686空白场地能力课程：检测/规划有证据，通行未通过
[dynamic_open_curriculum_v686_20261101/](dynamic_open_curriculum_v686_20261101/README.md)保留新4米空白任务一次导航600公开/4800原生、一次完整4800重放和全部原始审计失败/补充零积分审计。574/600帧检测，19联合当前集合下密集合格空间路线，HORIZON终距3.401734m；原生最低净空0.540338、控制状态重放0误差。原driver STOPPED_EXCEPTION保留，V2纠正观测微轮速错误假设，普通候选/原生控制/安全/模型与11尾几何检查通过。193份原始文件/139清单文件解压哈希回读通过，存储11,416,725字节，原始runs保留。训练/独立确认/Stage/实机0，不称SAC已学会动态。[最终报告](../docs/DYNAMIC_OPEN_CURRICULUM_V686_REPORT.md)。


## V687 C0基础控制课程：三路线与完整重复通过
[control_curriculum_v687_20261101/](control_curriculum_v687_20261101/README.md)保留全部预注册直线206、圆弧232、原绕行344及绕行重复344公开步到达结果。9008导航原生与9008完整重放误差0，全部控制/安全/规范初态/模型/逐物理事件匹配，完整原车和地面参数不变；训练/动态/实机/Stage0。原初始化目录冲突0积分和原附加审计命名空间失败0积分保留，接续未重跑已执行直线、未延期。186原始文件/108清单文件完整解压哈希核验，存储11,985,857字节，原始runs全部保留。固定参考/重规划/观测/后备模式有多项变化，不作actor唯一因果归因，也不代替动态验收。[报告](../docs/CONTROL_CURRICULUM_V687_REPORT.md)。


## V688 6米动态参考通行与提案学习：学习版未通过
[dynamic_distance_v688_20261101/](dynamic_distance_v688_20261101/README.md)保存6mteacher884公开到达、852样本/512次监督训练、学习版900公开未到达终距1.074496m及实际470/868普通步网络控制。两次14272导航/14272完整重放、8253760私有，物理/控制/源模型/联合覆盖/投影/训练来源审计PASS；学习版未到达后相位测试/重复和8m全部未执行。原numpy.bool_JSON审计失败与原driverCOMPLETION保留，补充只修写出、0积分、未重跑teacher或延期。300原文件/176清单解压哈希回读通过，存储20,584,006字节，原始runs保留；训练是独立监督提案器，冻结SAC0，Stage/实机0。[完整报告](../docs/DYNAMIC_DISTANCE_V688_REPORT.md)。


## V689有限6米动态学习课程通过，8米初始观测失败
[dynamic_route_commitment_v689_20261101/](dynamic_route_commitment_v689_20261101/README.md)保存全部15次旧重规划诊断/前置、两相位6m629/631步到达及631步完整重复（全qpos/qvel/ctrl/mocap误差0、模型/规范初态/真实接触事件匹配）。15128导航/15128重放原生、9234400私有，本轮梯度0，复用旧6m网络，实际360/554和460/599普通步网络参与。8m已尝试但在0步因NO_INITIAL_ACTOR_OBSERVATION失败，原FAILED/driverCOMPLETION保留；47束原包/有效hit筛选/2.96m采样复算通过，8m训练和评估未执行。487份原文件/211清单完整解压哈希回读，存储20,518,861字节，原始runs保留，Stage/实机0。[完整报告](../docs/DYNAMIC_ROUTE_COMMITMENT_V689_REPORT.md)。


## V690 可比初始观测8米动态学习课程通过
[dynamic_visible_eight_meter_v690_20261101/](dynamic_visible_eight_meter_v690_20261101/README.md)保存两相位零积分可观测性/全扫掠预检、teacher854公开步到达、765样本/512监督微调、冻结学习相位0 827和pi2 722步到达及722完整重复。25000导航/25000重放原生、15032720私有，全部物理/控制/因果/原车参数审计通过；最低实际净空.291524，全状态/控制/actor重复误差0、接触事件匹配。原V1初始损失精度假设FAIL、0积分载入舍入诊断与V2全账目PASS一并保留，未重跑/改模型。624原始文件/265清单解压哈希核验、存储34,163,706字节，原始runs全部保留。明确新8米初始可见任务，不回填原V689不可见失败，不是复杂场地或统计动态验收，Stage/实机0。[报告](../docs/DYNAMIC_VISIBLE_EIGHT_METER_V690_REPORT.md)。


## V691途中发现：完整通行未通过
[完整证据](dynamic_discovery_v691_20261101/README.md)保存一次408公开步未到达、首次真实运动检测与完整制动、新路线、全原生控制状态重放，以及0积分失败诊断。223原文件/154清单全字节解压哈希通过，存储10,193,461字节，原始runs保留。重复未执行、梯度/Stage/实机0，不能将部分链条或审计PASS算完整成功。[报告](../docs/DYNAMIC_DISCOVERY_V691_REPORT.md)。


## V692固定末状态99动作验证
[完整证据](dynamic_escape_v692_20261101/README.md)保留3264旧控制重放误差0及99项32472私有预测，全部无合格证书。9原文件/11清单逐字节解压哈希核验通过，存储17,487字节，原始runs保留。失败预测的完整状态数组未保存，独立账目审核不等于重新仿真核验；0新导航/训练。[报告](../docs/DYNAMIC_ESCAPE_V692_REPORT.md)。


## 夜间V693/V694原始执行夹具失败
[完整归档](dynamic_night_setup_20261101/README.md)保存77原文件/44清单，完整解压哈希回读通过，存储48,380字节。V693被写出guard遮蔽的诊断账目永久未知区间，V694最终1原生步TypeError失败，0导航，不算物理通过；独立V695修复另记。全部原始runs保留。


## V695途中发现完整链开发通过
[完整证据](dynamic_discovery_v695_20261101/README.md)保存两相位765/770公开步主任务及各完整重复，24560导航/24560重放、最低净空.398713695m、全状态控制重复误差0，全部物理/因果发现/原生停车/新路线/严格到达审计通过。647原文件/235清单完整解压哈希通过，存储28,532,516字节，原始runs保留。仅两相位开发，V696全新24任务确认另记。[报告](../docs/DYNAMIC_DISCOVERY_V695_REPORT.md)。


## V696新确认预检停止与最终夜间封账
[完整证据](dynamic_confirmation_v696_20261101/README.md)保留冻结24项、11预检通过/第12旧初始化失败、12未预检/24未导航/3未重复、原STOPPED_EXCEPTION/独立全门FAIL和零积分原因复核。915原文件/228清单完整解压/哈希回读通过，存储5096886字节，原始runs保留。V695开发通过另档；新确认未完成，没有导航成功率，自动任务已删除。[最终报告](../docs/DYNAMIC_OVERNIGHT_20261101_REPORT.md)。


## 2026-11-02汇报素材与两个高清静态视频
[下载与核验](presentation_materials_20261102/README.md)保存8页PPT文字、方法图和V657每类首个成功案例的双视角1080p/25fps/H.264视频（44.92秒、59.32秒）。均为原审核状态渲染，0新增积分/训练，输入SHA不变；完整解码与ZIP逐文件SHA回读通过，不增加独立试验样本。


## RP-CCR定位修正版汇报素材v2
[修正版素材](rpccr_presentation_alignment_20261102/README.md)明确核心研究算法为RP-CCR，补充风险/进展/连续恢复机制与实验约束；修正8页文字和框图标题。两个静态视频与原版字节完全相同，原审核/模型/轨迹不改，新增仿真和训练0。旧版保留，汇报建议使用v2。


## RP-CCR V697初始化解耦开发通过
[完整证据](rpccr_dynamic_initialization_v697_20261102/README.md)保存24项原清单零导航预检/原噪声逐包精确复算、旧765锚点整段等价、原slot12主与重复均788到达及全状态/控制/接触匹配。最低实际净空.293145305m，18728导航+18728完整重放/11440168私有，0新算法修订/训练。2194原文件/510清单全解压哈希回读通过，存储24,800,670字节；原始runs保留。只新增1个开发任务，独立24导航确认仍0；原V696失败/旧夜间封账与截止不改。[报告](../docs/RPCCR_DYNAMIC_INITIALIZATION_V697_REPORT.md)。


## V698 RP-CCR动态独立确认
[完整证据](rpccr_dynamic_confirmation_v698_20261102/README.md)独立结论NOT_PASSED，尝试13/24、完整链到达12、未执行11，重复0/3；全部已归档字节解压哈希核验通过，原始runs保留。见[实际报告](../docs/RPCCR_DYNAMIC_CONFIRMATION_V698_REPORT.md)。不凭归档完成宣称导航成功。


V698[零积分原因补充](rpccr_dynamic_confirmation_v698_diagnosis_20261102/README.md)核实：第13原审计136帧空观测JSON形状误报，9934帧数值差0且全部因果状态匹配。原NOT_PASSED、原全证据归档及未执行11主/3重复保持；不追认确认通过，新增积分0。


## V699空观测审计修复：零积分验证通过
[完整证据](rpccr_dynamic_audit_v699_20261102/README.md)保存24原预检、13原发现链复审、严格七字段模式、全部真实包变更负例和完整入口缺键/畸形包拒绝；原V698未通过与11主/3重复未执行保持。新增积分/导航/训练0，不能叫动态确认通过。[分析报告](../docs/RPCCR_DYNAMIC_AUDIT_V699_REPORT.md)。


## V700 RP-CCR动态原清单接续
[完整证据](rpccr_dynamic_continuation_v700_20261102/README.md)独立结论FINITE_MOVING_DISCOVERY_SAME24_CONTINUATION_PASS，尝试24/24、完整链到达24、未执行0，重复3/3；全部已归档字节解压哈希核验通过，原始runs保留。见[实际报告](../docs/RPCCR_DYNAMIC_CONTINUATION_V700_REPORT.md)。不凭归档完成宣称导航成功。


## V701恢复续接机制诊断
[完整证据](rpccr_recovery_ablation_v701_20261102/README.md)保存固定两已观察案例的FULL/COMPLETE_TAIL及消融完整重复6执行。FULL2到达，消融2安全非到达并各完全复现；全部6物理审核/4完整比较通过，24000导航与完整重放、12641776私有准确。769原文件/327清单全解压哈希回读，不把证据完整PASS当作泛化或全面算法优越。[报告与解释](../docs/RPCCR_RECOVERY_ABLATION_V701_REPORT.md)。原始runs保留。


## V702新任务计算对照：预检超时，导航未执行
[完整原证据](rpccr_prospective_compute_v702_20261102/README.md)329原文件/128清单全解压回读通过，3项t0通过/第4旧初始化超时，全部旧校准/8新主/2重复未执行；没有全4成功率或触发率，不能把未执行计失败。原记录保持，[停止原因报告](../docs/RPCCR_PROSPECTIVE_COMPUTE_V702_REPORT.md)明确阶段和未知根因，不把工程预检异常当算法无效。原始runs全部保留。


## V703零积分初始化栈诊断
[原栈与失败证据](rpccr_bootstrap_trace_v703_20261102/README.md)保留旧reset几何/Hermite/B样条规划采样和结构化写出guard失败；不是新导航或初始化PASS。12原文件/14清单全部解压哈希回读通过，原始runs保留。[原因与修复设计](../docs/RPCCR_BOOTSTRAP_TRACE_V703_REPORT.md)。

## V704初始化入口修复与旧锚点等价
[完整证据](rpccr_bootstrap_repair_v704_20261102/README.md)包含4原t0通过和2旧slot14轨迹精确复现，FULL811到达/SHADOW335安全非到达；共同307步首提交候选与1297608共同预测积分相同。609原文件/254清单全部解压哈希再核验，9168导航/9168重放/5070640私有精确；旧V702/V703失败不改，原4新主导航0。[报告](../docs/RPCCR_BOOTSTRAP_REPAIR_V704_REPORT.md)。原始runs保留。

## V705原4新任务成对与计算对照
[完整证据](rpccr_prospective_pairs_v705_20261102/README.md)保存8主+2固定完整重复、4t0及所有原始物理/控制/传感/源模型/因果/尾/配对审计。FULL4/4、SHADOW3/4，仅1对实际触发并出现到达差异；其余3对未触发且相同，全部保留。两完整重复误差0，53440导航/53440重放/30118368私有精确；1626原文件/485清单全解压哈希回读，原始runs保留。不把归档或影子消融当强基线与全面优势。[报告与范围](../docs/RPCCR_PROSPECTIVE_PAIRS_V705_REPORT.md)。

## V706原场地预检失败
[原失败全证据](rpccr_global_field_v706_20261102/README.md)85原文件/87清单回读，首预检无注册宽敞晚发现点，actor未生成、导航/私有/重放0；[后续零积分诊断](rpccr_global_field_v706_diagnosis_20261102/README.md)独立保存，不覆盖原归档。不能把未执行计失败或称全场无解。

## V707最后开发预检失败与夜间封账
[原V707全证据](rpccr_field_reference_v707_20261102/README.md)84原文件/86清单回读，首例未返回合格离线完整目标参考，actor未生成、导航/私有/重放0。全夜2开发额度用尽，独立24全部未执行；[夜间实际报告](../docs/GLOBAL_DYNAMIC_OVERNIGHT_20261102_REPORT.md)不把建场失败或未执行冒充导航通过/失败率。原始runs保留。

## 完整场地夜间最终封账
[夜间授权/台账/报告与全部离线诊断快照](rpccr_global_dynamic_overnight_20261102/README.md)逐文件回读。两开发均在actor生成前预检失败、2零积分初始化、导航/私有/重放0，24确认和3重复未执行；开发额度用尽提前停止。原各批归档独立保留，不把零积分或未执行计导航成功率。


## V757–V761状态反馈方向/速度资格与实际组件
[完整证据](rpccr_state_feedback_v757_v761_20261103/README.md)343来源文件/337归档清单全部解压与来源哈希回读。三原受阻状态有合格替代，但闭环仍在52主动公开后安全尾停稳，净目标进展.737740333m、96步资格未过；V758/V760独立证据通过，重复未执行。1768旧重放/84952私有/712新实际/89新包，0从头导航确认/训练/Stage/实机。原失败和原始runs保留，[完整报告与图](../docs/RPCCR_STATE_FEEDBACK_V759_REPORT.md)。


## V762–V768提前观察承诺
[完整证据](rpccr_observation_commitment_v762_v768_20261103/README.md)1746来源/746去重清单逐字节解压和来源回读。V762有限96主动组件主+完整重复PASS；V764/V767长周期FAIL，原失败全部保留。V767实际两次退出观察，但首次退出后仅.091108m未达1m。1752旧重放/527424私有/4544新实际/568新包，所有独立证据审核通过，完整场地动态仍未通过。[报告与图](../docs/RPCCR_OBSERVATION_COMMITMENT_V762_V768_REPORT.md)。原始runs保留。


## V769–V777地图条件可达集合与保留尾重新接入资格
[全证据](rpccr_map_conditioned_v769_v777_20261103/README.md)1133来源/822去重清单全部解压/来源回读；私有固定SciPy2338文件完整ZIP/安装来源哈希保留，共享环境未改。V772两实际版本均持续推进FAIL，完整动态未通过；V776原138/140/144尾状态15动作各12/9/2合格、4/3/0有≥.05预测进展，V777独立审核通过，新交接未实际执行。原V770导入失败/V774补充写出失败与修复均完整保留。累计4216旧重放/290608私有/2320新实际/290新包，所有原生安全/模型/因果/状态证据通过，0新从头导航确认/训练/Stage/实机。明确非穿透已知几何是条件运动类。[报告与图](../docs/RPCCR_MAP_CONDITIONED_V769_V777_REPORT.md)。原始runs保留。
