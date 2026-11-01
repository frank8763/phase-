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
