# 周末研究进展 · 2026-11-27

当前正式共同对照仍为120项固定分母：72关闭、7完整到达、53可核验功能拒绝、12技术删失、48未执行。下列开发结果不并入正式成功率。

- PSF：999次求解、4995正常步后因记录字节授予耗尽中断；随后完成200步原错误停车。5195实际步与5195重放误差0、接触不一致0；1998预测轨迹首次独立前缀审核通过。端点位移3.8349917255771095m，原目标尚距4.472713391469523m；未发现actor，不能声称动态避障或到达。原失败、原源码均保留，远端10133成员/28465712B逐项SHA与清理屏障已闭。
- PCBF：固定单位变换保留原优化目标、约束、严格成功/残差/硬几何门。原失败输入query081的辅助状态由8变为0；四个已保存输入及开放正例均通过，车辆占用负例仍被硬几何门拒绝。12次新NLP已完整保存并完成首次算术审核，未追加求解。真实车辆验证尚待。末尾stdout的NumPy布尔序列化错误保留为外层技术失败，未覆盖原记录。
- SCCR：保存测量状态/深度的3帧完整联合传感拼接软件检查通过；两份冻结107/186维策略已分别完成3次真实前向，与原SB3批输出最大误差5.96e-8/4.17e-7，均小于原1e-6门，均非逐字节相同。0物理步、0训练、0正式任务。V2165入口技术失败保留，一次最小绑定修正后的V2166组件已远端证据闭环。实时联合传感、Phase21/22风险融合与完整控制链仍未验收，不能称完整SCCR已运行。
- PRIEST：精确朝向矩形在现有50栅格点输入仍有1项初态冲突；公开精确向量地图的同一初态却保有0.001465883973069404m原预测余量。问题涉及车辆近似和栅格保守性，不能只换圆盘数量；原安全余量未降低。
- 记录格式：对全部9994条关闭JSON进行内存内无损字典流试验，逐字节SHA及原压缩包重构SHA吻合，但只节省12.7%，不足以解决完整路线容量及审核时间问题，暂不部署。

PCBF100原车组件因准备阶段耗尽启动预留而未执行，保留V2162关闭账，不是数值失败，不延长旧窗口或重复该资格。下一项优先为SCCR实时联合传感及原风险融合/内部控制链，在独立新源码下先完成能力验收，再进入相同相机/深度的新确认组。

周末按本地时间周日2026-11-29 09:00收尾、07:00停止新增原车轮次安排。同一聊天工作续行已启用；后续不需要逐轮人工批准。科学结论不以运行时长、源码版本数量或进程退出码代替。

主要机器证据：
- runs/v2151_psf_wrapper_identity_binding/components/PSF/RUNTIME_CLOSED_REVIEW.json（关闭后的晚审核报告，明确不冒称原runtime归档已含）
- runs/v2161_pcbf_conditioning_numeric_audit/RESULT.json（首次算术审核，0新增NLP）
- runs/v2155_sccr_full_observation_assembly/RESULT.json
- runs/v2164_sccr_measured_union_sensor/RESULT.json
- runs/v2166_sccr_import_binding_recovery/components/POLICY/RESULT.json（两冻结策略组件，不是导航）
- runs/v2157_priest_oriented_initial_geometry/RESULT.json 与 EXACT_VECTOR_SUPPLEMENT.json
- runs/v2158_metadata_stream_capacity/RESULT.json

所有旧失败、未执行槽位和未知内部总工作量保持原账。没有建立普遍算法优越性、未见地图泛化或新机制收益结论。

### 2026-11-27T18:16:43.390077+08:00：完整 SCCR 观测接口的源前验收

V2168 已实现当前测量位置上的完整传感联合生产器及107→186冻结策略接口。生产采样代码和独立审核分别通过三帧保存数据的软件测试及各15项负例；模型、渲染和物理边界在这些测试中均为显式替身。另在实际隔离命名空间确认四个未获准入口在读取模型前拒绝，公开静态地图路径检查通过。以上均不是新的实际传感、策略推理或导航结果。原先相机距离特征漏用原getter裁剪的问题已在首轮活体输入试验前修正；V2166仅证明给定输入上的后端近似一致性，不能据此声称完整原生观测等价。

