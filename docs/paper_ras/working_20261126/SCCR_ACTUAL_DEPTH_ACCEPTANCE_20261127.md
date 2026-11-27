# SCCR真实深度采集验收：已执行并闭环

V2144已实际运行，2026-11-27约13:08:27启动、约13:09:12全部归档闭环。它只验证真实深度采集、当前状态绑定与原车完整停车，不是完整SCCR策略导航或新正式对照。

- 实测原相机查找名`d435i_depth`返回-1，现有`d435i_depth_camera`为id0；显式绑定现有相机，模型与原源码不改名。该适配可能改变历史策略的输入分布，尚未资格为原版完整SCCR。
- native0/5/10各取得1帧实际64×64深度图，原始24patch提取与独立重算一致；三帧均非全1默认值，特征范围约0.211–0.867。没有用软件夹具冒充真实采集。
- 10步零命令正常保持后完成2200步停车，共2210actual/2210replay；fullstate/ctrl/mocap重放最大误差0、接触不一致0、badcontacts0，最小实际净空0.31498918194116166m。独立5个完整预测profile及3个实际原始帧审核通过，controller/memory重算误差均0，无首错或secondary。
- canonical初始化1次、显式新renderer1个、显式策略/NLP调用0；factory内部模型/renderer/策略调用和Allocator/总工作量unknown。q1159已恢复subset仅Python11030/CPP0、6个constructor返回，不代表所有模型开销。
- 机器执行12.27秒、owner19.06秒；连同上传、逐实际远端block/member/whole/indexSHA与精确运输副本清理约45秒。运行137成员、6987348B，原raw保留，全部已知owner/child/IO身份退出，REVIEW精确恢复、双锁空闲。

源码19997成员，sole719efdff090d6ede85698f7111ebb6358836ca33，Release460189587，源码66成员408522B完成远端恢复链后才构造模型。原224MiB task、272MiB IO、512MiB root与15GiB上限保持；仅以精确closed-increment SHA/size/block/mtime/device/inode清单收紧旧增量上界，没有删除或renew旧baseline。V2142的资源预拒和V2143的单位检查失败均为0模型，原source/记录保留，没有重复资格旧批或重跑失败数值。

PCBF上一轮长段仍为失败：82次求解、81次执行，405normal+200errorstop=605actual/605replay；辅助SLSQP返回status8，successfalse，低残差未被追认为收敛。已完整远端闭账，不原样重跑。

当前正式旧账仍72closed/7whole/48unexecuted。SCCR还缺其余50通道实际采集、完整186维、两级冻结策略/风险融合和整车导航能力；PSF完整路线记录集成与PRIEST几何耦合仍待补。本轮传感PASS不能用作这些方法的全程到达或RP-CCR优势证据。

此报告与晚闭轮复核写于源和runtime封存之后，仅本地晚补，不声称旧Release已经包含，也不第二次封传push同批。
