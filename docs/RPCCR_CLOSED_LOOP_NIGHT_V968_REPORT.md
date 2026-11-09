# V968实测RPP闭环交接与有限通宵动态链

结果：**NOT_PASSED**。唯一总截止2026-11-10 08:00+0800（1794268800.0），实际关闭1794235317.6080883。
用户在原V962失败/夜链未启动后明确“继续开启通宵的”，本轮独立授权；旧失败和23:45:42.425截止保持。

## 修改与资格

整路算法/模型/原生控制器精确V963；新组件使用真实安装的FeasibleRPP FollowPath、真实位姿反馈及原转向连续发令/安全准入：先.20m前向弯行，实测刹稳并保持弯轮，再以因果实测转角构造连续1.2m空间参考，持续闭环跟随。没有以固定速度开环走满12秒，也没有原地回正。
V962的7.42cm时间位置/4.72cm几何路径/约2°航向失败保持；本轮是实际空间闭环验证，不宣称旧固定速度时间跟踪误差修复。所有原逐命令.02非反向位置/.035航向预测—监控门不降；组件空间门.04m/.035rad、前向>=1m、目标.04m、完整刹停、原生净空.15/控制自体接触/完整自身重放均必需。组件RPP终点.02m比整路.20m严格。
真实Nav2预目标8项通过；完整真实RPP两动作软件演练通过，使用明确非物理运动学peer，0模型/积分，不当物理证据。首演练的合成peer发送超时造成TF缺失和生命周期启动超时保留，修正的是夹具发布节奏/背压处理；没有发生模型或物理入口重跑。新独立几何/审核负例与全部依赖/原固定表资格详见ZERO_MODEL_QUALIFICATION。

## 实际分账

|组别|尝试|通过|实际原生|自身控制重放|私有|
|---|---:|---:|---:|---:|---:|
|component|1|0|2794|2794|0|
|we_development|0|0|0|0|0|
|regression|0|0|0|0|0|
|confirmation|0|0|0|0|0|
|confirmation_repeat|0|0|0|0|0|

真t0尝试0，完成0，0积分；未产出初始化账目保留未知。
固定24已执行0、未执行24。不完整24不报全24率；开发/组件/重复不混分母。
固定10110001–24和原11/9已锁定但未执行的连续相位保持；三路线8/方向12，门>=23/24、路线7/8、方向11/12，第二功能失败或首次安全/证据异常停。固定1/9/17完整重复不换槽。异步重复要求相同完整模型/规范初态及两次功能安全与各自完整状态控制重放≤1e−8，不冒称整导航轨迹逐步相同。
组件独立结果：False；跟踪：未完整产出；实际前向：未知m。
停止诊断：{'error': "AssertionError('FIRST_FUNCTIONAL_FAILURE v968-closed-handoff')", 'traceback': 'Traceback (most recent call last):\n  File "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v968_rpp_closed_loop_night/campaign.py", line 59, in main\n    component=navigation(tasks[0]);dump(O/\'COMPONENT_GATE.json\',dict(passed=True,row=component))\n  File "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v968_rpp_closed_loop_night/campaign.py", line 47, in navigation\n    if strict:assert row[\'passed\'],\'FIRST_FUNCTIONAL_FAILURE \'+t[\'run_id\']\nAssertionError: FIRST_FUNCTIONAL_FAILURE v968-closed-handoff\n'}。

## 范围及收尾

原19静态体/单直径.20幅.25欧氏速.08actor/.32周期先验/3m测距5%漏检与模型网络不改，真值仅物理感知与离线评价。发现前较弱静态反应式合同/公开3m起步先验保留；实际行驶发现—因果新参考—实际续行>=1m—目标<=.45和停稳均必须。当前.2s命令+2s刹停经验管不是旧328步定理，不宣称任意遮挡/多actor/地图/实时/递归安全/RAS保证。即使本轮通过，对照/消融/实机与论文创新论证仍另立。
首异常闭批，冻结后无修补/候选/重跑。训练/SAC/实机0，Stage隔离；REVIEW_PENDING原字节恢复，模型授权关闭、锁空闲。源SHA全回读，必要原始状态/控制/传感/模型/实际审核/失败证据完整归档并逐成员SHA验证；同仓库Git/Release远端下载回读通过才按清单清理。单次新push30s及HEAD核验5s，失败不重试、未远端核验数据保留，原批同步不调用。