当前共同120项仍为72关闭、7完整到达、48未执行。下一步为完成源/运输/容量/启动器验收并恢复远端证据链，然后才允许一次零学习控制的完整传感与冻结策略组件试验。

### 2026-11-27T19:00:29.803338+08:00：保留两项技术失败，完整SCCR能力仍待实测

V2168在创建车辆前因旧证明文件名缺失而结束，机器RESULT缺失及未知计数保留；源推导的零调用另列。V2169修复这一入口后完成1次车辆初始化，但在首次完整传感采样前，运行期全源哈希校验触及被原始隔离门禁止的历史BODY_COMMANDS文件并拒绝。原门未放宽。该轮完成200步错误收尾和200步自有回放，完整状态/控制/mocap回放误差0、接触不一致0，独立实际前缀审核通过；0正常控制、0完整传感帧，无导航或机制收益结论。内部factory模型/策略数未知，自己的新增策略与渲染调用源推导0与机器null分账。两轮原始失败和运行证据均已远端逐项SHA验证并闭账。

V2170只准备一次源校验生命周期修复：初始化前完整源验证与权限哈希绑定，运行期验证允许读取的源文件，原历史读取隔离门保持；缓存只有路径/哈希字符串。纯软件回归及新的已关闭预留核验通过，实际完整传感与策略组件仍未启动。现有共同120项继续保持72关闭、7完整到达、48未执行；这些组件不计入正式性能分母。

### 2026-11-27T19:36:42.362771+08:00：完整传感与双冻结策略组件实测通过

V2170在一项已暴露课程上取得原生步0/5/10的三帧完整186维观测，完成2个冻结actor的2次权重加载和6次推理；策略输出仅记录。实际执行10步零控制及2200步完整停车，共2210步及等长自有回放；完整状态/控制/mocap回放误差0，接触不一致0、坏接触0，最小实际净距0.31498918194116166m。独立审核核验三帧特征与五个完整预测剖面，未重复神经推理或渲染。内厂模型/策略/渲染数与完整工作量仍未知；q1159恢复子集Python11030/CPP0及6次PythonPredictor返回另列。

源29324项与运行147成员/6694713B均已在Release460506353逐块/成员/整包/索引实读SHA验证并闭账。该结果证明注册观测适配与冻结网络接口可工作，未验证完整SCCR风险融合、路径恢复、非零控制或全程到达。十方法相同传感包可用性的复制接口通过，不代表十个算法已执行。历史包装器传感调用节奏、相机别名适配及零动作历史的范围继续披露。原120正式任务仍为72关闭、7完整到达、48未执行。下一步用这三帧和实际actor输出核对原v3风险/安全盾/控制单位，不再重复本组件推理或物理试验。


### SCCR applicability boundary, V2171 (2026-11-27T19:51:23.518125+08:00)

Complete measured186-input/two-frozen-actor acquisition passed only as a log-only component (V2170). V2171 saved-input source arithmetic validates risk/shield interfaces but finds the historical environment performs post-step direct vehicle position/orientation/velocity corrections, incompatible with the common no-state-injection plant. Native full-environment SCCR is not a valid drop-in comparator. A separately identified controller-only common-plant adaptation remains unqualified; residual-policy output is not body velocity or a final safe actuator command. Three all-clear saved frames and synthetic risk/negative tests are not navigation outcomes. No new formal samples; original120 remains72closed/7whole/48unexecuted. See `docs/SCCR_CONTROL_CONTRACT_V2171_REPORT.md`.


SCCR control-adapter preparation (V2173/V2174): original inner-controller arithmetic, nonzero actuator-unit equations and recovery negatives passed on saved inputs only. Raw virtual requests exceed the shared speed domain. An explicitly labelled common-command projection passed software domain checks; it changes actuation interpretation and is not native environment equivalence or physical qualification. Any future shared-route controller-module comparison must be separated from full-system comparisons and disclose frontend/adapter policy uniformly. No new formal sample or navigation arrival. Details: `docs/SCCR_INNER_CONTROL_V2173_V2174_REPORT.md`.
