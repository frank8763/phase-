# 剩余四种方法：有效比较的执行安排

用户已授权继续，并选择另设所有参比方法具有相同相机/深度权限的新确认组。旧120登记、72闭轮及其失败保持；新组不把SCCR额外输入偷偷加入旧表，也不把未具备接口的方法填0成功率。

当前已经实际执行：

| 方法 | 本次执行 | 已建立的证据 | 尚未建立 |
| --- | --- | --- | --- |
| PSF | V2131原车20次当前求解、100normal+2200stop，2300actual/replay | 原控制/跟踪/净空/接触/完整capture/N+1/replay/独立审核PASS；无首错secondary | 全路线、完整到达、必要挡位交接、最终新相位/布局确认 |
| PCBF | V2131原车3次求解、2次执行，10normal+200errorstop，210actual/replay | 原安全前缀审核PASS；第三aux status8未收敛，准确保FAIL | 连续20次、全路线及确认；当前初始化对照是开发数学实验 |
| SCCR | V2132原传感纯函数24软件场景×10统一consumer，50camera/depth维一致 | 原传感特征的接口/来源/形状/时钟/拒绝测试通过；无hidden geometry字段 | 原车采样/噪声/完整186特征/风险融合/冻结actor与车辆动作资格；没有新正式SCCR运行 |
| PRIEST | V2132保存输入几何与原作者约束分析 | 原rearcirc输入50/50障碍在t0内，与固定初态等式不相容；bodycenter单圆仍3个在内，不接受该修复猜想 | 正确车辆参考点/朝向相关足迹和作者优化耦合、基本能力及完整停车验证；没有重跑旧拒绝 |

PCBF初始化对照固定原3个开发输入、独立软件open正例和occupied负例。原始slack=max(g,0)+.01与去掉额外.01的可行起点比较，原控制初值/目标/Jacobian/约束/400iter/ftol1e-10/residual1e-7/status-success及物理hardgate不变。V2133记录器对NumPy布尔值序列化失败，保留3个原始输入的5个返回；原始open输出缺失，严格记unknown/unreviewable。V2134仅运行尚未执行的5个minimal分支和1个原始occupied负例，不重跑已执行或缺输出的原始open。修复只对JSON类型做.tolist并逐次保存返回，不放宽结果门。该数学对照不是新车辆或正式成功率。

新组准入条件按顺序执行：

1. 共同传感机制：所有参与方法同等获得公开地图、当前测量、自身动作记忆及原历史camera/depth通道。不同轨迹产生各自因果观测，不要求实际packet字节相同。原camera是目标方向/范围5维，depth为离散射线模拟，不冒充RGB或真实深度图；噪声、采样频率、延迟与缺测策略须先统一冻结。真值仅在隔离的传感生成/评价器内部，算法不可读障碍坐标或未来actor。
2. 每个方法先在独立公开开发任务证明直行、可行弯道、停车、必要换挡和静态避障能力。通过API/一次控制/1秒闭环都不代替完整导航能力。PRIEST初态约束不合不能进入正式试验；SCCR不得补零或用masked变种冒原版。
3. 明确方法身份及适配，固定相关/有竞争力对照和事前等额开发预算。PSF/PCBF是安全过滤机制，须固定相同名义导航器、模型、误差和终端策略；不借用未满足前提的原论文安全定理。共同物理监督器拒绝率和原因单列，不能只写成原算法导航失败。
4. 能力门通过后冻结最终版本、全任务输入SHA和主/次终点与时间/计算预算，再运行新的分层确认任务。原安全门不降，失败/技术中断/未执行全部保留。新地图、actor相位和多actor是分开的研究因素；不把已暴露输入作为新确认。

以上有部分真实车辆和软件结果，有部分待实现依赖，不能表述“四种正式对照均启动”或“公平比较已完成”。目前没有新的正式claim。V2131两组件runtime均完成实际远端block/member/whole/indexSHA和exacteligible运输清理，原车模型线空闲；V2134为有限CPU6数学后台任务。所有Stage资源保持隔离，无新训练/实机。


## 2026-11-27T12:13:11.372299+08:00 追加：PCBF候选资格与真实后台

V2134未执行的6个数学case现真实完成11个NLP返回并完全远端校验/精确运输清理。minimal分支3个保存current输入及独立open均aux/performance status0、原残差门通过；current5/10仍有约.002的收紧slack，但原ideal全体raw几何仍通过。旧额外zero-slack gate把这些数学上合格、硬几何合格的候选挡掉，不应当成PCBF原生方法失败。

V2135单一新PCBF暴露开发组件已实际后台启动（source18415/sole2347ce31b836bee61d3302e60546fcd27deb0f75，source115members89676B每实际远端block/member/whole/indexSHA及cleanup/sourcechain通过）。仅删除额外zero-slack提案限制；仍要求严格优化status+residual、原ideal硬几何/command域，以及逐次完整原车10+2200shadow、5+2200admission及实际/接触/重放门，完整保留每次预测slack。名义控制、车辆模型、物理净空等原阈值全部不改，不宣称满足原PCBF终端/不确定性定理。

最近记录PCBF已9次求解/45正常步，仅partial，最终以机器RESULT/独立审核/COMPLETION和runtimebarrier共同判断；尚无全程成功或正式claim。PSF已闭组件不重复。SCCR186特征和原车采样、PRIEST朝向足迹表示仍未资格，不能称四个正式都在跑。本报告/launchcheckpoint晚于封档本地材料，不追加旧sourcepush或重封runtime。
