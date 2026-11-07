# V862失败与V863单静态通过

V862 MPPI原180秒静态失败保留。官方RPP同模型和硬门在原WE到达：45.69秒仿真、目标误差.241m、最低净空.272m、4569实际+4569完整重放误差0。没有动态/三路线/重复/新24通过。

[必要证据Release](https://github.com/frank8763/phase-/releases/tag/phase-nav2-v862-v863-20261107)。RECORD_INDEX含分块SHA，Release INVENTORY含全部成员SHA。按需恢复：`python3 -B experiments/v863_closure/restore.py v862-v863-evidence`。ROS基础运行库复用V856 Release的v856-ros-runtime，新增RPP插件及签名来源在本档。

报告docs/NAV2_RPP_STATIC_V863_REPORT.md；当前一次物理授权已封账，无自动后续导航。
