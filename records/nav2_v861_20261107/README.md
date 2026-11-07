# V861 前置资格记录

真实Nav2启动原3/3、新逐服务就绪3/3与一个真实无响应服务负例；固定16秒原Adapter曲线1600实际+1600完整重放全部组件门通过。没有Nav2整条路径导航/动态或新24验收。

[必要证据Release](https://github.com/frank8763/phase-/releases/tag/phase-nav2-v861-20261107)；RECORD_INDEX.json逐分块SHA，Release INVENTORY逐原始成员SHA。按需恢复：`python3 -B experiments/v861_closure/restore.py v861-evidence`。真实ROS运行库单独使用V856 Release的v856-ros-runtime，避免重复下载SDK。

报告docs/NAV2_STARTUP_CURVE_V861_REPORT.md。旧偶发启动未稳定复现，不能声称唯一根因已经解决；原V858/V859/V860失败保持。
