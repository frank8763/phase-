# V841结束检查与直接原因

结论：完整动态单场景未通过；资格组件通过不能替代导航。

{
  "status": "CLOSED_REVIEW_VERIFIED_NOT_PASSED",
  "checked_at": "2026-11-06T11:30:38.966456+08:00",
  "stopped_at": "2026-11-06T11:15:44.870255+08:00",
  "direct_stop": "single_navigation_original1200s_soft_wall_cap; global5400s_is_total_window_not_one_navigation_cap",
  "global_elapsed_s": 1934.9819474220276,
  "single_navigation_elapsed_s": 1199.1891546820116,
  "outcome": "BOUNDED_WALL_STOP",
  "main_attempts": 1,
  "complete_chain_successes": 0,
  "conditional_repeats_executed": 0,
  "new24_executed": 0,
  "public_steps": 389,
  "navigation_native": 3112,
  "private_native": 4463680,
  "replay_native": 3112,
  "post_stop_displacement_m": 0.9687805721385718,
  "goal_distance_m": 3.1534572837609054,
  "end_speed_m_s": 0.13186430742281555,
  "end_is_not_actual_stationary_stop": true,
  "physical_audits_passed": 17,
  "minimum_actual_clearance_m": 0.305892278021587,
  "obstacle_or_unknown_contacts": 0,
  "full_native_replay_error": 0.0,
  "first_trigger": 295,
  "pre_trigger_native_exact": 2360,
  "joint_public_cycles": 94,
  "joint_probes": 284,
  "joint_complete_tails": 6981,
  "joint_admitted_every_cycle": true,
  "selected_reference_tails": 0,
  "old_same389_goal_distance_m": 3.1226894182063334,
  "old_same389_private_native": 2202472,
  "same_index_comparison_is_descriptive_different_post295_states": true,
  "archives": [
    {
      "archive": "evidence/rpccr_early_joint_v841_qualification_20261106",
      "sources": 18229,
      "raw_bytes": 2359991659,
      "all_source_and_decompressed_sha_verified": true,
      "large_blobs": 5,
      "chunks_reassembled_sha_verified": true
    },
    {
      "archive": "evidence/rpccr_early_joint_v841_20261106",
      "sources": 34984,
      "raw_bytes": 3920735448,
      "all_source_and_decompressed_sha_verified": true,
      "large_blobs": 6,
      "chunks_reassembled_sha_verified": true
    }
  ],
  "operation_snapshot_entries_verified": 100,
  "frozen_source_files_verified": 18088,
  "review_original_bytes_restored": true,
  "execution_lock_idle": true,
  "new_models": 0,
  "new_integrations": 0,
  "network_calls": 0,
  "raw_deleted": false,
  "not_proven_would_arrive_with_more_time": true
}

单次导航仍采用原1200秒软上限；用户选定90分钟是资格、主、条件重复和各模型审核合计根窗口。达到单次上限即按预注册停止，不能用剩余时间延长原任务。389公开=31.12秒仿真，末仍有合法MODEL_SAFE_COMMAND、前向完整证书，末速约.132m/s；并非原库全拒、碰撞或已物理停稳。发现后位移.9688m不足1m、目标3.1535m未达.45m。

第295步后94周期均联合找到完整合格尾，284首命令/6981完整尾；94次实际选择全部原FORWARD_BRAKE，沿参考新尾没有获选。同389公开旧私有2202472、新4463680，约2.03倍；两轨迹在295之后不同，只作固定步数描述，不当等价加速或统计优势。额外搜索每步开销增加而当前没有完整导航收益证据；不能据预算终止声称物理无解，也不能声称延长就能到达。

下一步仅设计：先剖分并压低完整尾联合计算、检查当前选择目标为何持续偏向原前向尾；任何决策等价优化必须保存同输入/同选择/完整向量证据，若改变触发频率或评分则属于新候选，需另行冻结有界验证。当前轮不追加模型、不延长、不新池或训练，旧失败和所有冻结归档保持。
