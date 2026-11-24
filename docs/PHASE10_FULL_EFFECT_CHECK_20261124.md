# phase10 full 效果与关闭检查

本次只读原结果和保存数组并绘图，未重跑模型、物理、重放、优化器或数值审核。

实际记录到达原目标，最终距离0.055524709799089564m；50754 actual / 50754 replay，最大qpos/qvel/ctrl/mocap误差0、接触不匹配0；坏接触0、实际最低净空0.2539839999344672m、自体最低余量0.009291440147786989m。末平移速度8.238971845367436e-6m/s；发现后实际行驶5.582242749475054m。独立BASE前缀安全审核通过，控制和记忆重算误差各2.220446049250313e-16。

完整合格成功仍为false。首错SAVE_NPLUS1 / BYTE_GRANT_EXHAUSTED；FULL_STATE_NPLUS1.npz未生成，因此分派prefix_safety_only，完整独立到达审核未执行。V1797审核目录修复只获得此前软件验证，本轮未走到fullgoal审核，不能称已通过真实完整审核。记录到达和前缀安全不能代整体PASS。

随后归档器错误引用不存在的runs/v1620_mechanism_boundary/UNATTENDED_CONTINUATION_AUTHORIZATION_20261124.json；原真实授权是20261123文件。此为新归档helper日期字符串替换错误，原ARCHIVE_CLAIM和错误保持，不制造授权文件或重跑旧finalizer。当前本轮FULL_REMOTE_VERIFIED和canonicalPOST_ROUND_STORAGE_BARRIER均缺失，所有本地原始证据留存，未核删除0。

full与no_time同相位保存的所有NATIVE_TRACE数组成员逐dtype/shape/字节完全一致，APPLIED_JOURNAL整体SHA也一致。图显示两实际路径重合。本对未观察到时间选择带来实际轨迹/到达改善；两项均有完整证据审核缺口，因此不作为合格机制对照、不主张统计结论。

正式20表目前16closed：6完整合格成功、10non-success（含技术与科学失败），4未执行。本检查没有启动后继。全部相关owned进程退出，REVIEW原SHA恢复，两执行锁idle。旧source/任务/参数/安全门/失败分母保持。

模型owner实际墙钟202.218867s，含失败归档后台210.868769s。

模型关闭时间：2026-11-24T09:26:10.000330+08:00。

保存数组图：runs/v1800_phase10_saved_review/phase10_saved_paths.png；精确成员比较：SAVED_PAIR_COMPARISON.json。此晚生成材料尚未远端保存，不外推已封sourcearchive包含。
