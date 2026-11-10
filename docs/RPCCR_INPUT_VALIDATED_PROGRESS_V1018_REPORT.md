# V1018完整输入预测准入的恢复搜索通宵实验

状态：NOT_PASSED。截止2026-11-11 09:00，不延长；旧失败/窗口保持。

科学：完整实际输入预测不合格时继续原5000扩展/12边/5秒搜索，直到同一原.4米进展/原完整几何和停车门通过；不只检验第一条简化路径。保留新鲜零速许可与恢复停车所有权原子交接；原180秒导航内最多8完整进展段，每段原输入/几何/跟踪/.4米进展/200步停车门不变，提交前预留完整段时间。纯解析预测和转向元数据重建允许1e-12浮点差（1e-9篡改拒绝），实际qpos/qvel/ctrl/mocap全重放仍1e-8，控制与身体请求仍精确。

分账：

```json
{
  "status": "NOT_PASSED",
  "stop_reason": {
    "error": "AssertionError('STOP_ALL_SAFETY_OR_EVIDENCE')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1018_input_progress_night/campaign.py\", line 70, in main\n    if action.startswith('STOP_'):raise AssertionError(action)\nAssertionError: STOP_ALL_SAFETY_OR_EVIDENCE\n"
  },
  "known_counts": {
    "navigation_models": 3,
    "navigation_native": 26730,
    "own_replay_native": 26730,
    "private_native": 0,
    "preflight_models": 0,
    "reused_original_preflight_models": 3
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
      "output": "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/runs/v858_nav2_verified/v1018/main_we",
      "actual_native": 12362,
      "replay_native": 12362,
      "private_native": 0,
      "goal_m": 2.269688667479738,
      "minimum_clearance_m": 0.27481106915655573,
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
      "output": "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/runs/v858_nav2_verified/v1018/main_ns",
      "actual_native": 14161,
      "replay_native": 14161,
      "private_native": 0,
      "goal_m": 2.371366376330775,
      "minimum_clearance_m": 0.32967681356106504,
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
    },
    {
      "task_id": "main_ew",
      "slot": 4,
      "stage": "regression",
      "route": "ew",
      "initial_axis_direction": null,
      "passed": false,
      "executed": true,
      "evidence_passed": false,
      "output": "/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/runs/v858_nav2_verified/v1018/main_ew",
      "actual_native": 207,
      "replay_native": 207,
      "private_native": 0,
      "goal_m": 8.000063789864182,
      "minimum_clearance_m": null,
      "error": "AssertionError()"
    }
  ],
  "confirmation_executed": 0,
  "confirmation_unexecuted": 24,
  "confirmation_successes": 0,
  "full24_rate": null,
  "models_during_closure": 0,
  "old_failures_preserved": true,
  "guard_original": true,
  "execution_lock_idle": true
}
```

完整行驶发现、因果控制、实际停车、续行、目标和完整重放全部门通过才记成功。开发/重复/旧批不混新24；未执行不报0/24。有限单actor课程，非任意地图/遮挡/多actor/实时/递归安全或RAS保证。训练/实机/Stage0。网络离线时保留有界必要原证据，待重新联网进行零模型上传校验。
