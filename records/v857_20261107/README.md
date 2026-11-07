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
