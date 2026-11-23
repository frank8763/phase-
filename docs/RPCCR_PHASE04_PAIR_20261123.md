# phase04配对检查：两项完整成功，实际轨迹相同

原合同、同一冻结SOURCE V1744、同已知WE课程/起终点/模型/单actor、相位4.8689554913751625/原传感seed不变，固定顺序full→no_onward。两项各一次规范初始化，内部factory次数unknown，未重跑旧case或修改安全门。

|指标|完整方法full|去除执行前onward预检|
|---|---:|---:|
|原完整科学结果|PASS|PASS|
|实际执行步数|47320|47320|
|自身完整重放|47320|47320|
|state/ctrl/mocap最大重放误差|0|0|
|完整独立数值/物理审核|PASS|PASS|
|最终距目标m|0.24247824628184625|0.24247824628184625|
|最终平移速度m/s|0.0000074846189933|0.0000074846189933|
|实际最小间距m|0.27698465551487667|0.27698465551487667|
|坏接触/重放接触不匹配|0 / 0|0 / 0|
|首错/secondary|无 / 无|无 / 无|

原BASE逐47320row重算ctrl/memory误差均为2.2898349882893854e-16，不是0。整体完整独立actualaudit physical_audit_complete=true；其中goal analytical subaudit的同名false只表明该子层没有新物理积分，不能错读成整体物理审核失败。

## 配对结论

保存的初始全state逐NPZ成员字节相同，packet除真实wall测量时间外一致，科学任务和source一致。全部47320步qpos/qvel/ctrl/mocap/time/请求逐元素一致，完整NATIVE_TRACE每个成员（含clearance/selfmargin）SHA也一致，没有执行分叉；本图两条线完全重合。完整方法的初始名义预检确实执行，接受8600native完整参考及2600native初始prefix；消融只生成同一2600prefix，后续实测onward仍执行。

所以，本相位两项都能成功，未观察到执行前onward预检改善到达、路径或实际步数，不能把这对成功写成机制收益。也不能凭一个相位否定该预检在所有任务的作用。full多出q1159已跟踪CPP3940600/Python12000子集native工作；normal/static/其他FFI及内部总modelwork未知，不作总成本或equalwork结论。

![实际轨迹与原门](../runs/v1748_phase04_pair_review/figures/phase04_pair.png)

图仅展示已知静态几何，没有绘制移动actor；在线仍只使用原因果测量。PNG/PDF及CSV位于runs/v1748_phase04_pair_review/。它们来自已保存数组的CPU4数学，不增加任何模型/规划/物理/重放/独立审核或统计样本。本次晚分析/图片尚不在此前已封的runtime档案中，未重封旧档。

## 证据与当前状态

full原runtime99members46626504B与no_onward100members46328080B均已实际远端每block/member/whole/indexSHA核验，精确重复运输清理及canonicalbarrier通过，全部原始anchors保留。独立文件日志的后台no_onward pipeline完整结束，REVIEW原字节/锁闲/ownedchildren与controller均已退出。原full旧monitor退出原因仍未知，其已完成模型与审核未重跑，只补齐元数据及I/O。

正式账8/20已关闭，其中2项完整PASS，6项非成功含技术审核/准入缺口，12项未执行。不能把异质技术censor和已知课程相位简单写成独立泛化成功率。旧weekend、exposedpilot与历史SCCR/DWA比较分账不变。

当前等待用户审阅，本次只检查与展示结果，没有启动下一实验。NS/EW剩余12项仍需要对应源/输入/接口准入，不能直接套WE运行。
