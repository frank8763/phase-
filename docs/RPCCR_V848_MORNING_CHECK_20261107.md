# V848 通宵实验晨检

整体三路线未通过。南北主回合665公开步到达（末距.441281m，29.22min）及完整重复（25.27min）通过，所有原生状态ctrl/mocap误差0；东西主回合1200步HORIZON（32.69min），末距1.748784m，最近1.224323m，反向主及后续重复未执行。11月7日00:09:29按首功能失败停止，非断网或墙钟超时。

东西12次规划全部有GLOBAL_GOAL_PATH；末300保存公开步位置累计3.899132m，净目标进展.000175m，存在反复进退。当前证据定位到局部控制/后备续接的进展循环，不能仍仅归因为全局无路；具体触发规则待诊断，不认为加时必然解决。

三实际回合全部安全/因果/覆盖/完整重放审核通过，最低原生净空.218542m、障碍穿透未知0，原生重放误差0。证据归档完成，262493来源/20.654GB原始字节，7大blob/41无损块本次重新核验；3840冻结输入未变，REVIEW_PENDING原字节和执行锁空闲、监督及campaign已退出。晨检模型初始化/积分/导航0，不重开旧窗口。

{
  "overall_passed": false,
  "planned_routes": 3,
  "main_attempts": 2,
  "main_successes": 1,
  "complete_repeats_passed": 1,
  "unexecuted_main_routes": [
    "EAST_WEST"
  ],
  "unexecuted_navigation": 3,
  "west_east": {
    "outcome": "HORIZON",
    "wall_s": 1961.2270453239908,
    "public_steps": 1200,
    "simulated_seconds": 96.0,
    "final_goal_m": 1.748783501546025,
    "closest_goal_m": 1.2243228684503948,
    "closest_public_step": 1097,
    "last300_sampled_travel_m": 3.8991320545666714,
    "last300_net_goal_progress_m": 0.00017507709238784308,
    "planning_attempts": 12,
    "all_plans_complete_goal": true
  },
  "checks": {
    "review_guard_exact": true,
    "frozen_inputs": 3840,
    "frozen_inputs_changed": 0,
    "large_blobs_reassembled": 7,
    "transport_chunks_verified": 41,
    "models_started_this_check": 0,
    "integrations_this_check": 0,
    "supervisor_exited": true,
    "campaign_exited": true,
    "execution_lock_idle": true
  },
  "interpretation": "West-east has complete goal references but repeatedly advances and retreats; the last300 recorded public positions travel about3.90m with only0.000175m net target progress. This is evidence of a control/recovery progress cycle, not a wall timeout, network interruption or missing complete global reference. Which admission/recovery rule causes the cycle still requires focused diagnosis; no new model tests performed.",
  "counts": {
    "navigation_native": 20240,
    "private_native": 31111088,
    "replay_native": 20240
  }
}
