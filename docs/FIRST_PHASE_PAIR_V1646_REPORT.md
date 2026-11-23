# 首个新相位机制配对：两支均未到达

原V1281合同、WE原sensorseed10060001，仅相位改为预锁定2.2609711555894934。full和no_onward按固定顺序各运行一次，闭批后不补跑或补审核。此为一个同课程相位，不支持统计优势或新地图泛化。

|分支|原首功能拒绝|actual / own replay|独立前缀审核|
|---|---|---:|---|
|full|NO_CURRENT_WHOLE_GOAL_SOURCE|36625 / 36625|导入route_tools失败，未执行|
|no_onward|NO_MEASURED_HANDOFF_ONWARD_SOURCE|39425 / 39425|执行至传感覆盖门失败：200错误停尾缺40条5native扫描|

两者goal success均false，各自身全状态/控制/mocap重放最大误差0、contact mismatch0。no_onward保存完整39426个N+1状态、39425动作和接触数组，但不能把传感缺口下的capture称为全合同完整证据。原RESULT/首错/secondary均保留，未重建任何缺失测量。

对已保存数组和journal作零模型比较：两分支前36425个已施加动作、控制memory记录和36426个全状态（qpos/qvel/ctrl/mocap/time）逐值完全相同。比较不新增模型积分、Allocator重算或物理重放。full随后进入200错误停步；no_onward选中refuge0并执行600运动+2200完整停止的局部段，随后实测handoff的onward搜索失败，再施加200错误停步。no_onward额外执行2800native，最终目标距离2.3633506217630424m；full为3.0286572839576253m，均未到达。

该单对可支持的机制观察是：执行前onward预检在此相位提前拒绝了一个局部可执行、但本次实测handoff有限搜索仍无法续行的前缀，因此避免了一次2800native局部执行。两支都没有产生整程到达，不支持到达率收益、全局不可行、安全保证或普适机制优势。独立前缀审核缺口明确限制证据强度，不能用无接触telemetry替代通过。

no_onward规范init返回1、内部factory模型构造次数未知；q1159恢复子集CPP23842000/Python12800、Engine返回11/Predictor返回4、内部Allocator构造数未知。完整normal/static/其他FFI模型工作仍未知，原审核与子集计数有重叠不加总，不声称equalwork。审核源码已越过39425步Allocator ctrl/memory循环及其门，后在传感覆盖门拒绝；这是从执行trace位置推导的部分覆盖，不是独立完整PASS。

正式20项现2项已关闭非成功、18项未执行；累计76050actual/76050ownreplay、2规范init返回，internal unknown。已暴露pilot与旧weekend账完全分开。下一先V1648一次distinctruntime全部远端块/成员/整流/index SHA核验与精确运输清理，再仅修后续错误停尾实际扫描记录，原科学参数/候选/phase/seed/门不动，按原顺序phase02no_onward。

证据：runs/v1643_formal_parent_metadata/rounds/phase_01__no_onward/{RESULT在actual中,RUNTIME_CLOSED_REVIEW,PAIRED_MECHANISM_OBSERVATION,ERROR_STOP_SENSOR_GAP_DIAGNOSIS}.json。保存状态比较与诊断是零模型源/数组审阅，不是补跑已闭任务。
