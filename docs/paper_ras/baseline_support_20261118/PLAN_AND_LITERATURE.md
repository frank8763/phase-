# V1281之后的对比算法、论文依据与实验计划

核查日期：2026-11-18。当前任务仅研究与计划：0新模型、0积分、0训练；REVIEW_PENDING保持。以下方法是建议的比较对象，均不冒称已经在当前车辆上通过资格。本文件替代旧计划中“V1248尚在运行”的当前状态描述，旧失败结论保持。

## 已有成果与下一步目标

V1281已完成原固定24主任务24/24、三路线各8/8、两个方向各12/12及固定三次完整重复；完整成对状态/控制误差0。成功版本、必要证据及依赖已在[GitHub Release](https://github.com/frank8763/phase-/releases/tag/phase-dynamic-fixed24-v1281-20261118)备份并下载/解压SHA回读。[本地验收报告](../../RPCCR_CAUSAL_TIME_WINDOW_FIXED24_V1281_REPORT.md)记录原始分母与所有门。

下一步工作是建立公平比较接口、验证外部方法、完成机制消融与新测试，而后再做实时性和实机。现有24项作为公开开发/回归集；已反复用于修订，不能当未见泛化测试。当前证据没有完成正式基线对比、消融、实时闭环或实机验证。

## 推荐的比较对象

|方法|实验定位|论文与原始资料|当前项目适配判断|
|---|---|---|---|
|Nav2 Ackermann MPPI|首要预测控制主对照|[Williams等，T-RO 2018](https://arxiv.org/abs/1707.02342)，[官方1.3.13实现说明](https://raw.githubusercontent.com/ros-navigation/navigation2/1.3.13/nav2_mppi_controller/README.md)|本地有V929工程资产，可复用资料和接口经验；其中修改过采样可执行性，不能不加说明便当原生MPPI。须重新按当前执行器/模型资格。|
|RPP＋公共可执行全局规划器|工程跟踪参照|[Macenski等，Autonomous Robots 2023](https://arxiv.org/abs/2305.20026)，[官方实现说明](https://raw.githubusercontent.com/ros-navigation/navigation2/1.3.13/nav2_regulated_pure_pursuit_controller/README.md)|优先与MPPI完成共同接口。RPP以跟踪为主，动态避障完整系统须有可更新的全局路径及其原碰撞检查；不能让它跟随失效固定路径，再据此断言RP-CCR规划更强。|
|PRIEST / 选定的D-PRIEST变体|首要投影采样强对照|[Rastgar等，RA-L 2024](https://arxiv.org/abs/2309.08235)，[作者代码](https://github.com/fatemeh-rastgar/PRIEST)|先核查车式运动学映射、完整足迹和低层控制闭环，再准入。标准与分散变体选择须事前固定，不在失败后换更有利版本。|
|TEB，同伦类别搜索开启的明确配置|非完整运动约束、拓扑与轨迹优化对照|[Rösmann等，RAS 2017](https://doi.org/10.1016/j.robot.2016.11.007)，[作者/机构实现](https://github.com/rst-tu-dortmund/teb_local_planner)|有车式机器人依据。上游当前为ROS1/noetic分支；先衡量独立优化核心接入成本，不未经验证替换现有仿真或整个运行环境。|
|SVG-MPPI|现代多模态采样扩展对照|[Honda等，ICRA 2024](https://arxiv.org/abs/2309.11040)，[作者代码](https://github.com/kohonda/proj-svg_mppi)|针对多模态动作分布的车辆控制。作者代码列出ROS Noetic；可在TEB接入过重时，作为优先评估的扩展对照。不是Nav2 MPPI的现成开关。|
|PSF / PCBF的明确车辆适配|安全与可行性恢复近邻，单独机制表|[Wabersich与Zeilinger，Automatica 2021](https://arxiv.org/abs/1812.05506)，[同作者，TAC 2023](https://arxiv.org/abs/2105.10241)|须统一名义控制器、模型、约束与终端条件后比较安全干预、恢复和到达。不是无需适配的Nav2导航插件；适配未完成不能填成已复现的基线。|

实际顺序建议：先MPPI与RPP共同接口和小试；接入PRIEST；TEB与SVG-MPPI依据可验证的接入成本，先选择其中一个扩展方法。PSF/PCBF作为创新边界必读材料，并准备同名义控制器的机制比较。不要同时搭建六套未经资格的运行栈。

## 论文究竟支持什么

### MPPI：采样预测控制依据

Williams等从信息论角度推导采样控制，并在车辆自动驾驶中验证。Nav2官方实现支持Ackermann，使用CPU向量化优化。论文与实现支持把它列为采样预测控制参照；不能把官方其他机器的频率直接写成本车速度。[论文](https://arxiv.org/abs/1707.02342)；[固定版本实现](https://raw.githubusercontent.com/ros-navigation/navigation2/1.3.13/nav2_mppi_controller/README.md)。

本项目判断：保留已记录的上游1.3.13来源和SHA，先评估其当前适配，避免无依据升级。需要改变模型或采样约束时，公开标注“MPPI＋车辆可执行性适配”，同时记录上游原算法与适配层的区别。

### RPP：把跟踪能力与恢复能力分开

RPP引入调速和碰撞检查，作者提供Nav2参考实现；其官方说明要求搭配机器人能跟随的路径规划器。它适合作为成熟跟踪参照，单独运行不等于完整动态规划系统。[原论文](https://arxiv.org/abs/2305.20026)；[实现说明](https://raw.githubusercontent.com/ros-navigation/navigation2/1.3.13/nav2_regulated_pure_pursuit_controller/README.md)。

本项目判断：禁止车式底盘原地旋转指令；倒车、曲率、停车与末端目标行为须按同一实际执行器接口资格。公共全局规划器与更新频率须写入方法名称和配置，不能只标注“RPP”。

### PRIEST：有GPU与车式示例，但不是直接可用的本车控制器

PRIEST以可行域投影引导采样。原文V-A使用JAX GPU后端；BARN/动态主比较使用全向双积分模型，V-B4另有通过微分平坦性映射的车式D-PRIEST示例。因此既不能说它只适用全向机器人，也不能直接把其主表性能当作本车可达性证据。[作者全文II-A、V-A、V-B4](https://arxiv.org/html/2309.08235v1)。

本项目判断：重点检查曲率、低速/停车时映射的数值问题、转向滞后、驱动积分记忆、控制变化率、整车矩形足迹及实际跟踪。作者仓库使用ROS和JAX，并表示欢迎ROS2实现贡献，不能称作当前Nav2即插即用插件。[作者代码](https://github.com/fatemeh-rastgar/PRIEST)。GPU型号、依赖和资源分配未验证前，不承诺本机GPU提速。

### TEB与SVG-MPPI：拓扑和多模态参照

TEB论文考虑差速与车式非完整约束，并优化多个拓扑类别的候选轨迹。[RAS原文页面](https://www.sciencedirect.com/science/article/pii/S0921889016300495)。SVG-MPPI针对多模态动作分布，用引导分布选择目标模式，作者给出车辆实验和实现。[原论文](https://arxiv.org/abs/2309.11040)；[作者实现](https://github.com/kohonda/proj-svg_mppi)。

本项目判断：这两者比只比较朴素跟踪器更能检验“另一条可执行避障路线能否产生”。适配费用、几何/动力学约束及感知输入资格决定先做哪一个，不能因为某个实现未调通就把工程失败当成算法性能。

### PSF/PCBF：必须正面处理的创新边界

2021 PSF根据当前状态预测候选输入的约束满足情况，并以模型预测形式提供修改与后备。2023 PCBF进一步研究原安全过滤问题失去可行性后的恢复，提出软约束辅助问题及终端屏障条件。[PSF](https://arxiv.org/abs/1812.05506)；[PCBF全文](https://arxiv.org/html/2105.10241v2)。

2026年的相关工作继续研究稳健PCBF与控制目标的结合，已由出版社元数据核实为Automatica 189, 113009；此处仅作为更新的相关工作入口，未声称已复现其算法。[论文DOI](https://doi.org/10.1016/j.automatica.2026.113009)。

本项目判断：不能声称“安全过滤或可行性恢复”首次提出。可以检验的贡献候选是：在声明的观测与运动合同下，从完整实测车辆/执行器记忆状态建立可执行恢复入口，接通安全后续目标路线，并用因果时序选择恢复通行。它是否超出现有工作，需要同源消融、近邻方法比较和必要的理论分析；当前24/24不是这项新颖性结论的证明。

## 先解决方法定义与先验公平

当前冻结代码`experiments/v1281_partial_reconnection_fixed24/route_dispatch.py`按登记路线选择WE/NS/EW恢复分支；验收报告也明确保留了已暴露课程提案。它是成功的受限系统配置，不能据此直接宣称任意地图上的单一通用规划器。

V1281保持冻结。下一阶段先记录每个分支输入、候选生成、课程模板和公开先验，把共用算法部分与课程配置分开。若论文要声称跨起终点/地图的统一方法，需要在独立新版本中按实测状态、目标及因果观测生成候选，去除按任务编号选法的依赖，并完成回归与新测试。该研究步骤不能冒充已经完成，也不能把旧24改名为未见数据。

同样必须列出本方法使用的已知地图、运动先验和提案库。外部方法获得等价的可用信息/初始化，或将“原生方法”与“共同先验适配方法”分别报告。不能只给RP-CCR公开课程模板和较强运动先验，再把结果差异全归因于安全恢复算法。

## 公平比较的共同合同

1. **车辆与执行器一致。** 同模型、地图、起终点、actor轨迹/相位、整车足迹、控制频率定义和实际执行器。共享(v,omega)到实际轮控的低层接口及物理限幅/速率门。所有方法的预测模型、参数辨识与开发预算均公开。物理可用域从当前资格导出，不把旧MPPI的速度配置直接与当前方法相比较。
2. **感知机制一致。** 同3m、32射线、原漏检/噪声机制和登记随机种子，各方法由自己的实际位姿生成观测。轨迹不同，完整传感包不会逐字节相同；只有保存态组件对照才用完全相同输入包。物理真值只用于仿真传感和离线评价，不作为在线障碍位置/未来轨迹输入。
3. **先验和预测明确。** 原方法的周期/速度先验、候选提案和估计状态应列明。需要预测障碍状态的PRIEST等使用因果估计输入，不能直接读取模拟器actor真值。使用共同预测器的适配版须单列，不冒称原论文无改动实现。
4. **外部指标与内部证书分开。** 共同成功指标使用到达<=.45m、原实际停稳合同、净空>=.15m、坏接触/穿透/未知接触0、合法ctrl/速率及完整自身重放。发现→2200刹停→内部重规划等RP-CCR专用机制，单独作为本方法链条核验，不强迫能平顺绕行的外部算法必须停车或输出相同证书。
5. **原生安全处理保留。** 保留各基线自己的碰撞检查、约束与后备。公共仿真终止监视器不提供有利控制输入；若加入统一安全层，必须对全部相应方法同等加入并单列干预次数。不能把本方法恢复器强加给全部外部基线后仍称原生比较。
6. **预算可解释。** 主表采用同硬件、同实际决策截止，记录采样数、迭代数、预测时域和调参预算；另做相同样本/传播预算的诊断。不要求本质不同的优化器机械使用相同样本数，也不能给一方无限计算时间。
7. **算法失败与工程异常分账。** 未到达/安全停驶/任务超时是结果；导入、模型不一致、真值泄漏、记录/控制异常是工程问题。是否允许某类逐回合失败后继续原清单须在新比较协议中明确；源/模型/控制/证据异常全批停。未执行标NA，不填作0次成功或完整失败率。

## 建议的实验顺序与每步交付

|顺序|工作|通过条件/产出|
|---|---|---|
|1|统一观测、状态、命令和独立评价接口；审计路线配置与提案先验|可核验接口schema、信息公平表、上游版本/改动清单；复用原通过资格，仅重验变化部分|
|2|MPPI、RPP的当前车辆资格与小规模公开开发|先零模型拒绝例/真实调用口，再另立有界物理组件、三路线公开小试；失败定位到接口或算法，原成功版不改|
|3|PRIEST车式及GPU后端资格；选择TEB或SVG-MPPI扩展|全足迹、转向/倒车/停车/速率合法、因果感知和实际跟踪均过；未过不能列入“已复现”表|
|4|固定24公开回归比较与同源机制消融|所有方法冻结后配对运行，同一评价器；此处用于开发、机制与回归，不作泛化主证据|
|5|预注册新测试，冻结全部算法与调参|先新相位/噪声组合，再独立起终点/地图；后者须先有通用提案生成资格。样本量由先导差异与预算决定，不承诺某个样本数必然显著|
|6|真实时间闭环与硬件接口资格|计算中环境时间连续推进；记录超期及后备；仿真全链通过后再实机接入、受控静态与单动态验证|

准备效率：先用15分钟检查点明确MPPI/RPP接口可复用范围和阻塞，不重复全历史资格或下载全部3.9GB证据。仅按需恢复对应保存态。PRIEST/GPU接入若遇到依赖、数值或动力学障碍，先给出具体缺口，不无限等待安装，也不以未合格实现填论文表。此为工作建议，不是已启动的物理窗口。

## 必须做的同源消融

|消融|保持不变|主要检验|
|---|---|---|
|去除主动恢复入口构造，仅保留原保守停止|相同模型、候选普通分支及安全评价|从安全停驶到重新推进是否依赖入口构造|
|取消完整后续目标衔接，只保留原短段安全|相同实际安全终止、基本控制和预算|局部能动是否足以稳定到达；不能执行未经安全准入的动作|
|去除因果起步时间窗，仅用原wait=0|控制形状、因果域、全部完整安全门|几何路线相同而动态时序不同的效应|
|去除分段储备，采用事前固定的统一储备|同模型、实际门、候选预算|保守性与跟踪误差、恢复准入的权衡；不能事后挑更有利阈值|
|去除课程提案/统一公共初始化|同原始信息、计算与调参预算|成功依赖模板先验多少，是否具有跨课程适应性|

先用完全相同保存态做机制核验，再对合法、可执行的变体另立真实运行。保存态消融不是车辆成功率；确定性完整重复不扩大独立样本数。一次改一机制；若改动使控制器不具备安全执行条件，报告拒绝或保守停驶，而不是绕过门执行。

## 结果表与实时性

共同主表：全任务成功/失败/未执行、最小实际净空、接触/穿透/未知接触、控制合法性、停驶/恢复/干预次数、路径长度、仿真到达时间。时长与路径长度需配对报告共同成功子集，同时保留全部失败/超时，不能因失败提前结束而显得更快。

效率表分开：感知、估计、提案、认证、控制提交/生效、物理积分、自身重放、离线独审。记录端到端p50/p95/p99/max、超期率和所用CPU/GPU/精度/采样预算。JIT冷启动单列，热身后的端到端耗时仍含必要数据传输。GPU批量吞吐不等于单车实时性；先实测再按传感与停车合同确定决策周期。

GPU路线首选评估PRIEST的作者JAX实现。Nav2 MPPI固定版本是优化CPU实现，不能只设置CUDA变量便称GPU化。[Nav2固定版本说明](https://raw.githubusercontent.com/ros-navigation/navigation2/1.3.13/nav2_mppi_controller/README.md)。本聊天不检查Stage进程或显存。沿用户报告的Stage CPU8/10/12，Phase CPU2–5与其物理核/超线程不重叠；GPU设备分配须另核定，当前没有经过资格的GPU实现。

## 可直接引用的书目信息

以下完整字段见[REFERENCES.bib](REFERENCES.bib)，由出版社提交的[Crossref元数据核验记录](BIBLIOGRAPHIC_VERIFICATION.json)交叉确认。作者预印本与作者实现用于算法内容核对；元数据核验不等于完整复现实验。部分出版社全文受访问限制，未冒称阅读全文。

- Macenski, Singh, Martín, Ginés. *Regulated Pure Pursuit for Robot Path Tracking*. Autonomous Robots 47(6), 685–694, 2023. DOI：[10.1007/s10514-023-10097-6](https://doi.org/10.1007/s10514-023-10097-6)。
- Williams, Drews, Goldfain, Rehg, Theodorou. *Information-Theoretic Model Predictive Control: Theory and Applications to Autonomous Driving*. IEEE Transactions on Robotics 34(6), 1603–1622, 2018. DOI：[10.1109/TRO.2018.2865891](https://doi.org/10.1109/TRO.2018.2865891)。
- Rastgar, Masnavi, Sharma, Aabloo, Swevers, Singh. *PRIEST: Projection Guided Sampling-Based Optimization for Autonomous Navigation*. IEEE Robotics and Automation Letters 9(3), 2630–2637, 2024. DOI：[10.1109/LRA.2024.3357311](https://doi.org/10.1109/LRA.2024.3357311)。
- Rösmann, Hoffmann, Bertram. *Integrated online trajectory planning and optimization in distinctive topologies*. Robotics and Autonomous Systems 88, 142–153, 2017. DOI：[10.1016/j.robot.2016.11.007](https://doi.org/10.1016/j.robot.2016.11.007)。
- Honda等. *Stein Variational Guided Model Predictive Path Integral Control: Proposal and Experiments with Fast Maneuvering Vehicles*. ICRA, 7020–7026, 2024. DOI：[10.1109/ICRA57147.2024.10611021](https://doi.org/10.1109/ICRA57147.2024.10611021)。
- Wabersich与Zeilinger. *A predictive safety filter for learning-based control of constrained nonlinear dynamical systems*. Automatica 129, 109597, 2021. DOI：[10.1016/j.automatica.2021.109597](https://doi.org/10.1016/j.automatica.2021.109597)。
- Wabersich与Zeilinger. *Predictive Control Barrier Functions: Enhanced Safety Mechanisms for Learning-Based Control*. IEEE Transactions on Automatic Control 68(5), 2638–2651, 2023. DOI：[10.1109/TAC.2022.3175628](https://doi.org/10.1109/TAC.2022.3175628)。
- Didier与Zeilinger. *A multiobjective approach to robust predictive control barrier functions for discrete-time systems*. Automatica 189, 113009, 2026. DOI：[10.1016/j.automatica.2026.113009](https://doi.org/10.1016/j.automatica.2026.113009)。

没有复制整篇论文或下载大型代码/模型仓库；材料提供原文、作者实现、书目、比较理由、适配缺口和可执行的实验顺序。任何新的车辆运行仍需独立协议、完整资格和有界授权。
