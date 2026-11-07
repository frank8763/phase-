# 2026-11-07 Phase存储清理工具

本目录为本次已授权清理的操作源码，选择清单和远端核验结果见 `records/maintenance_20261107/`。原失败结果保持，公共Git历史没有强推重写。

按需恢复：`python3 tools/phase_storage_20261107/restore.py --list`，选择一个组后运行同命令加组名。恢复工具使用Python标准库与zstd，不需要下载全部数据；选定旧内容寻址包按 `unpack_blobs.py` 恢复。临时下载块恢复后自动删除。

plan/package/publish/upload/cleanup脚本是2026-11-07这一次固定选择的操作记录，不能未经新选择清单直接用于新实验。执行删除前要求Phase执行锁空闲、路径/原文件身份匹配，并有远端SHA和完整下载回读证明。trash_only只删除用户明确授权的未选中中间文件，保留必要原件直到上传核验完成。

GitHub CLI来自官方cli/cli发布并校验官方SHA256，使用用户已有keyring登录。CLI二进制是本地工具依赖，由.gitignore排除；新机器应安装官方GitHub CLI后设置自己的Git认证，不应复制凭据。工具和清理不访问Stage，不启动模型或训练。
