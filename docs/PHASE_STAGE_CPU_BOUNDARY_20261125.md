# 双方CPU资源边界

用户明确要求避免冲突并让双方合理安排。只协调CPU，不交换研究内容，不读取或修改Stage源、模型、结果或进程。

| 用途 | CPU逻辑编号 |
|---|---|
| Phase最大允许边界 | 0–7、16–23 |
| Stage保留边界 | 8–15、24–31 |
| Phase实际RPP车辆/重放 | 2 |
| Phase纯几何 | 4 |
| Phase后台管理/归档 | 5 |
| Phase独立算法资格 | MPPI 6、SVG-MPPI 7 |

Stage的8、10、12分别与24、26、28是超线程兄弟核，现连同整个8–15/24–31保留区一起避让。Phase本方硬件拓扑及身份绑定进程树审计：11进程、28线程，无Stage保留区重叠；旧后台inhibitor PID1261621原宽affinity已固定CPU5，算法代码/参数/旧deadline不变。Stage侧也只读资源确认重叠0。后续Phase launcher和辅助shell入口先taskset，再启动受限子进程，避免父wrapper短暂宽affinity触发对方守卫。

资源核验记录：runs/v1999_phase_cpu_allocation/RESULT.json 与 AGREED_BOUNDARY.json。该CPU分工不是多方法车辆安全资格；未过验收的方法不能据此冒作正式对照。无Stage研究访问、无新代理/聊天心跳或训练实机。
