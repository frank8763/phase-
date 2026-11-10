# V1020完整输入预测准入的恢复搜索通宵实验

状态：TWO_ROUTE_DEVELOPMENT_NOT_PASSED。截止2026-11-11 09:00，不延长；旧失败/窗口保持。

科学：完整实际输入预测不合格时继续原5000扩展/12边/5秒搜索，直到同一原.4米进展/原完整几何和停车门通过；不只检验第一条简化路径。保留新鲜零速许可与恢复停车所有权原子交接；新300秒导航内最多8完整进展段，每段原输入/几何/跟踪/200步停车门不变；非终点仍.4米进展，终点段仅以预测终点距离+.08<=.45及实际终点<=.45替代进展门，提交前预留完整段时间。纯解析预测和转向元数据重建允许1e-12浮点差（1e-9篡改拒绝），实际qpos/qvel/ctrl/mocap全重放仍1e-8，控制与身体请求仍精确。

分账：

```json
{
  "status": "TWO_ROUTE_DEVELOPMENT_NOT_PASSED",
  "stop_reason": null,
  "known_counts": {
    "navigation_models": 2,
    "navigation_native": 23121,
    "own_replay_native": 23121,
    "private_native": 0,
    "preflight_models": 0,
    "reused_original_preflight_models": 2
  },
  "unknown_counts": [],
  "route_branch_rows": [
    {
      "task_id": "main_we",
      "slot": 0,
      "stage": "we_development",
      "route": "we",
      "initial_axis_direction": null,
      "passed": false,
      "executed": true,
      "evidence_passed": true,
      "output": "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/runs/v858_nav2_verified/v1020/main_we",
      "actual_native": 11825,
      "replay_native": 11825,
      "private_native": 0,
      "goal_m": 2.7835477350184505,
      "minimum_clearance_m": 0.2751827833741254,
      "error": null
    },
    {
      "task_id": "repeat_we",
      "slot": 1,
      "stage": "we_development",
      "route": "we",
      "passed": false,
      "executed": false,
      "reason": "MAIN_FUNCTION_FAILED_REPEAT_UNEXECUTED",
      "actual_native": 0,
      "replay_native": 0,
      "private_native": 0
    },
    {
      "task_id": "main_ns",
      "slot": 2,
      "stage": "regression",
      "route": "ns",
      "initial_axis_direction": null,
      "passed": false,
      "executed": true,
      "evidence_passed": true,
      "output": "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/runs/v858_nav2_verified/v1020/main_ns",
      "actual_native": 11296,
      "replay_native": 11296,
      "private_native": 0,
      "goal_m": 2.755575262138231,
      "minimum_clearance_m": 0.40395404428774295,
      "error": null
    },
    {
      "task_id": "repeat_ns",
      "slot": 3,
      "stage": "regression",
      "route": "ns",
      "passed": false,
      "executed": false,
      "reason": "MAIN_FUNCTION_FAILED_REPEAT_UNEXECUTED",
      "actual_native": 0,
      "replay_native": 0,
      "private_native": 0
    }
  ],
  "development16_executed": 0,
  "development16_unexecuted": 16,
  "development16_successes": 0,
  "complete_development16_descriptive_rate": null,
  "original_three_route24_acceptance_passed": false,
  "original_EW_initial_zero_gate_unqualified": true,
  "navigation_budget_s": 300,
  "old_180s_failures_not_upgraded": true,
  "models_during_closure": 0,
  "old_failures_preserved": true,
  "guard_original": true,
  "execution_lock_idle": true
}
```

这是两个合法起点路线的300秒开发及条件新16开发（10120001–16），不是原180秒、原三路线或固定24验收；旧10110001–24仍未执行。完整行驶发现、因果控制、实际停车、续行、目标和完整重放全部门通过才记成功。开发/重复/旧批不混新24；未执行不报0/24。有限单actor课程，非任意地图/遮挡/多actor/实时/递归安全或RAS保证。训练/实机/Stage0。网络离线时保留有界必要原证据，待重新联网进行零模型上传校验。
