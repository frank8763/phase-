# RP-CCR机制收益与同课程新相位边界

用户选择V1281原仿真合同，全部原安全门保持：4cm/.035rad/.015转向跟踪、原预测储备、.15m实际间距、完整2200停止尾、逐状态/控制/mocap精确重放等。结果不声称满足周末新版合同。旧周末任务已按用户要求停止，science12及原分母独立保留。

用户随后明确取消09:00总截止，授权持续无人值守推进并保留安全异常退出与证据闭环。每轮5400秒（normal4200+close1200）及独立双钟是单轮技术上限，不延任何旧冻结窗口；没有新的整体日历截止。

12个新相位、20个适用运行项在模型前锁定；同一已知地图、模型、起终点、单actor与运动类，原传感seed保持，仅改变相位。EW四对full/no_time，WE四对full/no_onward，NS四个full不造无效消融。原V1281的24个已暴露任务不当新任务。推断仅限同课程新相位，不声称新地图、多actor泛化或统计优势。

时间消融保留原40候选计算，只取消非零等待的选择资格。衔接消融只取消执行前onward预检，原prefix反馈、连续shadow、完整停止证明和实测handoff后的onward重规划均保留。候选、数值参数与其他安全门不调。正式失败不重跑、不换seed；未执行项保留全部20分母。

## 当前可核结果

|用途/任务|状态|新增actual / own replay|可支持的结论|
|---|---|---:|---|
|已暴露WE03 full operational pilot，V1639|原合同完整链PASS|44750 / 44750|当前完整执行、保存与原独立审核链可用；不是新相位或机制收益证据|
|新phase01 full，相位2.2609711555894934，原seed10060001|CLOSED非成功|36625 / 36625|有限direct和两次refuge-onward搜索未找到当前whole-goal source；不能推断全局无解|
|相同phase01 no_onward|ACTIVE，结果待定|不预加闭账|配对完成前不能归因机制收益|
|其余18项|未执行|0 / 0|保留分母|

V1639原合同pilot全goal/stop、完整N+1、独立numeric/physical audit、自身fullstate-ctrl-mocap重放通过，重放误差0。原BASE_NATIVE_AUDIT逐44750步重新计算Allocator控制与memory，两项误差均2.220446049250313e-16，不能写作0。该pilot不计入正式20项，不构成新独立样本。

首个正式full的首错为原方法NO_CURRENT_WHOLE_GOAL_SOURCE，发生于feedback admission之前。保存selection显示direct1241nodes、terminal_attempts0、static拒绝3、dynamic拒绝2012，两次refuge-onward均失败。实际轨迹及36625步自身重放完整，误差0、contact mismatch0；但后续独立前缀审核因route_tools导入错误未执行，因此不宣称独立安全PASS。该审核缺口和功能失败永久保留，不补审旧case。V1646仅修后续未执行项的审核导入scope，正常策略/数值/phase/seed/安全门不变。

正式任务共用runs/v1643_formal_parent_metadata，来源版本可由每轮FORMAL_ADMISSION.source_version_root精确区分。当前配对使用已冻结V1646来源；2项已登记、其中1项已关闭，18项未执行。EW/NS的后端仍未获实际准入，不把其未执行从分母移除。EW两个公开proposal的旧恢复失败与partial原样保留，不盲目重试；WE不依赖它们。

## 计数与证据边界

q1159 work计数仅覆盖恢复子集，normal/static/其他FFI总模型工作未知；不声称equalwork。正式full的子集CPP32786000/Python0、Engine返回11/Predictor返回1，内部Allocator构造数未知。已暴露pilot的CPP16005616/Python47400及独立审核3752616存在重叠，不重复加总。规范init返回数与内部factory构造数分别记录。

已暴露4次operational pilot累计89900actual/44950ownreplay/3规范init返回，保留其中3次接口或资源失败，不混入正式机制结果。旧周末26starts/14partial/151210actual/105105replay/science12/newcontractwhole0保持独立。

首个正式full的全部runtime已由V1645实际远端逐block/member/whole/index SHA恢复核验并精确清理重复运输，原件全留。V1646新source由V1647完整恢复，13177成员链=13156继承+21新delta。当前运行raw尚未备份，不能外推source归档含其证据。每轮关闭、准确/未知计数、独立审核结果保存、完整远端恢复与精确运输清理后，才按固定顺序推进下一项。

相关事实以每轮COMPLETION、actual/RESULT、RUNTIME_CLOSED_REVIEW、POST_ROUND_STORAGE_BARRIER及FORMAL_LEDGER为准。首full的FUNCTIONAL_BOUNDARY_DIAGNOSIS是保存JSON零模型推导，不是新模型实验。
