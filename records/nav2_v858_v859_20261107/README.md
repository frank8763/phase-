# V858–V860 必要仿真记录

- [公开证据Release](https://github.com/frank8763/phase-/releases/tag/phase-nav2-v858-v860-20261107)。原装配/控制资格通过，Nav2场地开发和候选未通过；新动态/24未启动。
- RECORD_INDEX.json包含两32MiB以内分块SHA与整档SHA；每成员原始SHA在Release INVENTORY。
- 按需恢复：`python3 -B experiments/v858_closure/restore.py v858-v860-evidence`，原V856输入/ROS运行库另按该Release索引恢复，不默认下载历史。
- FINAL_INDEPENDENT_AUDIT.json是失败记录一致性终审，不是动态验收PASS。
- 原入口失败、唯一目录接续、V859负结果及V860零控制生命周期异常分别保留。合计14975新实际/14975新完整重放/1100旧重放/私有0，新增动态/训练/实机0。
- 必要来源/逐解压SHA和远端下载SHA核验后清理本地原始缓存，保留这些摘要和源码。
