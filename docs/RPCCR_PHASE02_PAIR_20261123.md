# 第2相位正式配对：预检未产生到达收益

两项均按原锁表完成，未重跑、改参数、换seed或修改冻结科学源。相位4.551718764234382、原传感seed10060001、已知WE课程/模型/起终点/单actor保持相同；顺序no_onward→full。两项SOURCE均为V1649，冻结SHA和全部13200成员相同。每项各一次规范初始化，内部factory模型构造次数未知。

|项|full|no_onward|
|---|---:|---:|
|到达原任务目标|否|否|
|actual native|39320|39320|
|自身完整重放|39320，误差0|39320，误差0|
|contact mismatch / bad contacts|0 / 0|0 / 0|
|独立实际前缀数值安全审核|PASS|PASS|
|最终距原目标|2.534647053805079m|2.534647053805079m|
|实际最小间距|0.27698465551487667m|0.27698465551487667m|
|首拒绝|NO_MEASURED_HANDOFF_ONWARD_SOURCE|同左|
|secondary errors|无|无|

两项均包括39120步之前的执行及最后200步原零命令closure；真实每5native闭轮传感记录完整。独立prefix审核不是whole-goal审核，也不是导航成功。原controller与memory数值重算误差均为2.2898349882893854e-16，不记作0。

## 可复核的机制结论

保存数组比较核实：初始完整状态逐成员字节相同，初始测量packet除真实墙钟测量时间外一致，公共场景/限制一致。两项39320步qpos/qvel/ctrl/mocap/time、实际请求，以及clearance/self-margin全部逐元素或逐成员字节相同。没有执行分叉；图中曲线因此完全重合。这是单个已知课程新相位的有限null result，不能推出所有相位中预检均无效。

full确实执行了额外预检：名义完整参考8700native、prefix2600native、refuge0、名义composition_error0，执行前检查通过。随后实际handoff的onward有限搜索仍拒绝；两项记录同为3571nodes、terminal_attempts0、best distance0.599417m。这不是全局无解证明。

full多出q1159恢复子集CPP4174900/Python12200；normal/static/其他FFI及内部总工作仍未知，不称equalwork或总工作精确差。预检不是未运行，它在本例没有改变候选提交或实际任务结果。

## 名义衔接与实测衔接的边界

原存档数组显示，full实际handoff相对名义参考末点位置差0.006571707m、航向差0.000149332rad、虚拟转向差0.001066748rad，均处于原4cm/.035/.015跟踪门以内；controller memory也不是名义值。这说明单点名义续接证据在本例没有保证实际重新规划成功。状态/memory差、观测source更新、有限搜索不完备三类影响尚未通过反事实实验分离，不能把失败唯一归因于其中之一。未重算模型、重放或补审旧case，也未调门限救结果。

论文可以写：本相位下预执行onward预检未改善到达，当前安全执行/停车证据与任务可持续完成需要分别陈述。尚不能写机制普遍优越、保证进度、全局不可行、统计优势、新地图/多actor泛化、实时或硬件结论。

## 图与原始出处

图中仅显示已知静态几何，移动actor未绘制；所有控制只使用原因果观测。两条实际曲线及距离/clearance曲线完全重合。

![phase02实际配对](../runs/v1742_formal_runtime_recovery/phase_02__full/figures/phase02_pair.png)

图PDF/PNG、PAIR_ANALYSIS、HANDOFF_BOUNDARY_ANALYSIS、全部trace成员字节比对和CSV在runs/v1742_formal_runtime_recovery/phase_02__full。每项原COMPLETION/actual RESULT/独立prefix审核/完整Nplus1/ownreplay在runs/v1643_formal_parent_metadata/rounds对应目录。总正式账为4closed非成功/16unexecuted；所有20分母保留。旧phase01的审核缺口不补审，旧周末和四个exposed operationalpilot账完全独立。

两项均已完成fullactualremote每block/member/whole/indexSHA、精确运输duplicate清理及canonicalbarrier。full首次运行归档123members/39847593B实际回读全部通过，包含本次图、配对分析、论文快照和书目核验。远端Release为phase-v1649-phase-02-full-runtime-20261123；source仅历史fc909e02 ref核验，无第二push。下一固定phase03配对尚未启动。本闭环更新晚于首次封档，原快照保持不变，不重封旧档。分析/制图为CPU4非模型数学，全部新增model/planner/physics/replay调用0；不作为额外试验样本。自动运行保持删除。
