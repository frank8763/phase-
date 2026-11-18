# V1281 动态固定24验收备份 · 2026-11-18

V1281 在2026-11-17 22:26至11月18日00:18完成：24个真实t0、24/24主任务（三路线各8/8、方向各12/12）、固定1/9/17三次完整重复全部通过。27次导航独审通过，完整成对状态/控制误差0，1089992实际原生步和相同数量自身重放，最低实际净空0.2558472575m，坏接触0。

这是已经暴露的固定课程验收，不是未见泛化、实时、实机或全面优势证明。原所有失败保持；V1286后软件接力误拒/dev/null，未完成多核测量、消融或正式多算法比较。

源码、报告和本目录索引由Git保存；完整原始数据在同仓库[Release](https://github.com/frank8763/phase-/releases/tag/phase-dynamic-fixed24-v1281-20261118)。`RECORD_INDEX.json`记录分组、32MiB传输块及SHA；`SOURCE_INVENTORY.json`记录每个解压文件的长度和SHA。成功27条导航按任务分组，可只恢复需要的一条。`INTERNAL_SYMLINKS.json`记录Git保留的仓库内部链接，目标文件内容另有备份；不读取外部仓库。

包括完整成功批、所需冻结依赖、18/19和24开发主重复、原V1275槽24失败见证、必要操作错误及晨检。没有重新打包所有无关旧候选池，也不宣称这些选定证据包含每次历史试验的所有中间候选。

按需恢复（在仓库根目录执行，执行锁须空闲、REVIEW_PENDING须存在）：

```bash
python3 experiments/v1287_github_backup_20261118/restore.py --list
python3 experiments/v1287_github_backup_20261118/restore.py --group v1281-main_slot24 --prefix runs/v858_nav2_verified/v1281/main_slot24/
python3 experiments/v1287_github_backup_20261118/restore.py --group frozen-dependencies-and-provenance
```

仅下载校验、不恢复可加`--verify-only`。恢复全部已选运行数据用`--all`；不会重新运行模型，也不会覆盖已有但SHA不同的文件。源码与元数据从Git取得，恢复器只写选定的runs路径。

上传结果以Release中的`FULL_REMOTE_VERIFIED.json`为准：必须Git远端提交核对、所有资产下载SHA及解压逐成员SHA通过，才允许按清单清除本地闭合缓存。任何未验证原件均保留。
