# V846小场景64/128世界GPU物理资格实际结果

{
  "status": "NOT_PASSED_GPU_WORLD_IDENTITY_CHECK",
  "worlds_physically_advanced": 64,
  "planned_world_counts": [
    64,
    128
  ],
  "world128_unexecuted": true,
  "counts": {
    "cpu_reference_native": 522,
    "gpu_completed_world_steps": 33280,
    "training_updates": 0,
    "navigation": 0,
    "confirmation": 0
  },
  "elapsed_s": 79.45399674400687,
  "observed_stop": "PARALLEL_WORLD_IDENTITY_OR_ISOLATION_FAILURE",
  "same_input_max_difference": null,
  "different_input_difference": null,
  "measured_steady_throughput": null,
  "training_updates": 0,
  "new_navigation": 0,
  "new24": 0,
  "no_policy_trained": true,
  "shared_environment_changed": false,
  "failure_diagnostic_limit": "The assertion ran before raw per-world states and latency samples were persisted; the two differences are unknown.",
  "no_model_retry": true,
  "source_unchanged": true,
  "raw_deleted": false
}

已使用机器人本体+支持平地（nq20/nv19/nu11，19body/32geom），没有复制原19静态实体场地或actor，无渲染、奖励、训练更新。依赖只runs私有安装，原环境/模型/网络字节不改。正式资格64世界完成33280原生世界步；CPU原生522步。CUDA首次编译日志保留，不能用总79.45秒（含编译）充当稳态吞吐。

停止于相同输入qpos最大差<=1e-6且不同输入差>1e-6的联合断言。日志未在断言前保存两差值和原始状态，故具体哪部分失败、是否浮点/接触数值差异或真正世界隔离问题未知；不能宣称GPU后端物理不正确，也不能宣称一致性通过。该诊断遗漏保留，不通过放宽容差/修补本冻源重新运行追认。128世界未执行，PPO/SAC和通宵训练未开始。

后续应另做明确有界后端诊断：优先保存各世界输入/末状态、接触容量、root/关节差异与稳态时延，再定义合理数值一致性门；同时保留CPU原车模独立评价。并行吞吐能力不能代替单车在线低延迟，也不能替代原完整动态验收。首失败即停止、执行锁空闲、原REVIEW_PENDING保留。初次依赖选取不匹配及下载完成前安装失败准备日志均保留；不隐藏为只有一次成功安装。
