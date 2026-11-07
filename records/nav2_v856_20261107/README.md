# Nav2 V856 必要记录

本轮真实ROS2 Jazzy/Nav2软件接口通过，本车执行器速度资格失败；没有执行场地静态/动态导航，也没有新24确认。原一次输出目录入口失败和一次仅输出域接续完整保留。详见[报告](../../docs/NAV2_FOUNDATION_V856_REPORT.md)、[独立保存审核](FINAL_INDEPENDENT_AUDIT.json)及[原生诊断](DIAGNOSIS.json)。

源码、固定任务/资格阈值、冻结SHA、报告和小摘要保存在Git；原生证据和精选运行依赖存[同仓Release](https://github.com/frank8763/phase-/releases/tag/phase-nav2-v856-20261107)。Git中的`RECORD_INDEX.json`与Release中的`FINAL_RECORD_INDEX.json`列出每个分块及完整压缩档SHA，远端上传及流式下载回读证明见`ASSET_REMOTE_VERIFICATION.json`。不是仅保存一份“通过”的汇总，原失败日志、实际状态控制接触及完整重放结论都在证据组中。

按需恢复，避免占用磁盘：

```bash
python3 -B experiments/v856_nav2_closure/restore_records.py --list
python3 -B experiments/v856_nav2_closure/restore_records.py v856-evidence
# 需要运行ROS软件接口时才恢复此组：
python3 -B experiments/v856_nav2_closure/restore_records.py v856-ros-runtime
# 再分发运行依赖时一并恢复许可文本：
python3 -B experiments/v856_nav2_closure/restore_records.py v856-third-party-licenses
```

- `v856-evidence`：约8.8MB压缩/22.1MB解压，199个文件；物理MJB、初态、1100真实原生/1100完整控制重放结果、全部自接触、软件失败与成功轨迹、依赖来源签名、原始操作账本和保存审核。
- `v856-ros-runtime`：约43.7MB压缩/179.8MB解压，6100个文件；已SHA核验包提取的ROS动态运行库/Python消息/插件与必要传递依赖。另有约0.6MB压缩的第三方许可文本组，按SHA去重保留486项原许可来源。运行组不包含开发头文件、静态库、编译工具或APT缓存，不承诺跨系统便携。需要兼容Ubuntu24.04 amd64、系统Python3.12及`RUNTIME_SELECTED.json`列出的系统库。授权文件随上游share目录保留。

恢复脚本逐分块和解压成员SHA核验，拒绝越界路径，已有文件字节不同即停，不覆盖。恢复证据不会运行模型；**原campaign已闭批，不要把恢复档案当成再次启动的授权**。后续修正模型与新物理任务须新协议，并保留本轮失败。

当前SOURCE_FREEZE锁定的是本轮原始输入字节。删除可重建缓存/开发包属于用户已授权存储清理，不代表同一物理任务可无准备地再次运行。结果不声称旧RP-CCR鲁棒证书或全面实机实时性。
