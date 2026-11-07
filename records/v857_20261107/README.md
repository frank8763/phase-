# V857 装配接触资格与论文推进记录

**原批未完成。** 精确两对装配过滤/465个实际模型数组保持/外部接触负例查询通过；原MJB首重放1原生步与V856状态误差0，但tuple/list序列化比对错误停止。修正模型运动0、场地导航0，不能声称速度改善。原失败与零模型补核分别保留，后者不追认原批通过。

- [报告](../../docs/ASSEMBLY_CONTACT_V857_REPORT.md)
- [RAS推进方案](../../docs/RAS_RESEARCH_ROADMAP_20261107.md)
- [英文工作稿](../../docs/paper_ras/MANUSCRIPT_WORKING.md)
- [主张—证据清单](../../docs/paper_ras/CLAIM_EVIDENCE.json)
- [必要原始证据Release](https://github.com/frank8763/phase-/releases/tag/phase-v857-assembly-20261107)

必要原始数据只存Release，`RECORD_INDEX.json`锁定档案和每个解压成员SHA。包括原ERROR/RESULT/窗口、修正MJB/模型差异、碰撞负例、原第1步状态与接触、全冻结输入清单。档案源文件与解压SHA、GitHub服务端digest、下载回读SHA均需核对后才能清本地原始缓存。后续再运行需要新的明确协议，不自动重开。

按需核验或恢复：

```bash
python3 -B experiments/v857_saved_audit/restore.py --verify-only
python3 -B experiments/v857_saved_audit/restore.py
```

复现旧输入需要V856证据组，按其[恢复说明](../nav2_v856_20261107/README.md)另行恢复；不默认下载ROS运行库或全部历史。

`SAVED_INTERFACE_AUDIT.json`仅保存数据/类型接口审核，新增模型与积分0；`STATISTICAL_SCOPE.json`只是设计示例：在固定独立同分布24次零事件条件下，一侧95%事件概率上界仍约11.7%，不是当前未完成实验的风险估计。

## 原窗口内的一次操作例外及最新结果

用户继续明确仿真先行后，另注册一次仅接触序列化比较器接续，原科学源/模型/命令/门不改，继承原17:31:10.700组件截止而不重新900秒，原失败保持。接续原1100原生控制完整重放状态/接触误差0；随后修正模型在Adapter构造的ACTUATOR_LIMITS_REQUIRED被拒，修正模型积分仍0，按规则停止，不作第二接续。原1步与新1100重放共1101，模型加载2/编译2，实际新分支/私有/导航0。物理参数数组相同不足以证明重编译后的命名索引契约正确：差异清单含name_actuatoradr重写和names_map结构变化；这是待独立模型接口审核的疑点，不是已测得执行器动力学失败。当前科学假设仍未验证。独立操作证据审核在records/v857_20261107/interface01/FINAL_INDEPENDENT_AUDIT.json，原始接续证据独立附件保留。

原批与一次操作接续各有独立不可覆盖档案；后者索引INTERFACE_RECORD_INDEX.json，使用`python3 -B experiments/v857_saved_audit/restore.py --interface --verify-only`核验或去掉--verify-only恢复。接续原1100完整重放通过，新修正模型执行器契约未过/积分0；不能追认原批通过。
