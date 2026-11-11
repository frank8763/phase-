# V1032 固定0.08m/s响应资格

NOT_PASSED。直行500实际+500完整重放通过；左转第343步位置误差0.01002193491549543m超过事前0.01m，立即停止，右转未执行。共2模型/843实际/843自身重放/私有MuJoCo0；训练实机0。位置门严于原导航.04m，但不能事后改门升级本次资格，未完成剩余157停车步，不能推断其结果。

左转第300步误差.006504m，第343步.010022m；纵向误差约-.009563m、横向-.002998m，实际速度-.004359m/s而预测+.001074m/s，主要在完整停车过程中累积。原低阶模型由.03m/s辨识，此为新速度留出检查，不用本次留出数据回填参数再追认通过。每已执行原生安全/合法ctrl/自体/静态体/rootguard/全部状态和接触重放通过，左转最低.406080m、坏接触0/重放误差0；证据前缀通过不等于完整响应或动态到达。

准备阶段同名audit错误导入产生KeyError，0模型原记录保留；冻源前改绝对自身模块绑定并通过10入口与15负例检查。实际退出时EGL析构警告保留在console，发生在结果保存后，不据此改写实际状态或门。所有物理窗口已封，REVIEW_PENDING原字节恢复/锁空闲；不启动右转或整路。原V1025/24未过，新较容易V1030主+重复通过另列。

```json
{
  "passed": false,
  "closed": true,
  "counts": {
    "model_initializations": 2,
    "navigation_native": 843,
    "own_replay_native": 843,
    "private_mujoco_native": 0
  },
  "unknown_counts": [],
  "rows": [
    {
      "task_id": "straight",
      "passed": true,
      "executed_native": 500,
      "error": null,
      "prefix_audit": {
        "passed": true,
        "scope": "executed prefix evidence only; not full response qualification",
        "checks": {
          "all_executed_native_accounted": true,
          "entire_executed_prefix_replayed": true,
          "full_actual_clearance": true,
          "full_self": true,
          "zero_bad_contact": true,
          "legal_ctrl": true,
          "legal_slew": true,
          "compiled_model_sha": true
        },
        "executed_native": 500,
        "position_error_max": 0.0023694909531143614,
        "heading_error_max": 0.00011609275580526379,
        "full_500_executed": true,
        "all_200_stop_executed": true,
        "component_passed": true,
        "models": 0,
        "integrations": 0
      },
      "response": {
        "passed": true,
        "native_steps": 500,
        "maximum_position_m": 0.002369490953114361,
        "maximum_heading_rad": 0.00011609275580526379,
        "maximum_virtual_steering_rad": 1.5131557739965257e-05,
        "actual_displacement_m": 0.2201879480277783,
        "complete_200_native_stop": true
      },
      "minimum_clearance_m": 0.4250568438792064
    },
    {
      "task_id": "left",
      "passed": false,
      "executed_native": 343,
      "error": "AssertionError('HELDOUT_NATIVE_RESPONSE_ERROR')",
      "prefix_audit": {
        "passed": true,
        "scope": "executed prefix evidence only; not full response qualification",
        "checks": {
          "all_executed_native_accounted": true,
          "entire_executed_prefix_replayed": true,
          "full_actual_clearance": true,
          "full_self": true,
          "zero_bad_contact": true,
          "legal_ctrl": true,
          "legal_slew": true,
          "compiled_model_sha": true
        },
        "executed_native": 343,
        "position_error_max": 0.010021934915495431,
        "heading_error_max": 0.006217983325123021,
        "full_500_executed": false,
        "all_200_stop_executed": false,
        "component_passed": false,
        "models": 0,
        "integrations": 0
      },
      "response": null,
      "minimum_clearance_m": 0.4060795564571018
    }
  ],
  "unexecuted": [
    "right"
  ],
  "models_authorized": false,
  "guard_original": true,
  "execution_lock_idle": true,
  "original_dynamic_acceptance": false,
  "new24_executed": 0,
  "training_updates": 0,
  "hardware_steps": 0,
  "stop_reason": "left response position error 0.01002193491549543 > preregistered 0.01m at native343; right unexecuted; old thresholds and failure preserved"
}
```
