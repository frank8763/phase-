# V864 静态NS回归失败及软件诊断

原WE成功保持；新NS3845原生+3845自身控制完整重放误差0、最低净空.227m，RPP预测碰撞拒绝，剩2.281m，后4任务未执行。动态/新24/实机0。V865仅配置准备未通过真实软件或物理资格，旧截止未延长。

[必要原始证据Release](https://github.com/frank8763/phase-/releases/tag/phase-nav2-v864-20261107)。恢复：`python3 -B experiments/v864_closure/restore.py v864-static-diagnosis-evidence`；RECORD_INDEX含分块SHA，Release INVENTORY含逐来源SHA。ROS基础库和官方RPP插件分别复用V856/V863 Release。

报告docs/NAV2_RPP_STATIC_V864_REPORT.md。原始错误/未执行/归档与清理回执全部保留。
