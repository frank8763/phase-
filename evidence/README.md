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
