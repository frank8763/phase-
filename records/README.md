# Phase必要实验记录

源码、报告、汇总和任务/审核结论保存在本仓库。大体积必要原始证据保存在[同仓库Release](https://github.com/frank8763/phase-/releases/tag/phase-essential-records-20261107)，以其 `RECORD_INDEX.json` 和SHA256为准。上传未完成前索引状态保持待核验。

本地保留运行依赖和小摘要，原始数据按需恢复；不默认下载全历史。恢复前运行 `python3 tools/phase_storage_20261107/restore.py --list` 查看各组大小，再指定一个组恢复。下载临时分块在恢复完成后自动删除。

`verified_three_route_v827`保存选定旧内容寻址记录。恢复该组后，以其 `V827_SELECTED_BLOB_INVENTORY.json.gz` 调用 `unpack_blobs.py`，按原SHA还原实际轨迹。历史预测/信念缓存明确裁剪，不再声称档案包含全部旧候选池。最新V855保留完整实际运行、已执行控制合同、独立审核结果和末失败见证，早期未选候选池裁剪，原未通过结果保持。

`fixtures/v854_b64_motion_estimate_selected.jsonl`仅四个原始保存状态，供零模型公式资格复算；不是完整历史跟踪日志。需要复算原资格时将这四行作为所选夹具输入，不能声称重新建立全历史因果覆盖。

存储和清理约定见[存储规则](../docs/STORAGE_POLICY.md)。
